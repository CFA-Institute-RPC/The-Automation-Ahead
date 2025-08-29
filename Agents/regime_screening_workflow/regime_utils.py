import pandas as pd
from typing import Tuple
from regime_state import Metrics, State
from evaluation_tables import (
    EXPANSIONARY_CRITERIA_FINANCIALS,
    INFLATIONARY_CRITERIA_FINANCIALS,
    STAGFLATIONARY_CRITERIA_FINANCIALS,
    RECESSION_CRITERIA_FINANCIALS
)
from metrics import *

def to_df(x):
        if x is None:
            return pd.DataFrame()
        if isinstance(x, pd.DataFrame):
            return x
        return pd.DataFrame(x)

def get_financials(state) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Returns: ann_inc, qtr_inc, ann_bs, qtr_bs as DataFrames extracted from the
    state.FinancialData list of FinData models.
    """
    ticker = state.Ticker
    financials = state.FinancialData

    if financials is None:
        if not state.FinancialData:
            raise KeyError(f"state.FinancialData is empty; no financial record available for {ticker}")

    ann_inc = to_df(financials.Ann_IncomeStatement)
    qtr_inc = to_df(financials.Qtr_IncomeStatement)
    ann_bs  = to_df(financials.Ann_BalanceSheet)
    qtr_bs  = to_df(financials.Qtr_BalanceSheet)

    return ann_inc, qtr_inc, ann_bs, qtr_bs

def regime_to_criteria(state: State, regime: str, is_financials:bool) -> str:
    if is_financials:
        mapping = mapping = {
        "Expansion": EXPANSIONARY_CRITERIA_FINANCIALS,
        "Inflation": INFLATIONARY_CRITERIA_FINANCIALS,
        "Stagflation": STAGFLATIONARY_CRITERIA_FINANCIALS,
        "Recession": RECESSION_CRITERIA_FINANCIALS,
        }
    else:
        mapping = {
            "Expansion": state.ScreeningCriteria.Expansionary,
            "Inflation": state.ScreeningCriteria.Inflationary,
            "Stagflation": state.ScreeningCriteria.Stagflationary,
            "Recession": state.ScreeningCriteria.Recession,
        }
    return mapping.get(regime, "")

async def save_metrics(ctx, metrics_dict):
    """Put metrics into state['MetricData'].MetricData (append/update)."""
    async with ctx.store.edit_state() as st:
        if "MetricData" not in st or st.MetricData is None:
            st.MetricData = Metrics()
        base = st.MetricData.MetricData or {}
        base.update(metrics_dict)
        st.MetricData.MetricData = base

def calculate_financials_metrics(regime, ann_inc, ann_bs, qtr_inc):
    if regime == 'Expansionary':
        pp = ppnr(ann_inc)
        ef = efficiency_ratio(ann_inc)
        rr = roe_roa(ann_inc, ann_bs)  # or roe_roa_avg(ann_inc, ann_bs)

        metrics_expansion_fin = {
            "PPNR Growth (YoY)": pp["PPNR Growth YoY (Latest)"],
            "Efficiency Ratio": ef["Efficiency Ratio (Latest)"],
            "ROE": rr["ROE (Latest)"],
            "supplemental info": {
                "PPNR": {k: str(v) for k, v in pp.items() if k != "PPNR Growth YoY (Latest)"},
                "Efficiency Ratio": {k: str(v) for k, v in ef.items() if k != "Efficiency Ratio (Latest)"},
                "ROE/ROA": {k: str(v) for k, v in rr.items() if k != "ROE (Latest)"},
            },
        }
        return metrics_expansion_fin

    elif regime == "Inflationary":
        ng = nii_growth_yoy(ann_inc)
        ef = efficiency_ratio(ann_inc)
        ea = equity_to_assets(ann_bs)

        metrics_inflation_fin = {
            "NII Growth (YoY)": ng["NII Growth YoY (Latest)"],
            "Efficiency Ratio Δ (YoY, bps)": ef["Efficiency Ratio Δ YoY (bps) Latest"],
            "Equity / Assets": ea["Equity / Assets (Latest)"],
            "supplemental info": {
                "NII": {k: str(v) for k, v in ng.items() if k != "NII Growth YoY (Latest)"},
                "Efficiency Ratio": {k: str(v) for k, v in ef.items() if k != "Efficiency Ratio Δ YoY (bps) Latest"},
                "Equity / Assets": {k: str(v) for k, v in ea.items() if k != "Equity / Assets (Latest)"},
            },
        }
        return metrics_inflation_fin

    elif regime == "Stagflationary":
        pgv = ppnr_growth_volatility_qtr(qtr_inc)   # <-- quarterly
        rr  = roe_roa(ann_inc, ann_bs)              # or roe_roa_avg(ann_inc, ann_bs)
        ea  = equity_to_assets(ann_bs)

        metrics_stagflation_fin = {
            "PPNR Growth Volatility (stdev, quarterly)": pgv["PPNR Growth Volatility (stdev, quarterly)"],
            "ROA": rr["ROA (Latest)"],
            "Equity / Assets": ea["Equity / Assets (Latest)"],
            "supplemental info": {
                "PPNR Growth": {k: str(v) for k, v in pgv.items() if k != "PPNR Growth Volatility (stdev, quarterly)"},
                "ROE/ROA": {k: str(v) for k, v in rr.items() if k != "ROA (Latest)"},
                "Equity / Assets": {k: str(v) for k, v in ea.items() if k != "Equity / Assets (Latest)"},
            },
        }
        return metrics_stagflation_fin

    elif regime == "Recession":
        ea = equity_to_assets(ann_bs)
        ef = efficiency_ratio(ann_inc)
        pa = ppnr_to_assets(ann_inc, ann_bs)  # or ppnr_to_assets_avg(ann_inc, ann_bs)

        metrics_recession_fin = {
            "Equity / Assets": ea["Equity / Assets (Latest)"],
            "Efficiency Ratio": ef["Efficiency Ratio (Latest)"],
            "PPNR / Assets": pa["PPNR / Assets (Latest)"],
            "supplemental info": {
                "Equity / Assets": {k: str(v) for k, v in ea.items() if k != "Equity / Assets (Latest)"},
                "Efficiency Ratio": {k: str(v) for k, v in ef.items() if k != "Efficiency Ratio (Latest)"},
                "PPNR / Assets": {k: str(v) for k, v in pa.items() if k != "PPNR / Assets (Latest)"},
            },
        }
        return metrics_recession_fin

    else:
        print("Invalid regime. Please try again.")
        return None