"""
agent/api_server.py
====================
Backend FastAPI pour l'interface Chronos-FDT.

Endpoints :
  POST /ask     — Envoie une question à l'agent Azure AI Foundry
  POST /suggest — Retourne 3 suggestions contextuelles basées sur la question

Usage :
  uvicorn agent.api_server:app --port 8000 --reload
"""

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from agent.fdt_agent import ask
from core.training_examples import get_all_examples

app = FastAPI(title="Chronos-FDT API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Modèles ────────────────────────────────────────────────────────
class Question(BaseModel):
    question: str

class SuggestRequest(BaseModel):
    question: str


# ── Endpoint principal ─────────────────────────────────────────────
@app.post("/ask")
async def ask_route(q: Question):
    answer = await ask(q.question)
    return {"answer": str(answer or "")}


# ── Endpoint suggestions contextuelles ────────────────────────────
@app.post("/suggest")
async def suggest_route(req: SuggestRequest):
    """
    Retourne 3 suggestions de questions contextuelles basées sur
    la question de l'utilisateur et les exemples de training_examples.py.

    Logique :
    1. Extraire les mots-clés de la question utilisateur
    2. Scorer chaque exemple de training_examples par pertinence
    3. Retourner les 3 questions les plus pertinentes (non identiques à la question)
    """
    suggestions = _get_contextual_suggestions(req.question, n=3)
    return {"suggestions": suggestions}


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
        if "join" in ex.get("sql_query","").lower().count("join") == \
           ex.get("sql_query","").lower().count("join"):
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


# ── Health check ───────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "Chronos-FDT API"}


# ── Dev ────────────────────────────────────────────────────────────
# uvicorn agent.api_server:app --port 8000 --reload