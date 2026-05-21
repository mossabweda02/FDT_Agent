"""
tests/scrubbing/test_scrubbing_score.py
========================================
Score global de validation du scrubbing.
Produit un rapport de type :

  ✅ SCRUBBED   : 42/43  (97.7%)
  ✅ VISIBLE    : 28/28  (100%)
  ⚠  FALSE NEG  : 1  → salary
  ⚠  FALSE POS  : 2  → service.name, scrubbing_group
  📊 ACCURACY   : 95.8%

Ce fichier ne remplace pas les tests unitaires — il agrège les résultats.

"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import pytest
from conftest import should_be_scrubbed, should_be_visible


# ════════════════════════════════════════════════════════════════════
# Données de référence complètes
# ════════════════════════════════════════════════════════════════════

MUST_SCRUB: list[tuple[str, Any]] = [
    # RH
    ("employee_name",           "Mohamed Ben Ali"),
    ("resource_name",           "Mohamed Ben Ali"),
    ("PERSONNELNUMBER",         "EMP-458921"),
    ("RESOURCEID",              "RES-2936"),
    ("WORKER",                  "123456"),
    ("WORKERRESPONSIBLE",       "ref"),
    ("WORKERRESPONSIBLEFINANCIAL", "ref"),
    ("WORKERRESPONSIBLESALES",  "ref"),
    ("RESOURCECOMPANYID",       "COMP-01"),
    ("FirstName",               "Mohamed"),
    ("NAME",                    "Mohamed Ben Ali"),
    # Finance
    ("StandardCost",            1000.0),
    ("TotalStandardCost",       8000.0),
    ("SalePrice",               1500.0),
    ("TotalSalePrice",          12000.0),
    ("RealCost",                900.0),
    ("TotalRealCost",           7200.0),
    ("TotalAmountCompanyCur",   3000.0),
    ("margin",                  0.25),
    ("budget",                  50000),
    ("revenue",                 75000),
    ("profit",                  25000),
    ("AnnualRevenue",           500000),
    ("TotalBudget",             80000),
    # Notes
    ("INTERNALNOTE",            "texte libre"),
    ("EXTERNALNOTE",            "texte libre"),
    ("description",             "texte sensible"),
    ("referenceNumber",         "REF-001"),
    # Secrets
    ("connection_string",       "Driver={ODBC}"),
    ("api_key",                 "sk-xxx"),
    ("client_secret",           "secret"),
    ("token",                   "Bearer xyz"),
    ("synapse_key",             "key"),
    # SQL / LLM
    ("db.statement",            "SELECT * FROM ga_resource"),
    ("sql",                     "SELECT salary FROM ga_resource"),
    ("prompt",                  "Quel est le salaire ?"),
    ("completion",              "Le salaire est 5000"),
    ("response",                "Sensitive content"),
    ("question",                "Question brute utilisateur"),
]

MUST_BE_VISIBLE: list[tuple[str, Any]] = [
    ("model_name",              "gpt-4.1-nano"),
    ("agent_name",              "fdt-agent"),
    ("table_name",              "timesheet_line"),
    ("operation_cost",          0.002),
    ("row_count",               25),
    ("question_hash",           "abc123"),
    ("question_preview",        "Combien d'heures a travaillé [PERSON] ?"),
    ("question_category",       "heures"),
    ("question_pii_detected",   True),
    ("gen_ai.request.model",    "gpt-4.1-nano"),
    ("gen_ai.usage.input_tokens",  120),
    ("gen_ai.usage.output_tokens", 80),
    ("gen_ai.usage.total_tokens",  200),
    ("http.request.method",     "GET"),
    ("http.response.status_code", 200),
    ("http.route",              "/ask"),
    ("db.system",               "mssql"),
    ("db.operation",            "SELECT"),
    ("APPROVALSTATUS",          1),
    ("row_count",               42),
]

# Connus comme non-patchés (xfail attendus)
KNOWN_FALSE_NEGATIVES = {"salary", "salaire", "payroll"}
KNOWN_FALSE_POSITIVES = {"service.name", "scrubbing_group"}


# ════════════════════════════════════════════════════════════════════
# Score
# ════════════════════════════════════════════════════════════════════

@dataclass
class ScrubbingReport:
    scrubbed_ok:    list[str] = field(default_factory=list)
    scrubbed_fail:  list[str] = field(default_factory=list)  # faux négatifs
    visible_ok:     list[str] = field(default_factory=list)
    visible_fail:   list[str] = field(default_factory=list)  # faux positifs

    @property
    def total_checks(self) -> int:
        return (len(self.scrubbed_ok) + len(self.scrubbed_fail)
                + len(self.visible_ok) + len(self.visible_fail))

    @property
    def correct(self) -> int:
        return len(self.scrubbed_ok) + len(self.visible_ok)

    @property
    def accuracy(self) -> float:
        if self.total_checks == 0:
            return 0.0
        return self.correct / self.total_checks * 100

    @property
    def false_negatives(self) -> list[str]:
        return [k for k in self.scrubbed_fail if k not in KNOWN_FALSE_NEGATIVES]

    @property
    def false_positives(self) -> list[str]:
        return [k for k in self.visible_fail if k not in KNOWN_FALSE_POSITIVES]

    @property
    def critical_leaks(self) -> list[str]:
        return [k for k in self.scrubbed_fail
                if k not in KNOWN_FALSE_NEGATIVES]

    def print_report(self) -> None:
        print("\n" + "═" * 60)
        print("  SCRUBBING VALIDATION REPORT — FDT Agent")
        print("═" * 60)
        s_ok = len(self.scrubbed_ok)
        s_tot = s_ok + len(self.scrubbed_fail)
        v_ok = len(self.visible_ok)
        v_tot = v_ok + len(self.visible_fail)
        icon_s = "✅" if s_ok == s_tot else "❌"
        icon_v = "✅" if v_ok == v_tot else "⚠ "
        icon_a = "✅" if self.accuracy >= 90 else "❌"
        print(f"  {icon_s} SCRUBBED   : {s_ok}/{s_tot}")
        print(f"  {icon_v} VISIBLE    : {v_ok}/{v_tot}")
        if self.scrubbed_fail:
            print(f"  ❌ FALSE NEG  : {len(self.scrubbed_fail)}")
            for k in self.scrubbed_fail:
                tag = " [known]" if k in KNOWN_FALSE_NEGATIVES else " ← CRITIQUE"
                print(f"       • {k}{tag}")
        if self.visible_fail:
            print(f"  ⚠  FALSE POS  : {len(self.visible_fail)}")
            for k in self.visible_fail:
                tag = " [known]" if k in KNOWN_FALSE_POSITIVES else " ← BLOQUANT"
                print(f"       • {k}{tag}")
        print(f"  {icon_a} ACCURACY   : {self.accuracy:.1f}%")
        print("═" * 60)
        if self.critical_leaks:
            print("  🚨 FUITES CRITIQUES (non connues) :")
            for k in self.critical_leaks:
                print(f"       • {k}")
        status = "✅ PRÊT" if (
            self.accuracy >= 90
            and len(self.critical_leaks) == 0
        ) else "❌ NON PRÊT"
        print(f"  STATUT GLOBAL : {status}")
        print("═" * 60 + "\n")


def test_global_scrubbing_score(capsys):
    report = ScrubbingReport()

    for key, value in MUST_SCRUB:
        if should_be_scrubbed(key, value):
            report.scrubbed_ok.append(key)
        else:
            report.scrubbed_fail.append(key)

    for key, value in MUST_BE_VISIBLE:
        if should_be_visible(key, value):
            report.visible_ok.append(key)
        else:
            report.visible_fail.append(key)

    report.print_report()

    # Assertions de validation finale
    assert len(report.critical_leaks) == 0, (
        f"FUITES CRITIQUES détectées : {report.critical_leaks}"
    )
    assert len(report.false_positives) == 0, (
        f"FAUX POSITIFS non connus détectés : {report.false_positives}"
    )
    assert report.accuracy >= 90.0, (
        f"Accuracy {report.accuracy:.1f}% < 90% — scrubbing insuffisant."
    )
