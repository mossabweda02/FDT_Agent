"""
Module: pydantic_agent.agent
==========================================
Création et gestion de l'agent Pydantic AI avec Azure OpenAI.

Ce module initialise l'agent IA qui utilise Pydantic AI et Azure OpenAI (GPT-4.1-nano)
pour traiter les questions en langage naturel et les convertir en requêtes SQL sécurisées
contre Azure Synapse.

Classes et fonctions:
    - ask(question): Traite une question utilisateur et retourne une réponse.
    - register_tools(agent): Enregistre les outils SQL disponibles pour l'agent.
    - AgentDeps: Dépendances nécessaires pour l'agent afin de passer des informations contextuelles (ex: auth_header).
"""

import os
import logfire
from dotenv import load_dotenv

from backend.core.business import execution_plan
from backend.core.business.workflow_state import WorkflowState, WorkflowStatus, save_workflow_state

load_dotenv()

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from openai import AsyncAzureOpenAI

from backend.agent.scrubbing.question_sanitizer import sanitize_question
from backend.agent.pydantic_agent.tools import register_tools, AgentDeps

from backend.core.prompts.system_prompt import SYSTEM_PROMPT
from backend.core.auth.user_context import UserContext
from backend.core.datetime.date_resolver import build_relative_date_context

# from backend.core.business.intent_classifier import classify_business_intent
from backend.core.business.intent_service import resolve_business_intent
from backend.core.business.scenario_detector import detect_business_scenario
from backend.core.business.execution_plan import build_execution_plan
from backend.core.business.structured_extractor import extract_business_request, normalize_business_request
from dataclasses import asdict

from backend.core.business.business_request_normalizer import normalize_business_request
from backend.core.business.confirmation_messages import build_confirmation_message


# ─────────────────────────────────────────────────────────────────────────────
# Initialisation du client Azure OpenAI, création de l'agent et enregistrement des outils
# ─────────────────────────────────────────────────────────────────────────────

_client = AsyncAzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-12-01-preview",
)

_model = OpenAIChatModel(
    os.environ["AZURE_OPENAI_DEPLOYMENT"],
    provider=OpenAIProvider(openai_client=_client),
)

async def call_azure_openai_for_intent(
    system_prompt: str,
    user_message: str,
) -> str:
    """
    Appelle le même déploiement Azure OpenAI que l'agent principal.

    Cette fonction est uniquement utilisée par le fallback de
    classification d'intention.
    """

    response = await _client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        temperature=0,
        max_tokens=250,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError(
            "Azure OpenAI a retourné une réponse vide pour la classification."
        )

    return content

agent = Agent(
    model=_model,
    system_prompt=SYSTEM_PROMPT,
    deps_type=AgentDeps,
)
register_tools(agent)


async def ask(
    question: str,
    conversation_id=None,
    history=None,
    auth_header: str | None = None,
    user_context: UserContext | None = None,
):
    """
    Exécute une requête utilisateur via l'agent Pydantic AI.

    Args:
        question: Message courant de l'utilisateur.
        conversation_id: Identifiant de la conversation (prévu pour une mémoire persistante).
        history: Historique récent utilisé pour reconstruire le contexte conversationnel.
        auth_header: Jeton d'authentification propagé aux outils Integration Hub.

    Returns:
        Réponse générée par l'agent ou un message d'erreur.
    """
    sq = sanitize_question(question)

    with logfire.span(
        "fdt.agent.ask", # nom du span 
        question_hash=sq.hash, # hash de la question pour identifier les questions similaires
        question_preview=sq.preview, # aperçu de la question pour debug sans exposer des données sensibles
        question_category=sq.category, # catégorie de la question (ex: finance, rh, opérations) pour monitorer les types de questions posées
        question_pii_detected=sq.pii_detected, # Personal Identifiable Information : booléen indiquant si des données sensibles ont été détectées dans la question
    ):
        try:
            # Reconstruit un contexte conversationnel court à partir
            # des derniers échanges. Cette approche est temporaire et
            # sera remplacée par une mémoire persistante.
            context = ""
            if history:
                context = "\n".join(
                    f"{'Utilisateur' if m.role == 'user' else 'Assistant'}: {m.content}"
                    for m in history[-8:]
                )

            date_ctx = build_relative_date_context()
            
            user_email = user_context.email if user_context else None
            user_fullname = user_context.fullname if user_context else None
            user_resource_id = user_context.resource_id if user_context else None
            user_resolution_status = user_context.resource_resolution_status if user_context else None

            enable_llm_intent_fallback = (
            os.getenv("ENABLE_LLM_INTENT_FALLBACK", "false")
            .strip()
            .lower()
            in {"1", "true", "yes", "on"}
            )

            try:
                minimum_intent_confidence = float(
                    os.getenv("LLM_INTENT_MIN_CONFIDENCE", "0.75")
                )
            except ValueError:
                minimum_intent_confidence = 0.75

            business_intent = await resolve_business_intent(
                question,
                llm_call=call_azure_openai_for_intent,
                enable_llm_fallback=enable_llm_intent_fallback,
                minimum_confidence=minimum_intent_confidence,
            )

            business_scenario = detect_business_scenario(
                question,
                business_intent,
            )

            business_request = await extract_business_request(
                message=question,
                intent=business_intent,
                scenario=str(business_scenario.scenario),
                model=_model,
                user_context={
                    "email": user_email,
                    "fullname": user_fullname,
                    "resource_id": user_resource_id,
                },
                date_context={
                    "today": str(date_ctx.today),
                    "yesterday": str(date_ctx.yesterday),
                    "tomorrow": str(date_ctx.tomorrow),
                    "week_start": str(date_ctx.week_start),
                    "week_end": str(date_ctx.week_end),
                    "timezone": date_ctx.timezone,
                },
            )
            normalize_business_request(business_request)
            common_date = business_request.timesheet.explicit_date
            if common_date:
                for entry in business_request.entries:
                    if not entry.date:
                        entry.date = common_date

            if (
                business_request.timesheet.number
                and business_request.timesheet.period_mode == "timesheet_number"
            ):
                for entry in business_request.entries:
                    if entry.repeat_type != "none":
                        entry.date = None
                        entry.dates_must_be_resolved_from_timesheet = True

            execution_plan = build_execution_plan(
                message=question,
                intent=business_intent,
                scenario=str(business_scenario.scenario),
            )

            if conversation_id and execution_plan.requires_confirmation:
                save_workflow_state(
                    WorkflowState(
                        conversation_id=conversation_id,
                        status=WorkflowStatus.WAITING_CONFIRMATION,
                        intent=business_intent,
                        scenario=str(business_scenario.scenario),
                        business_request=business_request.model_dump(),
                        execution_plan=asdict(execution_plan),
                        missing_fields=execution_plan.missing_fields,
                    )
                )
                return build_confirmation_message(str(business_scenario.scenario), business_request)


            prompt = f"""
        Contexte utilisateur connecté :
        - email: {user_email or "non disponible"}
        - nom complet: {user_fullname or "non disponible"}
        - resource_id: {user_resource_id or "non résolu"}
        - statut résolution ressource: {user_resolution_status or "non disponible"}

        Règle stricte :
        Si l'utilisateur demande son email, son nom ou son resource id,
        réponds uniquement avec les valeurs ci-dessus.
        Ne laisse jamais "Resource ID" vide.
        Si resource_id vaut "non résolu", dis "Ressource non résolue".

        Intelligence métier :
        - intention détectée: {business_intent or "non détectée"}
        - scénario détecté: {business_scenario.scenario}
        - raison scénario: {business_scenario.reason}

        Règle :
        Si une intention et un scénario métier sont détectés, tu dois les respecter.
        Ne transforme pas une action métier en simple question analytique.

        Contexte temporel :
        - timezone: {date_ctx.timezone}
        - aujourd'hui: {date_ctx.today}
        - hier: {date_ctx.yesterday}
        - demain: {date_ctx.tomorrow}
        - début de cette semaine: {date_ctx.week_start}
        - fin de cette semaine: {date_ctx.week_end}

        Contexte récent de la conversation :
        {context}

        Instruction importante :
        Si le message actuel est une confirmation courte comme "oui", "confirmer",
        "continue", "continuer" ou "ok", tu dois reprendre l'action métier préparée
        dans le contexte précédent, sans demander de clarification.

        Demande métier structurée :
        {business_request.model_dump()}

        Règle :
        Tu dois utiliser la demande métier structurée comme source principale pour les actions métier.
        Si elle contient missing_information, demande uniquement ces informations.
        
        Plan d'exécution métier :
        {asdict(execution_plan)}
        
        Message actuel de l'utilisateur :
        {question}
        """.strip()
            
            result = await agent.run(
                prompt,
                deps=AgentDeps(auth_header=auth_header, user_context=user_context),
                )
            return result.output
        except Exception as e:
            return f"❌ Erreur agent : {e}"