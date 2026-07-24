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
  - Crée l'application FastAPI avec CORS autorisé (port 3000)
  - Enregistre les middlewares de sécurité et de tracing

Lancement:
  uvicorn backend.server.api_server:app --port 8000 --reload

MVP :
Le contexte est injecté directement dans le prompt.

Une future évolution remplacera ce mécanisme par :
- une mémoire persistante par conversation_id
- un état de workflow métier (création/modification timesheet)
- une gestion native des confirmations utilisateur
"""

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
import json

# from agent.fdt_agent import ask
from backend.agent.pydantic_agent import agent as pydantic_agent
from backend.core.training_examples import get_all_examples
from backend.core.auth.user_context import resolve_user_context

from backend.core.business.workflow_state import (
    get_workflow_state,
)
from backend.core.business.workflow_manager import handle_workflow_message
from backend.core.business.workflow_state import get_workflow_state

# ─────────────────────────────────────────────────────────────────────────────
# Création de l'application FastAPI et configuration CORS
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(title="FDT Agent API", version="1.1.0")

# Instrument fastapi (application web) 
# instrument_fastapi_app(app)

# Communication de l'interface React avec l'API via CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], # les origines autorisées à communiquer avec l'API
    allow_credentials=True, # autoriser les identifiants (cookies, http auth, etc.)
    allow_methods=["*"], # méthodes HTTP autorisées
    allow_headers=["*"], # headers autorisés
)

# ─────────────────────────────────────────────────────────────────────────────
# Modèles Pydantic pour validation des requêtes
# ─────────────────────────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str = "user"
    content: str = ""

class Question(BaseModel):
    question: str
    conversation_id: str | None = None
    history: list[Message] = Field(default_factory=list)

class SuggestRequest(BaseModel):
    """Modèle pour les requêtes POST /suggest."""

    question: str


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints API
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/ask")
async def ask_route(q: Question, authorization: str | None = Header(None)) -> dict:
    auth_header = require_bearer_token(authorization)
    user_context = resolve_user_context(auth_header)
    state = get_workflow_state(q.conversation_id)

    handled = handle_workflow_message(
        question=q.question,
        state=state,
        conversation_id=q.conversation_id,
        user_context=user_context,
        auth_header=auth_header,
    )
    if handled is not None:
        return handled

    answer = await pydantic_agent.ask(
        q.question,
        conversation_id=q.conversation_id,
        history=q.history,
        auth_header=auth_header,
        user_context=user_context,
    )
    if isinstance(answer, dict):
        return answer
    return {"answer": answer}

# ── Suggestion endpoint ───────────────────────────────────────────────────
@app.post("/suggest")
async def suggest_route(req: SuggestRequest, authorization: str | None = Header(default=None)) -> dict:
    require_bearer_token(authorization)

    suggestions = _get_contextual_suggestions(req.question, n=3)
    return {"suggestions": suggestions}

# ── Health check ───────────────────────────────────────────────────
@app.get("/health")
async def health_route() -> dict:
    """ Vérification santé du service FDT Agent API. """
    return {
        "status": "ok",
        "service": "FDT Agent API",
        "version": "1.1.0",
    }


# ── Logique de suggestion et Helpers ──────────────────────────────────────────
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
 

def require_bearer_token(authorization: str | None) -> str:
    """Valide la présence d'un Bearer token et retourne l'en-tête complet."""

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token manquant ou invalide.")
    return authorization


# ── Dev ────────────────────────────────────────────────────────────
# uvicorn agent.api_server:app --port 8000 --reload