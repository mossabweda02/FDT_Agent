"""
check_corrections.py
====================
Vérifie que toutes les corrections sont bien appliquées.

Usage :
    python check_corrections.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


# ══════════════════════════════════════════════════════════════════
# CHECK 1 — Imports
# ══════════════════════════════════════════════════════════════════

def check_imports() -> bool:
    print("\n" + "="*60)
    print("1. VÉRIFICATION DES IMPORTS")
    print("="*60)

    ok = True

    try:
        from core.training_examples import format_examples_for_prompt, get_all_examples
        print("✅ training_examples.py importé")
    except Exception as e:
        print(f"❌ training_examples.py : {e}")
        ok = False

    try:
        # ✅ FIX — importer depuis system_prompt, pas schema_prompt
        from core.prompts.system_prompt import build_system_prompt, SYSTEM_PROMPT
        print("✅ system_prompt.py importé")
    except Exception as e:
        print(f"❌ system_prompt.py : {e}")
        ok = False

    try:
        from core.prompts.tools_definitions import TOOLS_DEFINITIONS
        print(f"✅ tools_definitions.py importé ({len(TOOLS_DEFINITIONS)} outils)")
    except Exception as e:
        print(f"❌ tools_definitions.py : {e}")
        ok = False

    try:
        from core.prompts import build_system_prompt, TOOLS_DEFINITIONS
        print("✅ core/prompts/__init__.py importé")
    except Exception as e:
        print(f"❌ core/prompts/__init__.py : {e}")
        ok = False

    return ok


# ══════════════════════════════════════════════════════════════════
# CHECK 2 — Contenu du prompt
# ══════════════════════════════════════════════════════════════════

def check_prompt_content() -> bool:
    print("\n" + "="*60)
    print("2. VÉRIFICATION DU PROMPT GÉNÉRÉ")
    print("="*60)

    try:
        from core.prompts.system_prompt import build_system_prompt
        prompt = build_system_prompt()

        print(f"✅ Prompt assemblé : {len(prompt):,} caractères")
        print(f"   Lignes : {prompt.count(chr(10)):,}")

        # Afficher la taille de chaque bloc
        for section in prompt.split("# [")[1:]:
            name = section.split("]")[0]
            print(f"   [{name}] → {len(section):,} chars")

        checks = []

        # ── Check A : APPROVALSTATUS = 3 uniquement dans contexte explicite
        # Le problème : "3=Approved" dans la doc du schéma déclenche faussement le check
        # Solution : chercher uniquement "WHERE" + "APPROVALSTATUS = 3" ensemble

        sql_blocks = re.findall(r'```sql(.*?)```', prompt, re.DOTALL)

        # Chercher WHERE h.APPROVALSTATUS = 3 ou WHERE l.APPROVALSTATUS = 3
        where_status3 = [
            b for b in sql_blocks
            if re.search(r'WHERE.*APPROVALSTATUS\s*=\s*3', b, re.DOTALL)
        ]

        if not where_status3:
            print("✅ Aucun WHERE APPROVALSTATUS = 3 dans les requêtes SQL")
            checks.append(True)
        else:
            # Vérifier que chaque occurrence est dans un contexte "approuvées"
            all_explicit = True
            for b in where_status3:
                pos = prompt.find(b)
                context = prompt[max(0, pos - 400): pos + 400].lower()
                if "approuv" not in context and "approved" not in context:
                    print(f"❌ WHERE APPROVALSTATUS = 3 hors contexte 'approuvées'")
                    print(f"   → {b.strip()[:100]}")
                    all_explicit = False

            if all_explicit:
                print(f"✅ WHERE APPROVALSTATUS = 3 uniquement dans contexte"
                    f" 'approuvées' ({len(where_status3)} cas)")
            checks.append(all_explicit)

        # ── Check B : LIMIT absent des vraies requêtes SQL
        # Le problème : LIMIT dans les contre-exemples (-- ❌) déclenche faussement le check
        # Solution : ignorer les lignes qui commencent par -- ou contiennent "❌"

        bad_limit_blocks = []
        for b in sql_blocks:
            for line in b.split('\n'):
                line_clean = line.strip()
                # Ignorer les commentaires et contre-exemples
                if line_clean.startswith('--'):
                    continue
                if '❌' in line_clean:
                    continue
                if re.search(r'\bLIMIT\b', line_clean, re.IGNORECASE):
                    bad_limit_blocks.append(line_clean)

        if not bad_limit_blocks:
            print("✅ Aucun LIMIT dans les vraies requêtes SQL (utilise TOP)")
            checks.append(True)
        else:
            print(f"❌ LIMIT trouvé dans {len(bad_limit_blocks)} ligne(s) SQL réelle(s) :")
            for line in bad_limit_blocks:
                print(f"   → {line[:80]}")
            checks.append(False)

        # ── Check C : Règle APPROVALSTATUS mentionnée
        if ("NE JAMAIS filtrer par APPROVALSTATUS" in prompt
                or "JAMAIS filtrer par APPROVALSTATUS" in prompt):
            print("✅ Règle APPROVALSTATUS présente dans le prompt")
            checks.append(True)
        else:
            print("❌ Règle APPROVALSTATUS absente du prompt")
            checks.append(False)

        # ── Check D : Les 4 blocs présents
        for bloc in ["ROLE", "SCHEMA", "RULES", "EXAMPLES"]:
            if f"# [{bloc}]" in prompt:
                print(f"✅ Bloc [{bloc}] présent")
                checks.append(True)
            else:
                print(f"❌ Bloc [{bloc}] absent")
                checks.append(False)

        return all(checks)

    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False


# ══════════════════════════════════════════════════════════════════
# CHECK 3 — Exemples SQL
# ══════════════════════════════════════════════════════════════════

def check_examples() -> bool:
    print("\n" + "="*60)
    print("3. VÉRIFICATION DES EXEMPLES SQL")
    print("="*60)

    try:
        from core.training_examples import (
            get_all_examples,
            BASIC_EXAMPLES, INTERMEDIATE_EXAMPLES,
            ADVANCED_EXAMPLES, ERROR_CORRECTION_EXAMPLES,
        )

        examples = get_all_examples()
        print(f"✅ {len(examples)} exemples chargés")
        print(f"   Basiques      : {len(BASIC_EXAMPLES)}")
        print(f"   Intermédiaires: {len(INTERMEDIATE_EXAMPLES)}")
        print(f"   Avancés       : {len(ADVANCED_EXAMPLES)}")
        print(f"   Corrections   : {len(ERROR_CORRECTION_EXAMPLES)}")

        checks = []

        # ── Check A : APPROVALSTATUS = 3 dans contextes explicites
        bad_status3 = []
        for ex in examples:
            sql = ex.get("sql_query", "")
            question = ex.get("user_question", "").lower()
            if ("APPROVALSTATUS = 3" in sql
                    and "approuv" not in question
                    and "approved" not in question
                    and "valid" not in question):
                bad_status3.append(ex.get("user_question", "N/A"))

        if not bad_status3:
            print("✅ Tous les APPROVALSTATUS = 3 sont dans contextes explicites")
            checks.append(True)
        else:
            print(f"❌ {len(bad_status3)} exemple(s) avec APPROVALSTATUS = 3 non justifié :")
            for q in bad_status3:
                print(f"   → '{q}'")
            checks.append(False)

        # ── Check B : Pas de LIMIT dans sql_query
        bad_limit = [
            ex.get("user_question", "N/A")
            for ex in examples
            if " LIMIT " in ex.get("sql_query", "").upper()
        ]
        if not bad_limit:
            print("✅ Aucun LIMIT dans les sql_query (utilise TOP)")
            checks.append(True)
        else:
            print(f"❌ {len(bad_limit)} exemple(s) avec LIMIT :")
            for q in bad_limit:
                print(f"   → '{q}'")
            checks.append(False)

        # ── Check C : Chaque exemple a sql_query
        missing_sql = [
            ex.get("user_question", f"exemple_{i}")
            for i, ex in enumerate(examples)
            if "sql_query" not in ex
        ]
        if not missing_sql:
            print(f"✅ Tous les {len(examples)} exemples ont un sql_query")
            checks.append(True)
        else:
            print(f"❌ {len(missing_sql)} exemple(s) sans sql_query :")
            for q in missing_sql:
                print(f"   → '{q}'")
            checks.append(False)

        return all(checks)

    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False


# ══════════════════════════════════════════════════════════════════
# CHECK 4 — Tools
# ══════════════════════════════════════════════════════════════════

def check_tools() -> bool:
    print("\n" + "="*60)
    print("4. VÉRIFICATION DES TOOLS")
    print("="*60)

    try:
        from core.prompts.tools_definitions import TOOLS_DEFINITIONS
        from tools.functions_tools import TOOL_FUNCTIONS

        defined_names  = {t["function"]["name"] for t in TOOLS_DEFINITIONS}
        function_names = set(TOOL_FUNCTIONS.keys())

        print(f"   Tools définis   : {sorted(defined_names)}")
        print(f"   Functions dispo : {sorted(function_names)}")

        checks = []

        # Chaque tool défini doit avoir une fonction
        missing_fn = defined_names - function_names
        if not missing_fn:
            print(f"✅ Tous les {len(defined_names)} tools ont leur fonction")
            checks.append(True)
        else:
            print(f"❌ Tools sans fonction : {missing_fn}")
            checks.append(False)

        # Chaque fonction doit être définie
        missing_def = function_names - defined_names
        if not missing_def:
            print(f"✅ Toutes les fonctions ont leur définition Azure")
            checks.append(True)
        else:
            print(f"⚠️  Fonctions sans définition Azure : {missing_def}")
            checks.append(True)  # Warning seulement

        return all(checks)

    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main() -> int:
    print("\n" + "="*60)
    print("🔍 VÉRIFICATION CORRECTIONS — AGENT FDT")
    print("="*60)

    results = []

    # Check 1 toujours
    imports_ok = check_imports()
    results.append(("Imports", imports_ok))

    if imports_ok:
        results.append(("Prompt",   check_prompt_content()))
        results.append(("Exemples", check_examples()))
        results.append(("Tools",    check_tools()))
    else:
        print("\n⚠️  Imports échoués — corriger avant de continuer.")
        results += [("Prompt", False), ("Exemples", False), ("Tools", False)]

    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ")
    print("="*60)
    for name, passed in results:
        icon = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {icon} — {name}")

    all_passed = all(p for _, p in results)

    print("\n" + "="*60)
    if all_passed:
        print("🎉 TOUTES LES VÉRIFICATIONS PASSÉES")
        print("\n  Prochaine étape :")
        print("    python -m agent.update_agent --force")
        print("    python test_agent.py")
    else:
        print("⚠️  VÉRIFICATIONS ÉCHOUÉES")
        print("\n  Actions :")
        print("    1. Corriger les erreurs ci-dessus")
        print("    2. Relancer : python check_corrections.py")
    print("="*60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())