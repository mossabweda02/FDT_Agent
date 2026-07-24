"""
Module: tests.diagnostics.scenario_cases
========================================

Catalogue des scénarios de diagnostic du FDT Agent.

Ce module centralise les demandes utilisateur utilisées pour évaluer la
classification des intentions, la détection des scénarios et la couverture
fonctionnelle du workflow métier.

Il ne contient aucune logique de production et n'effectue aucun appel vers
Azure OpenAI, Azure Synapse ou Integration Hub.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DiagnosticStage(StrEnum):
    """Étapes techniques susceptibles d'être responsables d'un échec."""

    CLASSIFICATION = "classification"
    SCENARIO_DETECTION = "scenario_detection"
    EXTRACTION = "extraction"
    DATE_RESOLUTION = "date_resolution"
    BUSINESS_RESOLUTION = "business_resolution"
    TIMESHEET_LOOKUP = "timesheet_lookup"
    VALIDATION = "validation"
    CONFIRMATION = "confirmation"
    EXECUTION = "execution"
    CONSULTATION = "consultation"
    DATA_MODEL = "data_model"


class ScenarioStatus(StrEnum):
    """État fonctionnel constaté lors des tests manuels."""

    VALID = "valid"
    INVALID = "invalid"
    NOT_SUPPORTED = "not_supported"


@dataclass(frozen=True)
class ScenarioCase:
    """Description d'un scénario utilisateur et de son comportement attendu."""

    case_id: str
    title: str
    prompt: str
    expected_intent: str
    expected_scenario: str
    status: ScenarioStatus
    responsible_stages: tuple[DiagnosticStage, ...]
    expected_summary: str


SCENARIO_CASES: tuple[ScenarioCase, ...] = (
    ScenarioCase(
        case_id="1.1",
        title="Création d'une feuille pour aujourd'hui",
        prompt="Créer une feuille de temps pour aujourd'hui.",
        expected_intent="CREATE_TIMESHEET",
        expected_scenario="CREATE_EMPTY_TIMESHEET",
        status=ScenarioStatus.VALID,
        responsible_stages=(),
        expected_summary=(
            "La date du jour est résolue et une confirmation de création "
            "est préparée."
        ),
    ),
    ScenarioCase(
        case_id="1.2",
        title="Création d'une feuille pour la semaine prochaine",
        prompt="Créer une feuille de temps pour la semaine prochaine.",
        expected_intent="CREATE_TIMESHEET",
        expected_scenario="CREATE_EMPTY_TIMESHEET",
        status=ScenarioStatus.INVALID,
        responsible_stages=(
            DiagnosticStage.DATE_RESOLUTION,
            DiagnosticStage.EXECUTION,
        ),
        expected_summary=(
            "La semaine prochaine est résolue en dates absolues et le début "
            "de cette période est transmis à Integration Hub."
        ),
    ),
    ScenarioCase(
        case_id="1.3",
        title="Création d'une feuille pour une date explicite",
        prompt="Créer une feuille de temps pour le 24 juin 2026.",
        expected_intent="CREATE_TIMESHEET",
        expected_scenario="CREATE_EMPTY_TIMESHEET",
        status=ScenarioStatus.INVALID,
        responsible_stages=(
            DiagnosticStage.DATE_RESOLUTION,
            DiagnosticStage.EXECUTION,
        ),
        expected_summary=(
            "La semaine contenant le 24 juin 2026 est calculée et utilisée "
            "pour la création."
        ),
    ),
    ScenarioCase(
        case_id="2",
        title="Création de plusieurs feuilles",
        prompt=(
            "Créer 3 feuilles de temps : une pour cette semaine, une pour "
            "le 14 juin 2026 et l'autre pour la semaine prochaine."
        ),
        expected_intent="CREATE_TIMESHEET",
        expected_scenario="CREATE_MULTIPLE_TIMESHEETS",
        status=ScenarioStatus.NOT_SUPPORTED,
        responsible_stages=(
            DiagnosticStage.DATA_MODEL,
            DiagnosticStage.SCENARIO_DETECTION,
            DiagnosticStage.EXTRACTION,
            DiagnosticStage.EXECUTION,
        ),
        expected_summary=(
            "Trois périodes sont extraites, résolues et présentées dans une "
            "confirmation globale."
        ),
    ),
    ScenarioCase(
        case_id="3.1",
        title="Ajout d'une ligne sans numéro de feuille",
        prompt=(
            "Ajoute 2h le 2026-07-14 sur le projet PRJ-00042, "
            "tâche TSK-00062, catégorie Development."
        ),
        expected_intent="ADD_TIME_ENTRY",
        expected_scenario="SINGLE_TIME_ENTRY",
        status=ScenarioStatus.INVALID,
        responsible_stages=(
            DiagnosticStage.TIMESHEET_LOOKUP,
            DiagnosticStage.VALIDATION,
        ),
        expected_summary=(
            "La feuille couvrant le 14 juillet 2026 est recherchée "
            "automatiquement pour l'utilisateur connecté."
        ),
    ),
    ScenarioCase(
        case_id="3.2",
        title="Ajout d'une ligne avec identifiants et numéro de feuille",
        prompt=(
            "Ajoute 2h le 2026-07-14 sur le projet PRJ-00042, "
            "tâche TSK-00062, catégorie Development dans la feuille "
            "de temps TS-0000318."
        ),
        expected_intent="ADD_TIME_ENTRY",
        expected_scenario="SINGLE_TIME_ENTRY",
        status=ScenarioStatus.VALID,
        responsible_stages=(),
        expected_summary=(
            "La ligne est extraite avec ses identifiants et préparée pour "
            "confirmation."
        ),
    ),
    ScenarioCase(
        case_id="3.3",
        title="Ajout d'une ligne avec noms métier",
        prompt=(
            "Ajoute 5h le 2026-07-17 sur Integration Hub V0.1, "
            "la tâche Develop FE, catégorie Operateur dans la feuille "
            "de temps TS-0000318."
        ),
        expected_intent="ADD_TIME_ENTRY",
        expected_scenario="SINGLE_TIME_ENTRY",
        status=ScenarioStatus.INVALID,
        responsible_stages=(
            DiagnosticStage.BUSINESS_RESOLUTION,
            DiagnosticStage.VALIDATION,
        ),
        expected_summary=(
            "Le projet, la tâche et la catégorie sont résolus vers leurs "
            "identifiants Integration Hub avant confirmation."
        ),
    ),
    ScenarioCase(
        case_id="4.1",
        title="Plusieurs tâches avec identifiants",
        prompt=(
            "Dans la feuille TS-0000318, le 2026-07-17, ajoute 2h sur "
            "PRJ-00042, tâche TSK-00062, catégorie Development, et 3h "
            "sur PRJ-00042, tâche TSK-00063, catégorie Support."
        ),
        expected_intent="ADD_MULTIPLE_TIME_ENTRIES",
        expected_scenario="MULTI_TASK_SAME_PROJECT",
        status=ScenarioStatus.INVALID,
        responsible_stages=(
            DiagnosticStage.SCENARIO_DETECTION,
        ),
        expected_summary=(
            "Deux lignes distinctes sont extraites avec la même date et "
            "le même projet."
        ),
    ),
    ScenarioCase(
        case_id="4.2",
        title="Plusieurs lignes avec noms de projets et tâches",
        prompt=(
            "Dans la feuille TS-0000318, le 2026-07-17, ajoute 2h sur "
            "Integration Hub V0.1, la tâche Develop FE, catégorie Operateur, "
            "et 3h sur Nova Construction, tâche Prepare building permit "
            "documentation, catégorie Development."
        ),
        expected_intent="ADD_MULTIPLE_TIME_ENTRIES",
        expected_scenario="MULTI_PROJECT_SAME_DAY",
        status=ScenarioStatus.INVALID,
        responsible_stages=(
            DiagnosticStage.CLASSIFICATION,
            DiagnosticStage.SCENARIO_DETECTION,
            DiagnosticStage.EXTRACTION,
            DiagnosticStage.BUSINESS_RESOLUTION,
        ),
        expected_summary=(
            "Deux entrées sont extraites et chaque couple projet/tâche est "
            "résolu indépendamment."
        ),
    ),
    ScenarioCase(
        case_id="5.1",
        title="Plusieurs tâches sur un projet avec identifiants",
        prompt=(
            "Ajoute sur PRJ-00042 2h pour TSK-00062 et 2h pour TSK-00063 "
            "pour le 2026-07-16 dans la feuille TS-0000318."
        ),
        expected_intent="ADD_MULTIPLE_TIME_ENTRIES",
        expected_scenario="MULTI_TASK_SAME_PROJECT",
        status=ScenarioStatus.VALID,
        responsible_stages=(),
        expected_summary=(
            "Deux tâches du même projet sont reconnues comme deux lignes."
        ),
    ),
    ScenarioCase(
        case_id="5.2",
        title="Plusieurs tâches sur un projet avec noms métier",
        prompt=(
            "Ajoute sur Nova Construction 2h pour Prepare building permit "
            "documentation et 2h pour Submit and track permit approvals "
            "pour le 2026-07-17 dans la feuille TS-0000318."
        ),
        expected_intent="ADD_MULTIPLE_TIME_ENTRIES",
        expected_scenario="MULTI_TASK_SAME_PROJECT",
        status=ScenarioStatus.INVALID,
        responsible_stages=(
            DiagnosticStage.CLASSIFICATION,
            DiagnosticStage.SCENARIO_DETECTION,
            DiagnosticStage.EXTRACTION,
            DiagnosticStage.BUSINESS_RESOLUTION,
        ),
        expected_summary=(
            "Le projet commun et les deux tâches sont extraits puis résolus "
            "sans exiger leurs identifiants."
        ),
    ),
    ScenarioCase(
        case_id="6",
        title="Consultation de la liste des feuilles",
        prompt="Affiche la liste de mes feuilles de temps.",
        expected_intent="CONSULT_TIMESHEET",
        expected_scenario="LIST_TIMESHEETS",
        status=ScenarioStatus.INVALID,
        responsible_stages=(
            DiagnosticStage.SCENARIO_DETECTION,
            DiagnosticStage.CONSULTATION,
        ),
        expected_summary=(
            "Les feuilles de la ressource connectée sont listées sans "
            "confirmation."
        ),
    ),
    ScenarioCase(
        case_id="7.1",
        title="Consultation d'une feuille par numéro",
        prompt="Affiche le détail de la feuille de temps TS-0000318.",
        expected_intent="CONSULT_TIMESHEET",
        expected_scenario="GET_TIMESHEET_DETAIL",
        status=ScenarioStatus.VALID,
        responsible_stages=(),
        expected_summary=(
            "Le détail de la feuille fournie est récupéré sans confirmation."
        ),
    ),
    ScenarioCase(
        case_id="7.2",
        title="Consultation d'une feuille par période",
        prompt="Affiche le détail de la feuille de temps de cette semaine.",
        expected_intent="CONSULT_TIMESHEET",
        expected_scenario="GET_TIMESHEET_DETAIL",
        status=ScenarioStatus.INVALID,
        responsible_stages=(
            DiagnosticStage.DATE_RESOLUTION,
            DiagnosticStage.TIMESHEET_LOOKUP,
            DiagnosticStage.CONSULTATION,
        ),
        expected_summary=(
            "La semaine courante est résolue et l'unique feuille "
            "correspondante est consultée."
        ),
    ),
    ScenarioCase(
        case_id="8",
        title="Consultation des heures enregistrées",
        prompt="Affiche les heures enregistrées dans la feuille TS-0000318.",
        expected_intent="CONSULT_TIMESHEET",
        expected_scenario="GET_TIMESHEET_LINES",
        status=ScenarioStatus.INVALID,
        responsible_stages=(
            DiagnosticStage.SCENARIO_DETECTION,
            DiagnosticStage.CONSULTATION,
        ),
        expected_summary=(
            "Les lignes de la feuille sont récupérées via Integration Hub."
        ),
    ),
    ScenarioCase(
        case_id="9.1",
        title="Plusieurs dates avec informations communes",
        prompt=(
            "Ajoute 2h lundi, 3h mardi et 5h mercredi de la semaine prochaine "
            "sur le projet PRJ-00042, tâche TSK-00062, catégorie Development."
        ),
        expected_intent="ADD_MULTIPLE_TIME_ENTRIES",
        expected_scenario="MULTIPLE_DATED_ENTRIES",
        status=ScenarioStatus.INVALID,
        responsible_stages=(
            DiagnosticStage.EXTRACTION,
            DiagnosticStage.DATE_RESOLUTION,
            DiagnosticStage.TIMESHEET_LOOKUP,
            DiagnosticStage.DATA_MODEL,
        ),
        expected_summary=(
            "Trois entrées sont produites avec des heures différentes et "
            "les références métier communes sont propagées."
        ),
    ),
    ScenarioCase(
        case_id="9.2",
        title="Plusieurs dates avec numéro de feuille",
        prompt=(
            "Ajoute dans la feuille de temps TS-0000344 2h lundi, 3h mardi "
            "et 5h mercredi de la semaine prochaine sur le projet PRJ-00042, "
            "tâche TSK-00062, catégorie Development."
        ),
        expected_intent="ADD_MULTIPLE_TIME_ENTRIES",
        expected_scenario="MULTIPLE_DATED_ENTRIES",
        status=ScenarioStatus.INVALID,
        responsible_stages=(
            DiagnosticStage.EXTRACTION,
            DiagnosticStage.DATE_RESOLUTION,
            DiagnosticStage.DATA_MODEL,
        ),
        expected_summary=(
            "Trois lignes datées sont extraites et leur cohérence avec la "
            "période réelle de TS-0000344 est vérifiée."
        ),
    ),
    ScenarioCase(
        case_id="10.1",
        title="Total des heures par numéro de feuille",
        prompt="Quel est le total des heures de la feuille TS-0000318 ?",
        expected_intent="CONSULT_TIMESHEET",
        expected_scenario="GET_TIMESHEET_TOTAL",
        status=ScenarioStatus.INVALID,
        responsible_stages=(
            DiagnosticStage.SCENARIO_DETECTION,
            DiagnosticStage.CONSULTATION,
        ),
        expected_summary=(
            "Les lignes de la feuille sont récupérées puis leurs quantités "
            "sont additionnées."
        ),
    ),
    ScenarioCase(
        case_id="10.2",
        title="Total des heures par période naturelle",
        prompt="Quel est le total des heures de cette semaine ?",
        expected_intent="CONSULT_TIMESHEET",
        expected_scenario="GET_TIMESHEET_TOTAL",
        status=ScenarioStatus.INVALID,
        responsible_stages=(
            DiagnosticStage.DATE_RESOLUTION,
            DiagnosticStage.TIMESHEET_LOOKUP,
            DiagnosticStage.CONSULTATION,
        ),
        expected_summary=(
            "Les feuilles couvrant la semaine courante sont retrouvées et "
            "le total de leurs lignes est calculé."
        ),
    ),
)


def get_case(case_id: str) -> ScenarioCase:
    """Retourne un scénario de diagnostic à partir de son identifiant."""

    for case in SCENARIO_CASES:
        if case.case_id == case_id:
            return case

    raise KeyError(f"Scénario de diagnostic inconnu : {case_id}")