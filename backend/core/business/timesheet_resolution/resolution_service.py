"""
Module: backend.core.business.timesheet_resolution.resolution_service
====================================================================

Orchestration de la résolution d'une référence de feuille de temps.

Ce service relie les composants déterministes déjà présents :

1. lecture de la référence extraite dans BusinessRequest ;
2. utilisation directe d'un numéro de feuille lorsqu'il est fourni ;
3. résolution de la période calendaire ;
4. recherche des feuilles qui chevauchent cette période ;
5. production d'une décision métier destinée au workflow.

Ce module ne crée, ne modifie et ne supprime aucune feuille de temps.
Il n'appelle aucun LLM et n'exécute aucune action d'écriture.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Callable

from pydantic import BaseModel, Field

from backend.core.business.business_request import BusinessRequest
from backend.core.business.timesheet_resolution.models import (
    ResolvedTimesheetPeriod,
    TimesheetLookupResult,
    TimesheetSummary,
)
from backend.core.business.timesheet_resolution.period_resolver import (
    TimesheetPeriodResolutionError,
    resolve_timesheet_period,
)
from backend.core.business.timesheet_resolution.timesheet_finder import (
    TimesheetFinderError,
    find_timesheets_for_period,
)
from backend.tools.hub_functions import hub_list_timesheets


ListTimesheetsCallable = Callable[..., str]


class TimesheetResolutionStatus(StrEnum):
    """Décisions possibles après résolution d'une référence de feuille."""

    USE_PROVIDED_TIMESHEET = "USE_PROVIDED_TIMESHEET"
    USE_EXISTING_TIMESHEET = "USE_EXISTING_TIMESHEET"
    CREATE_NEW_TIMESHEET = "CREATE_NEW_TIMESHEET"
    ASK_USER_TO_CHOOSE = "ASK_USER_TO_CHOOSE"
    RETRY_LATER = "RETRY_LATER"
    REQUIRES_CLARIFICATION = "REQUIRES_CLARIFICATION"
    INVALID_REQUEST = "INVALID_REQUEST"


class TimesheetResolutionDecision(BaseModel):
    """
    Résultat de l'orchestration de résolution d'une feuille de temps.

    Ce contrat contient toutes les informations nécessaires au workflow
    pour poursuivre, demander une précision ou interrompre proprement
    le traitement.
    """

    status: TimesheetResolutionStatus = Field(
        description="Décision déterministe produite par le service.",
    )

    selected_timesheet_number: str | None = Field(
        default=None,
        description=(
            "Numéro de la feuille sélectionnée directement ou trouvée automatiquement."
        ),
    )

    selected_timesheet: TimesheetSummary | None = Field(
        default=None,
        description="Feuille normalisée lorsqu'une correspondance unique existe.",
    )

    candidate_timesheets: list[TimesheetSummary] = Field(
        default_factory=list,
        description="Feuilles candidates lorsque plusieurs résultats existent.",
    )

    resolved_period: ResolvedTimesheetPeriod | None = Field(
        default=None,
        description="Période calendaire calculée avant la recherche.",
    )

    lookup_result: TimesheetLookupResult | None = Field(
        default=None,
        description="Résultat complet retourné par le Timesheet Finder.",
    )

    requires_user_input: bool = Field(
        default=False,
        description="Indique qu'une réponse de l'utilisateur est nécessaire.",
    )

    can_continue: bool = Field(
        default=False,
        description=(
            "Indique que le workflow peut poursuivre vers la résolution "
            "des projets, tâches et catégories."
        ),
    )

    message: str = Field(
        default="",
        description="Message fonctionnel exploitable par la couche conversationnelle.",
    )

    hub_error: str | None = Field(
        default=None,
        description="Erreur contrôlée retournée par Integration Hub.",
    )


def resolve_timesheet_reference(
    *,
    business_request: BusinessRequest,
    resource_id: str,
    auth_header: str,
    reference_date: date | None = None,
    list_timesheets_fn: ListTimesheetsCallable = hub_list_timesheets,
) -> TimesheetResolutionDecision:
    """
    Résout la feuille de temps correspondant à une demande métier.

    Ordre de traitement :

    1. utiliser directement le numéro explicite lorsqu'il existe ;
    2. vérifier les prérequis nécessaires à la recherche ;
    3. résoudre la période demandée ;
    4. interrompre le traitement si la période doit être clarifiée ;
    5. rechercher les feuilles qui chevauchent la période ;
    6. produire une décision selon le nombre de résultats.

    Aucun objet reçu en entrée n'est modifié.
    """

    provided_number = _normalize_timesheet_number(
        business_request.timesheet.number
    )

    # Un numéro explicite est prioritaire sur toute référence temporelle.
    # Aucune recherche Hub n'est nécessaire dans ce cas.
    if provided_number:
        return TimesheetResolutionDecision(
            status=TimesheetResolutionStatus.USE_PROVIDED_TIMESHEET,
            selected_timesheet_number=provided_number,
            requires_user_input=False,
            can_continue=True,
            message=(
                f"La feuille de temps {provided_number} a été fournie "
                "explicitement et peut être utilisée."
            ),
        )

    validation_error = _validate_search_context(
        business_request=business_request,
        resource_id=resource_id,
        auth_header=auth_header,
    )

    if validation_error is not None:
        return _invalid_request(validation_error)

    resolved_period = _resolve_requested_period(
        business_request=business_request,
        reference_date=reference_date,
    )

    if isinstance(resolved_period, TimesheetResolutionDecision):
        return resolved_period

    if resolved_period.requires_clarification:
        return TimesheetResolutionDecision(
            status=TimesheetResolutionStatus.REQUIRES_CLARIFICATION,
            resolved_period=resolved_period,
            requires_user_input=True,
            can_continue=False,
            message=(
                resolved_period.clarification_question
                or (
                    "La période demandée doit être précisée avant de "
                    "rechercher une feuille de temps."
                )
            ),
        )

    lookup_result = _search_timesheets(
        period=resolved_period,
        resource_id=resource_id,
        auth_header=auth_header,
        list_timesheets_fn=list_timesheets_fn,
    )

    if isinstance(lookup_result, TimesheetResolutionDecision):
        return lookup_result

    return _build_lookup_decision(
        resolved_period=resolved_period,
        lookup_result=lookup_result,
    )


def _normalize_timesheet_number(value: str | None) -> str | None:
    """Nettoie un numéro explicite sans inventer ni transformer son format."""

    if value is None:
        return None

    normalized = value.strip()

    return normalized or None


def _validate_search_context(
    *,
    business_request: BusinessRequest,
    resource_id: str,
    auth_header: str,
) -> str | None:
    """Valide les informations minimales nécessaires à une recherche Hub."""

    if not resource_id or not resource_id.strip():
        return (
            "L'identifiant de ressource est obligatoire pour rechercher "
            "les feuilles de temps."
        )

    if not auth_header or not auth_header.strip():
        return (
            "Le jeton d'authentification est obligatoire pour rechercher "
            "les feuilles de temps."
        )

    period_mode = business_request.timesheet.period_mode

    if not period_mode or period_mode == "unknown":
        return (
            "La période de la feuille de temps n'a pas pu être déterminée."
        )

    if period_mode == "timesheet_number":
        return (
            "Le mode timesheet_number nécessite un numéro de feuille "
            "de temps explicite."
        )

    return None


def _resolve_requested_period(
    *,
    business_request: BusinessRequest,
    reference_date: date | None,
) -> ResolvedTimesheetPeriod | TimesheetResolutionDecision:
    """
    Transforme la référence temporelle structurée en période absolue.

    Les erreurs métier du Period Resolver sont converties en décision
    contrôlée afin de ne pas laisser remonter une exception au workflow.
    """

    timesheet_reference = business_request.timesheet

    try:
        return resolve_timesheet_period(
            period_mode=timesheet_reference.period_mode,
            explicit_date=timesheet_reference.explicit_date,
            explicit_start_date=timesheet_reference.explicit_start_date,
            explicit_end_date=timesheet_reference.explicit_end_date,
            reference_date=reference_date,
        )
    except TimesheetPeriodResolutionError as exc:
        return _invalid_request(str(exc))
    except (TypeError, ValueError) as exc:
        # Protection supplémentaire contre une valeur structurée invalide.
        return _invalid_request(
            f"La période demandée est invalide : {exc}"
        )


def _search_timesheets(
    *,
    period: ResolvedTimesheetPeriod,
    resource_id: str,
    auth_header: str,
    list_timesheets_fn: ListTimesheetsCallable,
) -> TimesheetLookupResult | TimesheetResolutionDecision:
    """
    Exécute la recherche via le finder et convertit ses erreurs techniques.

    Une réponse Hub avec ok=False est transportée dans TimesheetLookupResult.
    Une réponse non JSON ou structurellement invalide déclenche en revanche
    TimesheetFinderError et devient une décision RETRY_LATER.
    """

    try:
        lookup_result = find_timesheets_for_period(
            period=period,
            resource_id=resource_id,
            auth_header=auth_header,
            list_timesheets_fn=list_timesheets_fn,
        )
    except TimesheetFinderError as exc:
        return TimesheetResolutionDecision(
            status=TimesheetResolutionStatus.RETRY_LATER,
            resolved_period=period,
            requires_user_input=False,
            can_continue=False,
            message=(
                "La recherche des feuilles de temps n'a pas pu être "
                "effectuée. Veuillez réessayer ultérieurement."
            ),
            hub_error=str(exc),
        )
    except Exception as exc:
        # Les exceptions techniques imprévues du connecteur sont contrôlées.
        # Aucune décision de création ne doit être prise dans ce cas.
        return TimesheetResolutionDecision(
            status=TimesheetResolutionStatus.RETRY_LATER,
            resolved_period=period,
            requires_user_input=False,
            can_continue=False,
            message=(
                "Le service de recherche des feuilles de temps est "
                "temporairement indisponible."
            ),
            hub_error=str(exc),
        )

    if lookup_result.hub_error:
        return TimesheetResolutionDecision(
            status=TimesheetResolutionStatus.RETRY_LATER,
            resolved_period=period,
            lookup_result=lookup_result,
            requires_user_input=False,
            can_continue=False,
            message=(
                "Integration Hub n'a pas pu rechercher les feuilles de "
                "temps. Veuillez réessayer ultérieurement."
            ),
            hub_error=lookup_result.hub_error,
        )

    return lookup_result


def _build_lookup_decision(
    *,
    resolved_period: ResolvedTimesheetPeriod,
    lookup_result: TimesheetLookupResult,
) -> TimesheetResolutionDecision:
    """Produit la décision finale à partir du nombre de feuilles trouvées."""

    if lookup_result.count == 1:
        selected_timesheet = lookup_result.selected_timesheet

        # Cette protection ne devrait jamais être nécessaire lorsque count == 1,
        # mais elle garantit un contrat de sortie cohérent.
        if selected_timesheet is None:
            return TimesheetResolutionDecision(
                status=TimesheetResolutionStatus.RETRY_LATER,
                resolved_period=resolved_period,
                lookup_result=lookup_result,
                requires_user_input=False,
                can_continue=False,
                message=(
                    "La feuille trouvée n'a pas pu être sélectionnée "
                    "correctement."
                ),
            )

        return TimesheetResolutionDecision(
            status=TimesheetResolutionStatus.USE_EXISTING_TIMESHEET,
            selected_timesheet_number=selected_timesheet.number,
            selected_timesheet=selected_timesheet,
            candidate_timesheets=[selected_timesheet],
            resolved_period=resolved_period,
            lookup_result=lookup_result,
            requires_user_input=False,
            can_continue=True,
            message=(
                f"La feuille de temps {selected_timesheet.number} correspond "
                "à la période demandée et peut être utilisée."
            ),
        )

    if lookup_result.count == 0:
        return TimesheetResolutionDecision(
            status=TimesheetResolutionStatus.CREATE_NEW_TIMESHEET,
            resolved_period=resolved_period,
            lookup_result=lookup_result,
            requires_user_input=True,
            can_continue=False,
            message=(
                "Aucune feuille de temps ne correspond à la période "
                f"du {_format_date(resolved_period.start_date)} au "
                f"{_format_date(resolved_period.end_date)}. "
                "Une nouvelle feuille peut être créée après confirmation."
            ),
        )

    return TimesheetResolutionDecision(
        status=TimesheetResolutionStatus.ASK_USER_TO_CHOOSE,
        candidate_timesheets=list(lookup_result.matched_timesheets),
        resolved_period=resolved_period,
        lookup_result=lookup_result,
        requires_user_input=True,
        can_continue=False,
        message=(
            f"{lookup_result.count} feuilles de temps correspondent à la "
            "période demandée. L'utilisateur doit choisir la feuille à utiliser."
        ),
    )


def _invalid_request(message: str) -> TimesheetResolutionDecision:
    """Construit une décision uniforme pour une demande inexploitable."""

    return TimesheetResolutionDecision(
        status=TimesheetResolutionStatus.INVALID_REQUEST,
        requires_user_input=True,
        can_continue=False,
        message=message,
    )


def _format_date(value: date) -> str:
    """Formate une date pour les messages fonctionnels en français."""

    return value.strftime("%d/%m/%Y")