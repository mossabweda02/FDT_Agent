"""
tests/scrubbing/test_finance_fields.py
=======================================

Catégorie : Finance / Coûts / Budgets / Montants
Couvre : StandardCost, SalePrice, margin, budget, revenue, profit,
         TotalAmount*, notes de frais      
"""

import pytest
from conftest import should_be_scrubbed, should_be_visible


# ════════════════════════════════════════════════════════════════════
# MUST SCRUB — finance
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("key,value", [
    # Colonnes directes DB
    ("StandardCost",             1000.0),
    ("TotalStandardCost",        8000.0),
    ("SalePrice",                1500.0),
    ("TotalSalePrice",           12000.0),
    ("RealCost",                 900.0),
    ("TotalRealCost",            7200.0),
    ("TotalAmountCompanyCur",    3000.0),
    # Agrégats métier
    ("margin",                   0.25),
    ("budget",                   50000),
    ("revenue",                  75000),
    ("profit",                   25000),
    # Notes de frais (acp_expense_card)
    ("expcardamount",            250.0),
    ("totalamount",              1200.0),
    ("totalpaymentamount",       1200.0),
    ("subtotalamount",           1000.0),
    ("tipsamount",               50.0),
    ("paymentexchangerate",      1.08),
    ("exchangeratecompany",      1.0),
    # Budgets projet (prj_budget_*)
    ("consumedbudget",           30000),
    ("contractualbudget",        100000),
    ("CostBudget",               45000),
    ("TotalBudget",              80000),
    ("CUNSUMEDBUDGET",           28000),
    # Revenus annuels CRM
    ("AnnualRevenue",            500000),
])
def test_finance_field_is_scrubbed(key, value):
    assert should_be_scrubbed(key, value), (
        f"FAUX NÉGATIF : '{key}' devrait être scrubbed."
    )


# ════════════════════════════════════════════════════════════════════
# MUST REMAIN VISIBLE — coûts opérationnels safe
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("key,value", [
    # operation_cost est whitelisté explicitement
    ("operation_cost",    0.002),
    ("operation.cost",    0.0015),
    # Métriques LLM token cost (safe)
    ("gen_ai.usage.input_tokens",  120),
    ("gen_ai.usage.output_tokens", 80),
    ("gen_ai.usage.total_tokens",  200),
])
def test_finance_safe_fields_visible(key, value):
    assert should_be_visible(key, value), (
        f"SUR-SCRUBBING : '{key}' devrait rester visible."
    )
