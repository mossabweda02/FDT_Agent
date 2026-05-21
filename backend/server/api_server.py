"""
Module: backend.server.api_server
==================================
Backend FastAPI pour l'API FDT Agent.

Ce module expose les endpoints HTTP pour communiquer avec le frontend React:
  - POST /ask     : Envoie une question à l'agent et récupère la réponse
  - POST /suggest : Retourne 3 suggestions de questions contextuelles
  - GET /health   : Vérification santé du service

Architecture:
  - Configure l'observabilité (Logfire + OpenTelemetry + Scrubbing)
  - Crée l'application FastAPI avec CORS autorisé (port 5173)
  - Enregistre les middlewares de sécurité et de tracing

Lancement:
  uvicorn backend.server.api_server:app --port 8000 --reload
"""

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logfire

from backend.agent.scrubbing.observability import (
    configure_observability,
    instrument_fastapi_app,
    instrument_pydantic_ai,
)

configure_observability()
instrument_pydantic_ai()

# from agent.fdt_agent import ask
from backend.agent.pydantic_agent import agent as pydantic_agent
from backend.core.training_examples import get_all_examples

# ─────────────────────────────────────────────────────────────────────────────
# Création de l'application FastAPI et configuration CORS
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(title="FDT Agent API", version="1.1.0")

# Instrument fastapi (application web) 
instrument_fastapi_app(app)

# Communication de l'interface React avec l'API via CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # les origines autorisées à communiquer avec l'API
    allow_credentials=True, # autoriser les identifiants (cookies, http auth, etc.)
    allow_methods=["*"], # méthodes HTTP autorisées
    allow_headers=["*"], # headers autorisés
)

# ─────────────────────────────────────────────────────────────────────────────
# Modèles Pydantic pour validation des requêtes
# ─────────────────────────────────────────────────────────────────────────────

class Question(BaseModel):
    """Modèle pour les requêtes POST /ask."""

    question: str


class SuggestRequest(BaseModel):
    """Modèle pour les requêtes POST /suggest."""

    question: str


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints API
# ─────────────────────────────────────────────────────────────────────────────


@app.post("/ask")
async def ask_route(q: Question) -> dict:
    """Traite une question utilisateur et retourne une réponse de l'agent.

    Args:
        q (Question): Modèle contenant la question utilisateur.

    Returns:
        dict: {"answer": str} - Réponse synthétisée par l'agent.

    Process:
        1. Reçoit la question via POST
        2. Délègue à pydantic_agent.ask()
        3. Retourne la réponse en JSON
    """
    answer = await pydantic_agent.ask(q.question)
    return {"answer": answer}


@app.post("/suggest")
async def suggest_route(req: SuggestRequest) -> dict:
    """Retourne 3 suggestions de questions contextuelles.

    Args:
        req (SuggestRequest): Modèle contenant la question utilisateur.

    Returns:
        dict: {"suggestions": list[str]} - 3 questions suggérées.

    Logique:
        1. Extrait les mots-clés de la question utilisateur
        2. Score chaque exemple de training_examples par pertinence
        3. Retourne les 3 questions les plus pertinentes (non identiques)
    """
    suggestions = _get_contextual_suggestions(req.question, n=3)
    return {"suggestions": suggestions}


@app.get("/health")
async def health_route() -> dict:
    """Vérification santé du service FDT Agent API.

    Returns:
        dict: {"status": "ok", "service": str, "version": str}
    """
    return {
        "status": "ok",
        "service": "FDT Agent API",
        "version": "1.1.0",
    }


# ── Logique de suggestion ──────────────────────────────────────────
def _get_contextual_suggestions(user_question: str, n: int = 3) -> list[str]:
    """
    Sélectionne les suggestions les plus pertinentes depuis training_examples.py.
    """
    examples = get_all_examples()
    user_q_lower = user_question.lower()

    # Extraire les mots-clés significatifs (> 3 chars, pas de mots vides)
    STOP_WORDS = {
        "les", "des", "une", "est", "dans", "sur", "par", "pour",
        "que", "qui", "avec", "ont", "été", "quel", "quels", "quelles",
        "combien", "quelles", "heures", "the", "and", "for", "what", "how",
        "are", "were", "have", "has", "from",
    }
    # Mots-clés : filtrer les mots de la question pour ne garder que les plus significatifs
    keywords = [
        w for w in user_q_lower.replace("?","").replace(",","").split()
        if len(w) > 3 and w not in STOP_WORDS
    ]

    # Mapper thèmes → exemples pertinents
    THEME_MAP = {
        "heure":     ["heures", "temps", "saisies", "enregistrées", "hours"],
        "projet":    ["projet", "projets", "project", "prj"],
        "employé":   ["employé", "employés", "ressource", "employee", "worker", "nom"],
        "tâche":     ["tâche", "tâches", "task", "activité", "activity"],
        "mois":      ["janvier", "février", "mars", "avril", "mai", "juin",
                      "juillet", "août", "septembre", "octobre", "novembre", "décembre",
                      "january", "february", "march"],
        "rentable":  ["rentable", "rentabilité", "marge", "profit", "coût", "cost"],
        "approuvé":  ["approuvé", "approuvées", "approved", "validé"],
        "top":       ["top", "plus", "meilleur", "premier", "best"],
    }

    # Déterminer les thèmes de la question
    active_themes = set()
    for theme, words in THEME_MAP.items():
        if any(w in user_q_lower for w in words):
            active_themes.add(theme)

    # Scorer chaque exemple
    scored = []
    for ex in examples:
        q = ex.get("user_question", "")
        if not q or q.lower() == user_q_lower:
            continue  # Exclure la question identique

        score = 0
        q_lower = q.lower()

        # Score par mots-clés communs
        for kw in keywords:
            if kw in q_lower:
                score += 2

        # Score par thèmes communs
        for theme, words in THEME_MAP.items():
            if theme in active_themes and any(w in q_lower for w in words):
                score += 3

        # Bonus pour les questions de même niveau de complexité
        sql = ex.get("sql_query", "").lower()
        join_count = sql.count("join")

        if join_count > 0:
            score += 1

        if score > 0:
            scored.append((score, q))

    # Trier par score décroissant, dépliquer
    scored.sort(key=lambda x: x[0], reverse=True)
    seen = set()
    results = []
    for score, q in scored:
        if q not in seen:
            seen.add(q)
            results.append(q)
        if len(results) >= n:
            break

    # Si pas assez de suggestions, compléter avec des questions de base
    fallback = [
        "Combien d'heures ont été saisies en janvier 2026 ?",
        "Top 3 projets par heures en 2026 ?",
        "Heures par employé en janvier 2026 ?",
        "Quelles tâches ont été effectuées sur le projet PRJ-00329 ?",
        "Quels sont les projets les plus rentables ?",
    ]
    for fb in fallback:
        if len(results) >= n:
            break
        if fb not in seen and fb.lower() != user_q_lower:
            results.append(fb)

    return results[:n]

# ──── API pour tester le scrubbing des données sensibles ────
# Generer des spans de test pour valider que les données sensibles sont correctement scrubbées.

@app.get("/test-scrubbing-suite")
async def test_scrubbing_suite():

    # ─── Données sensées scrubber ───

    # 1. RH/employé
    with logfire.span(
        "test scrubbing - hr sensitive fields",
        scrubbing_group="hr",
        employee_name="Mohamed Ben Ali",
        resource_name="Mohamed Ben Ali",
        PERSONNELNUMBER="EMP-458921",
        RESOURCEID="RES-2936",
        WORKER="123456",
        salary=5000,
    ):
        pass

    # 2. Finance 
    with logfire.span(
        "test scrubbing - finance sensitive fields",
        scrubbing_group="finance",
        StandardCost=1000.0,
        TotalStandardCost=8000.0,
        SalePrice=1500.0,
        TotalSalePrice=12000.0,
        RealCost=900.0,
        TotalRealCost=7200.0,
        TotalAmountCompanyCur=3000.0,
        margin=0.25,
        budget=50000,
        revenue=75000,
        profit=25000,
    ):
        pass

    # 3. Notes / texte libre 
    with logfire.span(
        "test scrubbing - free text notes",
        scrubbing_group="notes",
        INTERNALNOTE="Mohamed Ben Ali worked on confidential task",
        EXTERNALNOTE="Client Airbus Defense validation",
        description="Contains sensitive business context",
        referenceNumber="REF-SECRET-001",
    ):
        pass

    # 4. Secrets techniques 
    with logfire.span(
        "test scrubbing - technical secrets",
        scrubbing_group="secrets",
        connection_string="Driver={ODBC};Server=synapse;Pwd=secret",
        odbc="DSN=FDT;UID=user;PWD=password",
        api_key="sk-secret-test",
        client_secret="client-secret-value",
        token="secret-token-value",
        synapse_key="synapse-secret-key",
    ):
        pass

    # 5. SQL / prompt leakage 
    with logfire.span(
        "test scrubbing - sql and llm content",
        scrubbing_group="sql_llm",
        db_statement="SELECT * FROM timesheet_line WHERE employee_name = 'Mohamed Ben Ali'",
        sql="SELECT salary FROM ga_resource WHERE PERSONNELNUMBER = 'EMP-458921'",
        prompt="Quel est le salaire de Mohamed Ben Ali ?",
        completion="Le salaire de Mohamed Ben Ali est 5000 EUR",
        response="Sensitive model response",
    ):
        pass
    
    # ──── Données peuvent être visibles (non sensibles) ────
    # 6. Champs safe : visibles
    with logfire.span(
        "test scrubbing - safe telemetry fields",
        scrubbing_group="safe",
        question_preview="Combien d’heures a travaillé [PERSON] en janvier ?",
        question_hash="abc123def456",
        question_category="heures",
        question_pii_detected=True,
        model_name="gpt-4.1-nano",
        agent_name="fdt-agent",
        table_name="timesheet_line",
        row_count=25,
        operation_cost=0.002,
    ):
        pass

    # 7. Attributs OTel / monitoring : visibles
    with logfire.span(
        "test scrubbing - otel safe attributes",
        scrubbing_group="otel",
        **{
            "gen_ai.request.model": "gpt-4.1-nano",
            "gen_ai.usage.input_tokens": 120,
            "gen_ai.usage.output_tokens": 80,
            "gen_ai.usage.total_tokens": 200,
            "http.request.method": "GET",
            "http.response.status_code": 200,
            "http.route": "/test-scrubbing-suite",
            "service.name": "fdt-agent",
            "db.system": "mssql",
            "db.operation": "SELECT",
        },
    ):
        pass

    return {
        "status": "ok",
        "message": "scrubbing suite spans generated",
        "spans": [
            "hr sensitive fields",
            "finance sensitive fields",
            "free text notes",
            "technical secrets",
            "sql and llm content",
            "safe telemetry fields",
            "otel safe attributes",
        ],
    }    

# ── Health check ───────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "FDT Agent API"}


# ── Dev ────────────────────────────────────────────────────────────
# uvicorn agent.api_server:app --port 8000 --reload