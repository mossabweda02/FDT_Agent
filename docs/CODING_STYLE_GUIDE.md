# Guide de Style — FDT Agent

Guide professionnel pour les commentaires, docstrings et documentation du code.

---

## 📋 Table des Matières

1. [Docstrings](#docstrings)
2. [Commentaires](#commentaires)
3. [Nommage](#nommage)
4. [Structure](#structure)

---

## 📚 Docstrings

Tous les modules, classes et fonctions publiques **DOIVENT** avoir des docstrings en **Google style**.

### Module Docstring

```python
"""
Module: backend.agent.pydantic_agent.agent
==========================================
Création et gestion de l'agent Pydantic AI avec Azure OpenAI.

Ce module initialise l'agent IA qui utilise Pydantic AI et Azure OpenAI (GPT-4.1-nano)
pour traiter les questions en langage naturel et les convertir en requêtes SQL sécurisées
contre Azure Synapse.

Classes et fonctions:
    - ask(question): Traite une question utilisateur et retourne une réponse.

Auteur: FDT Team
Version: 1.1.0
"""
```

**Éléments requis:**
- ✅ Chemin complet du module (`backend.agent.pydantic_agent.agent`)
- ✅ Titre clair (ligne 2)
- ✅ Ligne de délimiteur (`=`) sous le titre
- ✅ Description générale (2-3 phrases)
- ✅ Ce que le module contient (classes, fonctions, services)
- ✅ Auteur et version

### Fonction/Méthode Docstring

```python
def ask(question: str) -> str:
    """Traite une question utilisateur et retourne une réponse synthétisée.

    Args:
        question (str): Question en langage naturel de l'utilisateur.

    Returns:
        str: Réponse synthétisée par l'agent, ou message d'erreur préfixé par ❌.

    Raises:
        Exception: Capturée internement, retournée comme message d'erreur.

    Processus:
        1. Sanitise la question (détection PII, hachage, catégorisation)
        2. Crée un span OpenTelemetry pour le monitoring et traçage
        3. Appelle l'agent Pydantic AI avec les outils SQL disponibles
        4. Retourne la réponse en langage naturel ou une erreur
    """
    pass
```

**Éléments requis:**
- ✅ Résumé d'une ligne (suit les triple-quotes)
- ✅ Ligne vide après le résumé
- ✅ Section `Args:` avec type et description
- ✅ Section `Returns:` avec type et description
- ✅ Section `Raises:` si applicable
- ✅ Section `Processus:` ou `Notes:` pour la logique complexe

### Classe Docstring

```python
class Question(BaseModel):
    """Modèle Pydantic pour valider les requêtes POST /ask.

    Attributes:
        question (str): Question en langage naturel de l'utilisateur.

    Example:
        >>> q = Question(question="Combien d'heures en janvier?")
        >>> q.question
        'Combien d\'heures en janvier?'
    """
    question: str
```

**Éléments requis:**
- ✅ Résumé clair
- ✅ Section `Attributes:` avec descriptions
- ✅ Section `Example:` pour les modèles d'utilisation courante

---

## 💬 Commentaires

Les commentaires **DOIVENT** être en français professionnel et clairement délimités.

### Règles Générales

| Règle | ✅ BON | ❌ MAUVAIS |
|-------|--------|-------------|
| **Langue** | Français uniquement | Mix FR/EN |
| **Ton** | Professionnel, clair | Familier, vague |
| **Délimiteur** | `# ────────────` (section) | `# comment aléatoire` |
| **Inline** | Sur la ligne suivante | Fin de ligne |
| **Longueur** | ≤ 80 chars (pour inline) | > 80 chars |

### Types de Commentaires

#### 1️⃣ Délimiteur de Section

Utiliser pour délimiter les grandes sections logiques.

```python
# ─────────────────────────────────────────────────────────────────────────────
# Initialisation du client et du modèle Azure OpenAI
# ─────────────────────────────────────────────────────────────────────────────

_client = AsyncAzureOpenAI(...)
_model = OpenAIModel(...)
```

**Format:**
- Ligne de `# ─────` avant et après la section
- Titre lisible et court (max 60 chars)
- Utilisé sparingly (max 3-4 par fichier)

#### 2️⃣ Bloc Logique (Explanation)

Pour expliquer une section de code sans être au niveau fonction.

```python
# Validation de la requête SQL avant envoi à la base
ok, err = validate_sql_query(query)
if not ok:
    import json
    return json.dumps({"error": err, "rows": [], "row_count": 0})
```

**Format:**
- Sur la ligne AVANT le code
- Court et descriptif (une phrase)
- Commencer par un verbe d'action

#### 3️⃣ Inline (Quick Note)

Pour clarifier une ligne de code complexe.

```python
_credential: DefaultAzureCredential | None = None  # Cache, créé une seule fois
engine = create_engine(..., poolclass=NullPool)     # Pas de pooling (tokens expirent)
```

**Format:**
- Après 2+ espaces (`  #`)
- Court (≤ 60 chars)
- Explication, pas duplication du code

#### 4️⃣ Warning/Important

Pour signaler des pièges ou des points critiques.

```python
# ⚠️ Modifier TOUJOURS en parallèle avec backend/tools/functions_tool.py
# Sinon les outils ne seront pas enregistrés correctement

# ❌ Ne PAS supprimer les exemples existants
# (Cela casse le Few-Shot du prompt système)
```

**Format:**
- Utiliser les émojis: ⚠️ (attention), ❌ (danger), ✅ (note positive)
- Court et impactant
- Expliquer le "pourquoi"

---

## 🏷️ Nommage

### Fichiers Python

```
✅ CORRECT:
  functions_tool.py       (singulier + underscore)
  sql_validator.py        (verbe + objet)
  connection.py           (nettement ce qu'on connecte)

❌ INCORRECT:
  functions_tools.py      (pluriel)
  sql-validator.py        (tiret)
  connect_synapse.py      (trop générique)
```

### Variables

```python
✅ CORRECT:
  _credential: DefaultAzureCredential   # Private, underscore
  _client = AsyncAzureOpenAI(...)      # Private helper
  SYNAPSE_SERVER = "..."               # Constante globale
  agent = Agent(...)                   # Instance publique

❌ INCORRECT:
  cred = DefaultAzureCredential()       # Trop court
  Client = AsyncAzureOpenAI()          # Pas constants
  synapse_server = "..."               # Constantes en CAPS
```

### Fonctions

```python
✅ CORRECT:
  def list_tables() -> str:            # Verbe + objet
  def validate_sql_query(query: str):  # Action
  def _get_credential():               # Private helper

❌ INCORRECT:
  def get_my_tables():                 # "my"
  def check():                         # Vague
  def f(q):                            # Non-descriptif
```

---

## 🗂️ Structure

### Ordre dans un Module

```python
# 1. Module docstring
"""
Module: backend.agent.pydantic_agent.agent
...
"""

# 2. Imports
import os
import logfire
from pydantic_ai import Agent

# 3. Constantes globales
_client = AsyncAzureOpenAI(...)
_model = OpenAIModel(...)

# 4. Private helpers (_fonction)
def _get_credential():
    ...

# 5. Public functions
def ask(question: str) -> str:
    ...

# 6. Classes (si applicable)
class MyClass:
    ...

# 7. Main
if __name__ == "__main__":
    ...
```

### Imports Organization

```python
# Standard library
import os
import struct
from typing import Tuple, Optional

# Third-party
from pydantic_ai import Agent
from sqlalchemy import create_engine

# Local/project
from backend.core.prompts.system_prompt import SYSTEM_PROMPT
from backend.tools.sql_validator import validate_sql_query
```

**Règles:**
1. Standard library d'abord
2. Third-party ensuite
3. Local imports en dernier
4. Alphabétique dans chaque groupe
5. Imports groupés, une ligne par groupe

---

## 📝 Exemples Complets

### ✅ BON EXEMPLE

```python
"""
Module: backend.tools.sql_validator
====================================
Validateur SQL pour prévenir les opérations dangereuses.

Ce module implémente une couche de sécurité locale pour valider toute requête SQL
avant envoi à Azure Synapse. Elle empêche les opérations d'écriture et les injections.

Fonctions publiques:
    - validate_sql_query(query): Valide une requête avant exécution
    - sanitize_query_for_logging(query): Nettoie pour les logs

Auteur: FDT Team
Version: 1.1.0
"""

import re
from typing import Tuple, Optional


def validate_sql_query(query: str) -> Tuple[bool, Optional[str]]:
    """Valide une requête SQL en vérifiant les opérations interdites.

    Args:
        query (str): Requête SQL à valider.

    Returns:
        Tuple[bool, Optional[str]]: (valide, message_erreur)
                                   - (True, None) si valide
                                   - (False, "message") si invalide

    Règles appliquées:
        1. Mots interdits : INSERT/UPDATE/DELETE/DROP/ALTER/CREATE
        2. Doit commencer par SELECT ou WITH
        3. Pas de commentaires SQL (-- et /*)
        4. Pas de multi-statements (;)
    """
    if not query:
        return False, "Requête vide"

    q = " ".join(query.strip().split()).upper()

    # ─────────────────────────────────────────────────────────────────────────────
    # Vérification des opérations interdites
    # ─────────────────────────────────────────────────────────────────────────────

    forbidden = [
        "INSERT", "UPDATE", "DELETE", "DROP",
        "ALTER", "CREATE", "EXEC", "MERGE"
    ]

    for f in forbidden:
        if f in q:
            return False, f"❌ Opération interdite : {f}"

    # Vérifier que la requête commence par SELECT ou WITH
    if not (q.startswith("SELECT") or q.startswith("WITH")):
        return False, "❌ Seuls SELECT et WITH sont autorisés"

    # Pas de commentaires SQL
    if "--" in query or "/*" in query:
        return False, "❌ Les commentaires SQL ne sont pas autorisés"

    # Pas de multi-statements
    if ";" in query.strip()[:-1]:
        return False, "❌ Les requêtes multi-statements ne sont pas autorisées"

    return True, None


def sanitize_query_for_logging(query: str, max_length: int = 200) -> str:
    """Nettoie et tronque une requête pour les logs.

    Élimine les whitespaces excessifs et tronque pour éviter d'exposer
    les données sensibles dans les logs.

    Args:
        query (str): Requête brute.
        max_length (int): Longueur max après troncature. Défaut: 200.

    Returns:
        str: Requête nettoyée et tronquée.

    Example:
        >>> sanitize_query_for_logging("SELECT  *  FROM  table", 20)
        'SELECT * FROM tabl'
    """
    clean = " ".join(query.strip().split())  # Normaliser les espaces
    return clean[:max_length]
```

### ❌ MAUVAIS EXEMPLE

```python
"""
sql_validator.py - valide les trucs sql

Ce fichier fait la validation des requetes sql pour eviter les problemes
"""

import re
from typing import Tuple, Optional

def validate_sql_query(query: str) -> Tuple[bool, Optional[str]]:
    # cette fonction valide
    if not query:
        return False, "Empty"
    q = " ".join(query.strip().split()).upper() # Normalise la requête

    # check for bad stuff
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "EXEC", "MERGE"]
    for f in forbidden: # loop through forbidden words
        if f in q: return False, f"Forbidden: {f}" # Check if word present

    # weird edge case
    if not (q.startswith("SELECT") or q.startswith("WITH")):
        return False, "Only SELECT/WITH"

    if "--" in query or "/*" in query: return False, "No comments" # prevent sql injection
    if ";" in query.strip()[:-1]: return False, "No multi-statement"

    return True, None  # ok
```

---

## 🎯 Checklist avant Commit

- [ ] Tous les modules ont un docstring Google-style
- [ ] Toutes les fonctions publiques ont des docstrings
- [ ] Pas de commentaires en anglais (sauf noms techniques)
- [ ] Sections logiques bien délimitées (`# ─────`)
- [ ] Noms de variables clairs et descriptifs
- [ ] Imports organizés (stdlib, third-party, local)
- [ ] Pas de commentaires en fin de ligne > 60 chars
- [ ] Pas de "TODO" ou "FIXME" sans contexte
- [ ] Les chemins utilisent `backend/frontend/tests/` (pas `./`)
- [ ] Les références aux fichiers utilisent les bons chemins

---

## 📚 Ressources

- Google Python Style Guide: https://google.github.io/styleguide/pyguide.html
- PEP 257 Docstring Conventions: https://www.python.org/dev/peps/pep-0257/
- Type Hints: https://docs.python.org/3/library/typing.html

---

## 🔧 Tools Recommandés

```bash
# Formatage automatique
pip install black autopep8

# Linting
pip install pylint flake8

# Type checking
pip install mypy

# Docstring checker
pip install pydocstyle
```

Exemple `.flake8`:
```ini
[flake8]
max-line-length = 100
extend-ignore = E203, W503
exclude = venv,__pycache__,.git
```

---

**Dernière mise à jour**: Mai 21, 2026  
**Auteur**: FDT Team  
**Version**: 1.1.0
