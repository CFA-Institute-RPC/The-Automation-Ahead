"""Tests for the mandate checks in the portfolio case study notebook.

Run from the Agents/ directory:
    pip install pytest pandas numpy
    pytest tests/test_mandate.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

NOTEBOOK = Path(__file__).resolve().parents[1] / "Agent-Augmented Portfolio Construction - Case Study.ipynb"


def _code_cells():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]


def _load_mandate_helpers():
    for src in _code_cells():
        if "def check_beta_mandate" in src:
            ns = {"np": np, "pd": pd}
            exec(src, ns)
            return ns
    raise AssertionError("mandate helper cell not found in notebook")


# -- Beta mandate -----------------------------------------------------------

def test_mandate_band_is_the_one_in_the_task_scope():
    assert _load_mandate_helpers()["MANDATE_BETA"] == (0.8, 1.2)


@pytest.mark.parametrize("beta", [0.8, 1.0, 1.2, 0.7995])
def test_beta_inside_the_band_is_not_a_breach(beta):
    assert _load_mandate_helpers()["check_beta_mandate"](beta) == []


def test_saved_portfolio_beta_is_reported_as_a_breach():
    # The saved run solved with beta bounds [0.31, 0.71] and returned beta 0.504.
    breaches = _load_mandate_helpers()["check_beta_mandate"](0.504)
    assert len(breaches) == 1
    assert "0.504" in breaches[0]


def test_beta_bounds_are_not_relaxed_unless_asked():
    candidates = _load_mandate_helpers()["beta_bound_candidates"]
    beta_vec = np.array([0.06, 0.5, 1.7])
    assert candidates(beta_vec, allow_relaxation=False) == [(0.8, 1.2)]


def test_relaxation_is_opt_in_and_starts_from_the_mandate():
    candidates = _load_mandate_helpers()["beta_bound_candidates"]
    bounds = candidates(np.array([0.06, 0.5, 1.7]), allow_relaxation=True)
    assert bounds[0] == (0.8, 1.2)
    assert len(bounds) > 1


def test_optimizer_cell_does_not_relax_by_default():
    optimizer = [src for src in _code_cells() if "build_and_solve" in src]
    assert len(optimizer) == 1
    assert "ALLOW_BETA_RELAXATION = False" in optimizer[0]
    assert "beta_bound_candidates(beta_vec, ALLOW_BETA_RELAXATION)" in optimizer[0]


# -- Final sector allocation --------------------------------------------------

def test_final_sector_allocation_sums_weights_not_positions():
    cells = [src for src in _code_cells() if "weight_opt_port" in src]
    assert len(cells) == 1
    out = pd.DataFrame({
        "Ticker": ["A", "B", "C"],
        "Weight": [0.95, 0.04, 0.01],
        "GICS Sector": ["Energy", "Utilities", "Utilities"],
    })
    sp = pd.DataFrame({"weight_SPY": [0.04, 0.06]}, index=pd.Index(["Energy", "Utilities"], name="GICS Sector"))
    table = eval(cells[0].strip(), {"out": out, "SP_sector_weights": sp})
    assert table.loc["Energy", "weight_opt_port"] == pytest.approx(0.95)
    assert table.loc["Utilities", "weight_opt_port"] == pytest.approx(0.05)
