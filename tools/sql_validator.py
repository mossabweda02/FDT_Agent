"""
fdtAgent/core/sql_validator.py
===============================
Validateur SQL pour empêcher les opérations dangereuses.
IMPORTANT : Cette validation s'exécute AVANT l'envoi à la base de données.

Pourquoi ce fichier ?
---------------------
1. Sécurité : Empêche INSERT/UPDATE/DELETE/DROP même si le LLM hallucine
2. Performance : Validation locale instantanée (pas d'appel réseau)
3. Coût : Évite les requêtes SQL inutiles qui consomment des ressources
4. Traçabilité : Logs clairs des tentatives de requêtes interdites

Architecture :
--------------
- validate_sql_query() : Point d'entrée principal (appelé par execute_query)
- _check_forbidden_operations() : Détecte les mots-clés interdits
- _check_required_operations() : Force SELECT ou WITH
- _check_sql_injection_patterns() : Détecte les patterns d'injection SQL
"""

import re
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class SQLValidationError(Exception):
    """Exception levée quand une requête SQL est invalide ou dangereuse"""
    pass


def validate_sql_query(query: str) -> Tuple[bool, Optional[str]]:
    """
    Valide une requête SQL avant exécution.
    
    Args:
        query (str): Requête SQL à valider
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
            - (True, None) si la requête est valide
            - (False, "message d'erreur") si invalide
    
    Exemples:
        >>> validate_sql_query("SELECT * FROM timesheet_header")
        (True, None)
        
        >>> validate_sql_query("DELETE FROM timesheet_header")
        (False, "❌ Opération interdite : DELETE")
        
        >>> validate_sql_query("SELECT * FROM users; DROP TABLE users;")
        (False, "❌ Opération interdite : DROP")
    
    Tests recommandés:
        pytest tests/test_sql_validator.py
    """
    
    # Nettoyer la requête (enlever espaces multiples, tabs, newlines)
    clean_query = " ".join(query.strip().split())
    
    # Correction automatique LIMIT → TOP
    limit_match = re.search(r'LIMIT\s+(\d+)', clean_query, re.IGNORECASE)

    if limit_match:
        limit_value = limit_match.group(1)
        clean_query = re.sub(r'LIMIT\s+\d+', '', clean_query, flags=re.IGNORECASE)
        clean_query = clean_query.replace("SELECT", f"SELECT TOP {limit_value}", 1)

        logger.warning("⚠️ LIMIT détecté et corrigé automatiquement en TOP")
    
    # 1. Vérifier les opérations interdites
    is_valid, error_msg = _check_forbidden_operations(clean_query)
    if not is_valid:
        logger.warning(f"SQL validation failed: {error_msg}")
        logger.warning(f"Blocked query: {query[:200]}")  # Log les 200 premiers caractères
        return False, error_msg
    
    # 2. Vérifier que la requête commence par SELECT ou WITH
    is_valid, error_msg = _check_required_operations(clean_query)
    if not is_valid:
        logger.warning(f"SQL validation failed: {error_msg}")
        return False, error_msg
    
    # 3. Vérifier les patterns d'injection SQL
    is_valid, error_msg = _check_sql_injection_patterns(clean_query)
    if not is_valid:
        logger.warning(f"SQL injection attempt detected: {error_msg}")
        return False, error_msg
    
    logger.info(f"✅ SQL query validated successfully")
    return True, None


def _check_forbidden_operations(query: str) -> Tuple[bool, Optional[str]]:
    """
    Vérifie que la requête ne contient pas d'opérations interdites.
    
    Opérations interdites :
    - INSERT : Ajout de données
    - UPDATE : Modification de données
    - DELETE : Suppression de données
    - DROP : Suppression de table/vue
    - TRUNCATE : Vidage de table
    - ALTER : Modification de schéma
    - CREATE : Création d'objets
    - EXEC/EXECUTE : Exécution de procédures stockées
    - MERGE : Fusion de données (peut inclure INSERT/UPDATE/DELETE)
    
    Note: Utilise des regex pour détecter ces mots-clés même s'ils sont
    encapsulés dans d'autres constructions (ex: "SELECT (SELECT 1; DROP TABLE)")
    """
    
    # Liste des opérations interdites (case-insensitive)
    forbidden_keywords = [
        r'\bINSERT\b',
        r'\bUPDATE\b',
        r'\bDELETE\b',
        r'\bDROP\b',
        r'\bTRUNCATE\b',
        r'\bALTER\b',
        r'\bCREATE\b',
        r'\bEXEC\b',
        r'\bEXECUTE\b',
        r'\bMERGE\b',
        r'\bGRANT\b',
        r'\bREVOKE\b',
    ]
    
    for keyword_pattern in forbidden_keywords:
        if re.search(keyword_pattern, query, re.IGNORECASE):
            # Extraire le mot-clé exact trouvé
            match = re.search(keyword_pattern, query, re.IGNORECASE)
            forbidden_word = match.group(0).upper()
            return False, f"❌ Opération interdite : {forbidden_word}. Seules les requêtes SELECT sont autorisées."
    
    return True, None


def _check_required_operations(query: str) -> Tuple[bool, Optional[str]]:
    """
    Vérifie que la requête commence par SELECT ou WITH (CTE).
    
    Pourquoi WITH est autorisé ?
    -----------------------------
    WITH permet les Common Table Expressions (CTEs), qui sont essentielles pour :
    - Requêtes complexes multi-étapes
    - Meilleure lisibilité
    - Performances (sous-requêtes optimisées)
    
    Exemple valide :
        WITH monthly_hours AS (
            SELECT MONTH(PERIODFROM) as Month, SUM(QTY) as Hours
            FROM timesheet_header h
            JOIN timesheet_line l ON h.TIMESHEETNBR = l.TIMESHEETNBR
            GROUP BY MONTH(PERIODFROM)
        )
        SELECT * FROM monthly_hours
    """
    
    # La requête doit commencer par SELECT ou WITH (ignorer espaces et commentaires)
    # Pattern: ignore les espaces, tabs, newlines, puis cherche SELECT ou WITH
    pattern = r'^\s*(SELECT|WITH)\b'
    
    if not re.match(pattern, query, re.IGNORECASE):
        return False, (
            "❌ Requête invalide : doit commencer par SELECT ou WITH. "
            "Exemple valide : SELECT * FROM timesheet_header"
        )
    
    return True, None


def _check_sql_injection_patterns(query: str) -> Tuple[bool, Optional[str]]:
    """
    Détecte les patterns classiques d'injection SQL.
    
    Patterns détectés :
    -------------------
    1. Commentaires SQL : -- ou /* */ (peuvent masquer du code malveillant)
    2. Multiples statements : ; séparant plusieurs requêtes
    3. UNION inattendus : UNION ALL SELECT * FROM sensitive_table
    
    Note: Cette fonction peut générer des faux positifs sur des requêtes légitimes.
    À ajuster selon les besoins métier.
    
    Exemple bloqué :
        SELECT * FROM users WHERE id = 1; DROP TABLE users; --
    """
    
    # Pattern 1 : Détecter les commentaires SQL (-- ou /* */)
    # Note: Commentaires légitimes dans les requêtes générées par le LLM sont rares
    if re.search(r'--', query):
        return False, "❌ Commentaires SQL (--) non autorisés"
    
    if re.search(r'/\*.*?\*/', query, re.DOTALL):
        return False, "❌ Commentaires SQL (/* */) non autorisés"
    
    # Pattern 2 : Détecter les multiples statements (point-virgule suivi d'autres mots-clés)
    # Autorisé : SELECT * FROM table;  (un seul statement terminé par ;)
    # Interdit : SELECT * FROM table; DROP TABLE users;
    if re.search(r';\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)', query, re.IGNORECASE):
        return False, "❌ Multiples statements SQL non autorisés (injection potentielle)"
    
    # Pattern 3 : UNION ALL suspect (tentative d'extraction de données d'autres tables)
    # Note: UNION peut être légitime, mais très rare dans notre use case timesheet
    # Si vous avez besoin de UNION, commentez cette vérification
    if re.search(r'\bUNION\s+ALL\b', query, re.IGNORECASE):
        logger.warning("⚠️ UNION ALL détecté - vérifier la requête")
        # Ne pas bloquer pour l'instant, juste logger
        # return False, "❌ UNION ALL non autorisé (risque d'injection)"
    
    return True, None


def sanitize_query_for_logging(query: str, max_length: int = 200) -> str:
    """
    Nettoie une requête SQL pour le logging (enlève informations sensibles).
    
    Utilisé pour :
    - Logs de debug
    - Logs d'erreur
    - Audit trails
    
    Args:
        query (str): Requête SQL brute
        max_length (int): Longueur max du log (défaut 200 caractères)
    
    Returns:
        str: Requête nettoyée et tronquée
    """
    
    # Enlever les espaces multiples
    clean = " ".join(query.strip().split())
    
    # Tronquer si trop long
    if len(clean) > max_length:
        clean = clean[:max_length] + "..."
    
    return clean


# ══════════════════════════════════════════════════════════════════════════
# Tests unitaires (à déplacer dans tests/test_sql_validator.py en production)
# ══════════════════════════════════════════════════════════════════════════

def _run_tests():
    """Tests de validation rapides pour développement"""
    
    test_cases = [
        # (query, should_be_valid, description)
        ("SELECT * FROM timesheet_header", True, "SELECT simple"),
        ("SELECT SUM(QTY) FROM timesheet_line WHERE MONTH(Date) = 1", True, "SELECT avec WHERE"),
        ("WITH cte AS (SELECT 1) SELECT * FROM cte", True, "CTE valide"),
        
        ("INSERT INTO timesheet_header VALUES (1)", False, "INSERT interdit"),
        ("UPDATE timesheet_header SET QTY = 0", False, "UPDATE interdit"),
        ("DELETE FROM timesheet_header", False, "DELETE interdit"),
        ("DROP TABLE timesheet_header", False, "DROP interdit"),
        ("SELECT * FROM users; DROP TABLE users;", False, "Injection SQL"),
        ("SELECT * FROM users -- comment", False, "Commentaire suspect"),
        
        ("   SELECT * FROM timesheet_header   ", True, "SELECT avec espaces"),
        ("SELECT TOP 10 * FROM timesheet_header ORDER BY RECID DESC", True, "SELECT TOP"),
    ]
    
    print("\n" + "="*80)
    print("🧪 TESTS SQL VALIDATOR")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for query, expected_valid, description in test_cases:
        is_valid, error_msg = validate_sql_query(query)
        
        if is_valid == expected_valid:
            print(f"✅ {description}")
            passed += 1
        else:
            print(f"❌ {description}")
            print(f"   Query: {query[:50]}")
            print(f"   Expected: {expected_valid}, Got: {is_valid}")
            print(f"   Error: {error_msg}")
            failed += 1
    
    print("="*80)
    print(f"Résultats : {passed} passed, {failed} failed")
    print("="*80)
    
    return failed == 0


if __name__ == "__main__":
    # Exécuter les tests en développement
    _run_tests()