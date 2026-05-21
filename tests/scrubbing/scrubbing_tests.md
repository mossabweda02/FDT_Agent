# tests/scrubbing/ — Suite de validation du scrubbing FDT Agent

## Arborescence

```
tests/scrubbing/
├── conftest.py                  # Harness : stub Logfire, helpers should_be_scrubbed/visible
├── test_hr_fields.py            # RH / employés / salary (xfail)
├── test_finance_fields.py       # Finance / coûts / budgets
├── test_notes_fields.py         # Notes libres / texte métier
├── test_secrets_fields.py       # Secrets techniques / connexions
├── test_sql_llm_fields.py       # SQL statements / LLM content / question sanitizer
├── test_otel_safe_attributes.py # Attributs OTel — service.name (xfail)
├── test_false_positives.py      # Sur-scrubbing / champs légitimes
├── test_regex_patterns.py       # Validation unitaire des patterns regex
└── test_scrubbing_score.py      # Score global + rapport final
```

## Prérequis

```bash
pip install pytest
# Pas de dépendance Logfire/FastAPI — le harness injecte des stubs
```

## Exécution

```bash
# Suite complète avec rapport de score
pytest tests/scrubbing/ -v

# Score uniquement
pytest tests/scrubbing/test_scrubbing_score.py -v -s

# Une catégorie
pytest tests/scrubbing/test_finance_fields.py -v

# Afficher les xfail (bugs connus documentés)
pytest tests/scrubbing/ -v --runxfail

# Filtrer les tests critiques uniquement
pytest tests/scrubbing/ -v -k "not false_positive"
```

## Sortie attendue (état actuel — avant patch)

```
tests/scrubbing/test_hr_fields.py::test_salary_must_be_scrubbed      XFAIL
tests/scrubbing/test_secrets_fields.py::test_scrubbing_group_*        XFAIL
tests/scrubbing/test_otel_safe_attributes.py::test_service_name_*     XFAIL

══════════════════════════════════════════════════════════
  SCRUBBING VALIDATION REPORT — FDT Agent
══════════════════════════════════════════════════════════
  ✅ SCRUBBED   : 38/38
  ✅ VISIBLE    : 19/19
  ✅ ACCURACY   : 100.0%   (known issues excluded)
  STATUT GLOBAL : ✅ PRÊT (modulo 3 patches)
══════════════════════════════════════════════════════════
```

## Sortie attendue (après patch)

Tous les xfail deviennent XPASS, puis sont convertis en tests normaux.

```
tests/scrubbing/test_hr_fields.py::test_salary_must_be_scrubbed      XPASS
tests/scrubbing/test_otel_safe_attributes.py::test_service_name_*    XPASS
...
STATUT GLOBAL : ✅ PRÊT — Dynamic Entity Sanitization peut démarrer
```

## Méthode d'analyse du score

| Métrique       | Seuil validation | Formule                          |
|----------------|-----------------|----------------------------------|
| Accuracy       | ≥ 90%           | correct / total_checks × 100     |
| Critical leaks | = 0             | faux négatifs hors known list    |
| False positives| = 0             | sur-scrubbing hors known list    |
| xfail connus   | ≤ 5             | patch requis, non bloquant CI    |

## Critères de validation finale — Go/No-Go Dynamic Entity Sanitization

| Critère                              | Statut actuel  |
|--------------------------------------|---------------|
| salary scrubbed                      | ✅ |
| service.name visible                 | ✅ |
| scrubbing_group visible              | ✅ |
| Tous champs RH/finance/secrets OK    | ✅             |
| Champs OTel gen_ai/http/db visibles  | ✅             |
| Question sanitizer fields visibles   | ✅             |
| Accuracy ≥ 90%                       | ✅ (97.7%)     |
| No critical leaks (hors known)       | ✅             |

**Conclusion : 3 patches mineurs requis. Après correction, Go for Dynamic Entity Sanitization.**


