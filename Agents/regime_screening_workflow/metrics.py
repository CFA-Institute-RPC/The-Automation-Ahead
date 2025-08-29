import numpy as np
import pandas as pd

# -- Helper ---------------------------------------------------------
def safe_get(df, field_name):
    """
    Safely get a field from DataFrame. Returns NaN series if field doesn't exist.
    """
    if field_name in df.index:
        return df.loc[field_name, :]
    else:
        print(f"Warning: '{field_name}' not found in data")
        return pd.Series(np.nan, index=df.columns, name=field_name)

# -- Non-Financials Metrics -----------------------------------------

def revenue_growth(ann_incstm, qtr_incstm):
    ann_rev = safe_get(ann_incstm, 'TotalRevenue')
    qtr_rev = safe_get(qtr_incstm, 'TotalRevenue')
    ann_rev_g = (ann_rev.iloc[0] - ann_rev.iloc[1]) / ann_rev.iloc[1]
    qtr_rev_g = (qtr_rev.iloc[0] - qtr_rev.iloc[1]) / qtr_rev.iloc[1]
    return {
        "Annual Revenue": ann_rev,
        "Quarter Revenue": qtr_rev,
        "Annual Revenue Growth": ann_rev_g,
        "Quarter Revenue Growth": qtr_rev_g,
    }

def ebitda_margin(ann_incstm, qtr_incstm):
    ann_rev = safe_get(ann_incstm, 'TotalRevenue')
    ann_ebitda = safe_get(ann_incstm, 'EBITDA')
    qtr_rev = safe_get(qtr_incstm, 'TotalRevenue')
    qtr_ebitda = safe_get(qtr_incstm, 'EBITDA')
    ann_margin = ann_ebitda / ann_rev
    qtr_margin = qtr_ebitda / qtr_rev
    return {
        "Annual EBITDA": ann_ebitda,
        "Annual Revenue": ann_rev,
        "Annual EBITDA Margin": ann_margin,
        "Quarter EBITDA": qtr_ebitda,
        "Quarter Revenue": qtr_rev,
        "Quarter EBITDA Margin": qtr_margin,
        "Annual EBITDA Margin (Latest)": ann_margin.iloc[0],
        "Quarter EBITDA Margin (Latest)": qtr_margin.iloc[0],
    }

def net_debt_to_ebitda(ann_incstm, ann_bs):
    net_debt_series = safe_get(ann_bs, 'NetDebt')
    ebitda_series   = safe_get(ann_incstm, 'EBITDA')
    net_debt_latest = net_debt_series.iloc[0]
    ebitda_latest   = ebitda_series.iloc[0]
    ratio_latest = net_debt_latest / ebitda_latest
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio_series = net_debt_series / ebitda_series
    return {
        "Annual Net Debt": net_debt_series,
        "Annual EBITDA": ebitda_series,
        "Annual Net Debt / EBITDA (series)": ratio_series,
        "Net Debt / EBITDA (Latest)": ratio_latest,
    }

def ebitda_margin_volatility(ann_incstm):
    ann_rev = safe_get(ann_incstm, 'TotalRevenue')
    ann_ebitda = safe_get(ann_incstm, 'EBITDA')
    ann_gm = ann_ebitda / ann_rev
    ann_gm_vol = ann_gm.sort_index().std()
    return {
        "Annual EBITDA Margin (series)": ann_gm,
        "Annual EBITDA Margin Volatility (stdev)": ann_gm_vol,
    }

def gross_margin_trend_bps(ann_incstm, qtr_incstm):
    ann_rev = safe_get(ann_incstm, 'TotalRevenue')
    ann_cogs = safe_get(ann_incstm, 'CostOfRevenue')
    ann_gm = ((ann_rev - ann_cogs) / ann_rev).sort_index()
    ann_trend = ann_gm - ann_gm.shift(1)
    ann_trend_avg_bps = ann_trend.mean() * 10000.0
    qtr_rev = safe_get(qtr_incstm, 'TotalRevenue')
    qtr_cogs = safe_get(qtr_incstm, 'CostOfRevenue')
    qtr_gm = ((qtr_rev - qtr_cogs) / qtr_rev).sort_index()
    qtr_trend = qtr_gm - qtr_gm.shift(1)
    qtr_trend_avg_bps = qtr_trend.mean() * 10000.0
    return {
        "Annual Gross Margin (series)": ann_gm,
        "Annual GM Trend (YoY, fraction)": ann_trend,
        "Annual GM Trend Avg (bps)": ann_trend_avg_bps,
        "Quarter Gross Margin (series)": qtr_gm,
        "Quarter GM Trend (QoQ, fraction)": qtr_trend,
        "Quarter GM Trend Avg (bps)": qtr_trend_avg_bps,
    }

def inventory_turnover(ann_incstm, ann_bs):
    cogs = safe_get(ann_incstm, 'CostOfRevenue')
    inv  = safe_get(ann_bs, 'Inventory')
    if inv.dropna().shape[0] >= 2:
        avg_inv_latest_two = inv.iloc[:2].mean()
    else:
        avg_inv_latest_two = inv.iloc[0]
    turnover_latest = (cogs.iloc[0] / avg_inv_latest_two) if avg_inv_latest_two != 0 else np.nan
    avg_inv_series = inv.rolling(2, min_periods=1, axis=0).mean()
    with np.errstate(divide='ignore', invalid='ignore'):
        turnover_series = cogs / avg_inv_series
    return {
        "Annual COGS": cogs,
        "Annual Inventory": inv,
        "Average Inventory (latest two)": avg_inv_latest_two,
        "Inventory Turnover (series)": turnover_series,
        "Inventory Turnover (Latest)": turnover_latest,
    }

def interest_coverage(ann_incstm):
    ebit    = safe_get(ann_incstm, 'EBIT')
    int_exp = safe_get(ann_incstm, 'InterestExpense')
    denom_latest = abs(int_exp.iloc[0])
    coverage_latest = (ebit.iloc[0] / denom_latest) if denom_latest != 0 else float('inf')
    with np.errstate(divide='ignore', invalid='ignore'):
        coverage_series = ebit / abs(int_exp)
    return {
        "Annual EBIT": ebit,
        "Annual Interest Expense": int_exp,
        "Interest Coverage (series)": coverage_series,
        "Interest Coverage (Latest)": coverage_latest,
    }

def cash_to_debt(ann_bs):
    cash = safe_get(ann_bs, 'CashAndCashEquivalents')
    sti  = safe_get(ann_bs, 'ShortTermInvestments')
    total_debt = safe_get(ann_bs, 'TotalDebt')
    cash_sti = cash + sti
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio_series = cash_sti / total_debt
    den_latest = total_debt.iloc[0]
    ratio_latest = (cash_sti.iloc[0] / den_latest) if den_latest != 0 else float('inf')
    return {
        "Annual Cash": cash,
        "Annual Short Term Investments": sti,
        "Annual Total Debt": total_debt,
        "Cash+STI (series)": cash_sti,
        "Cash+STI / Total Debt (series)": ratio_series,
        "Cash+STI / Total Debt (Latest)": ratio_latest,
    }

def dso_change_yoy(ann_incstm, ann_bs, days=365):
    ar  = safe_get(ann_bs, 'AccountsReceivable')
    rev = safe_get(ann_incstm, 'TotalRevenue')
    dso_series = (ar / rev.replace(0, np.nan)) * days
    dso_series = dso_series.dropna()
    if dso_series.shape[0] < 2:
        delta_latest = np.nan
    else:
        delta_latest = dso_series.iloc[0] - dso_series.iloc[1]
    return {
        "Annual Accounts Receivable": ar,
        "Annual Revenue": rev,
        "DSO (series, days)": dso_series,
        "DSO Change (YoY, days) Latest": delta_latest,
    }

# -- Financials Metrics ---------------------------------------------

def ppnr(ann_incstm):
    nii   = safe_get(ann_incstm, 'NetInterestIncome')
    total_rev = safe_get(ann_incstm, 'TotalRevenue')
    nonint_income = total_rev - nii
    sga   = safe_get(ann_incstm, 'SellingGeneralAndAdministration')
    other = safe_get(ann_incstm, 'OtherNonInterestExpense')
    nonint_expense = sga + other
    ppnr_series = (nii + nonint_income - nonint_expense).sort_index(ascending=False)
    ppnr_latest = ppnr_series.iloc[0]
    ppnr_growth = (ppnr_series.iloc[0] - ppnr_series.iloc[1]) / ppnr_series.iloc[1]
    return {
        "PPNR (series)": ppnr_series,
        "PPNR (Latest)": ppnr_latest,
        "PPNR Growth YoY (Latest)": ppnr_growth,
    }

def efficiency_ratio(ann_incstm):
    nii   = safe_get(ann_incstm, 'NetInterestIncome')
    total_rev = safe_get(ann_incstm, 'TotalRevenue')
    nonint_income = total_rev - nii
    sga   = safe_get(ann_incstm, 'SellingGeneralAndAdministration')
    other = safe_get(ann_incstm, 'OtherNonInterestExpense')
    nonint_expense = sga + other
    eff_series = (nonint_expense / (nii + nonint_income)).sort_index(ascending=False)
    eff_latest = eff_series.iloc[0]
    eff_delta  = (eff_series.iloc[0] - eff_series.iloc[1]) * 10000.0
    return {
        "Efficiency Ratio (series)": eff_series,
        "Efficiency Ratio (Latest)": eff_latest,
        "Efficiency Ratio Δ YoY (bps) Latest": eff_delta,
    }

def nii_growth_yoy(ann_incstm):
    nii = safe_get(ann_incstm, 'NetInterestIncome').sort_index(ascending=False)
    nii_growth = (nii.iloc[0] - nii.iloc[1]) / nii.iloc[1]
    return {
        "Net Interest Income (series)": nii,
        "NII Growth YoY (Latest)": nii_growth,
    }

def ppnr_growth_volatility_qtr(qtr_incstm):
    nii   = safe_get(qtr_incstm, 'NetInterestIncome')
    total_rev = safe_get(qtr_incstm, 'TotalRevenue')
    nonint_income = total_rev - nii
    sga   = safe_get(qtr_incstm, 'SellingGeneralAndAdministration')
    other = safe_get(qtr_incstm, 'OtherNonInterestExpense')
    nonint_expense = sga + other
    ppnr_series = (nii + nonint_income - nonint_expense).sort_index()
    ppnr_growth = ppnr_series / ppnr_series.shift(1) - 1.0
    vol = ppnr_growth.std()
    return {
        "Quarterly PPNR": ppnr_series,
        "Quarterly PPNR Growth": ppnr_growth,
        "PPNR Growth Volatility (stdev, quarterly)": vol,
    }

def roe_roa(ann_incstm, ann_bs):
    net_inc = safe_get(ann_incstm, 'NetIncome')
    equity  = safe_get(ann_bs, 'TotalEquityGrossMinorityInterest')
    assets  = safe_get(ann_bs, 'TotalAssets')
    roe_series = (net_inc / equity).sort_index(ascending=False)
    roa_series = (net_inc / assets).sort_index(ascending=False)
    return {
        "ROE (series)": roe_series,
        "ROE (Latest)": roe_series.iloc[0],
        "ROA (series)": roa_series,
        "ROA (Latest)": roa_series.iloc[0],
    }

def equity_to_assets(ann_bs):
    equity = safe_get(ann_bs, 'TotalEquityGrossMinorityInterest')
    assets = safe_get(ann_bs, 'TotalAssets')
    ea_series = (equity / assets).sort_index(ascending=False)
    return {
        "Equity / Assets (series)": ea_series,
        "Equity / Assets (Latest)": ea_series.iloc[0],
    }

def ppnr_to_assets(ann_incstm, ann_bs):
    pp_series = ppnr(ann_incstm)["PPNR (series)"]
    assets = safe_get(ann_bs, 'TotalAssets')
    pa_series = (pp_series / assets).sort_index(ascending=False)
    return {
        "PPNR / Assets (series)": pa_series,
        "PPNR / Assets (Latest)": pa_series.iloc[0],
    }