"""Regression tests for bugs fixed in the regime screener and portfolio case study.

Run from the Agents/ directory:
    pip install pytest pandas numpy pydantic
    pytest tests/
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

AGENTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AGENTS_DIR / "regime_screening_workflow"))

from regime_utils import regime_to_criteria  # noqa: E402
from regime_state import State  # noqa: E402
from evaluation_tables import (  # noqa: E402
    EXPANSIONARY_CRITERIA, INFLATIONARY_CRITERIA, STAGFLATIONARY_CRITERIA, RECESSION_CRITERIA,
    EXPANSIONARY_CRITERIA_FINANCIALS, INFLATIONARY_CRITERIA_FINANCIALS,
    STAGFLATIONARY_CRITERIA_FINANCIALS, RECESSION_CRITERIA_FINANCIALS,
)

# The regime names the workflows actually store in state.EconomicRegime
WORKFLOW_REGIMES = ["Expansionary", "Inflationary", "Stagflationary", "Recession"]


# -- Regime criteria lookup -------------------------------------------------

@pytest.mark.parametrize("regime,expected", list(zip(WORKFLOW_REGIMES, [
    EXPANSIONARY_CRITERIA, INFLATIONARY_CRITERIA, STAGFLATIONARY_CRITERIA, RECESSION_CRITERIA,
])), ids=WORKFLOW_REGIMES)
def test_non_financial_criteria_found_for_every_regime(regime, expected):
    assert regime_to_criteria(State(), regime, is_financials=False) == expected


@pytest.mark.parametrize("regime,expected", list(zip(WORKFLOW_REGIMES, [
    EXPANSIONARY_CRITERIA_FINANCIALS, INFLATIONARY_CRITERIA_FINANCIALS,
    STAGFLATIONARY_CRITERIA_FINANCIALS, RECESSION_CRITERIA_FINANCIALS,
])), ids=WORKFLOW_REGIMES)
def test_financial_criteria_found_for_every_regime(regime, expected):
    assert regime_to_criteria(State(), regime, is_financials=True) == expected


def test_unknown_regime_raises_instead_of_returning_empty_criteria():
    with pytest.raises(ValueError):
        regime_to_criteria(State(), "Stagflation", is_financials=False)


def test_workflow_regime_options_match_criteria_keys():
    src = (AGENTS_DIR / "regime_screening_workflow" / "regime_workflows.py").read_text()
    for opts in re.findall(r"regime_opts = (\[.*?\])", src):
        assert json.loads(opts.replace("'", '"')) == WORKFLOW_REGIMES


# -- Outlier table selection ------------------------------------------------

def test_financials_get_financial_outlier_table():
    src = (AGENTS_DIR / "regime_screening_workflow" / "regime_workflows.py").read_text()
    lines = re.findall(r"outlier_table = .*", src)
    assert lines, "outlier_table assignment not found"
    for line in lines:
        assert line.strip() == (
            "outlier_table = OUTLIER_TABLE_FINANCIALS if sector=='Financial Services' else OUTLIER_TABLE"
        )


# -- Payout ratio factor (function lives in the case study notebook) --------

def _load_construct_factor():
    nb_path = AGENTS_DIR / "Agent-Augmented Portfolio Construction - Case Study.ipynb"
    nb = json.loads(nb_path.read_text())
    for cell in nb["cells"]:
        src = "".join(cell["source"])
        if cell["cell_type"] == "code" and src.lstrip().startswith("def construct_factor"):
            ns = {"pd": pd, "np": np}
            exec(src, ns)
            return ns["construct_factor"]
    raise AssertionError("construct_factor cell not found in notebook")


def test_payout_factor_long_basket_holds_highest_eligible_payouts():
    construct_factor = _load_construct_factor()
    # 20 names so the 10% cutoff gives a basket of 2. Listed order deliberately
    # does not match payout order, so taking "the first eligible names" fails.
    payout = {f"T{i:02d}": 0.10 + 0.01 * i for i in range(20)}
    payout.update({"T00": 0.95, "T05": 0.90, "T01": 1.50, "T02": 0.0, "T03": np.nan})
    metrics = pd.DataFrame({"PayoutRatio": payout})

    dates = pd.date_range("2024-01-01", periods=3)
    returns = pd.DataFrame(0.0, index=dates, columns=metrics.index)
    returns[["T00", "T05"]] = 1.0      # intended long basket
    returns[["T02", "T03"]] = -1.0     # short basket (zero / missing payout)

    factor = construct_factor("PayoutRatio", metrics, returns)
    # Long basket mean 1.0 minus short basket mean -1.0
    assert (factor == 2.0).all()


# -- Report save path matches the path the notebook reads from -------------

def test_new_reports_saved_where_they_are_loaded():
    nb = (AGENTS_DIR / "Agent-Augmented Portfolio Construction - Case Study.ipynb").read_text()
    assert "reports/reports/" not in nb
