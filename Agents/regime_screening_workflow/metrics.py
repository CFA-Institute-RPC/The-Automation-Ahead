import numpy as np
import pandas as pd

# -- Helpers --------------------------------------------------------

def _get_row(df, *keys):
    """Try each key in order; return NaN series if none found."""
    for k in keys:
        if k in df.index:
            return df.loc[k, :]
    cols = df.columns if hasattr(df, 'columns') else []
    return pd.Series(np.nan, index=cols, name=keys[0])

def _iloc0(series):
    """Safe iloc[0]; NaN if empty."""
    s = series.dropna()
    return s.iloc[0] if len(s) >= 1 else np.nan

def _iloc1(series):
    """Safe iloc[1]; NaN if fewer than 2 points."""
    s = series.dropna()
    return s.iloc[1] if len(s) >= 2 else np.nan

def _yoy(series):
    """Year-over-year growth; NaN if < 2 non-null points or zero denominator."""
    s = series.dropna()
    if len(s) < 2 or s.iloc[1] == 0:
        return np.nan
    return (s.iloc[0] - s.iloc[1]) / s.iloc[1]

# -- Non-Financials Metrics -----------------------------------------

def revenue_growth(ann_incstm, qtr_incstm):
    ann_rev = _get_row(ann_incstm, 'TotalRevenue', 'Revenue', 'OperatingRevenue')
    qtr_rev = _get_row(qtr_incstm, 'TotalRevenue', 'Revenue', 'OperatingRevenue')
    return {
        "Annual Revenue": ann_rev,
        "Quarter Revenue": qtr_rev,
        "Annual Revenue Growth": _yoy(ann_rev),
        "Quarter Revenue Growth": _yoy(qtr_rev),
    }

def ebitda_margin(ann_incstm, qtr_incstm):
    ann_rev    = _get_row(ann_incstm, 'TotalRevenue', 'Revenue', 'OperatingRevenue')
    ann_ebitda = _get_row(ann_incstm, 'EBITDA')
    qtr_rev    = _get_row(qtr_incstm, 'TotalRevenue', 'Revenue', 'OperatingRevenue')
    qtr_ebitda = _get_row(qtr_incstm, 'EBITDA')
    ann_margin = ann_ebitda / ann_rev
    qtr_margin = qtr_ebitda / qtr_rev
    return {
        "Annual EBITDA": ann_ebitda,
        "Annual Revenue": ann_rev,
        "Annual EBITDA Margin": ann_margin,
        "Quarter EBITDA": qtr_ebitda,
        "Quarter Revenue": qtr_rev,
        "Quarter EBITDA Margin": qtr_margin,
        "Annual EBITDA Margin (Latest)": _iloc0(ann_margin),
        "Quarter EBITDA Margin (Latest)": _iloc0(qtr_margin),
    }

def net_debt_to_ebitda(ann_incstm, ann_bs):
    net_debt_series = _get_row(ann_bs, 'NetDebt')
    ebitda_series   = _get_row(ann_incstm, 'EBITDA')
    net_debt_latest = _iloc0(net_debt_series)
    ebitda_latest   = _iloc0(ebitda_series)
    ratio_latest = (net_debt_latest / ebitda_latest) if ebitda_latest and ebitda_latest != 0 else np.nan
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio_series = net_debt_series / ebitda_series
    return {
        "Annual Net Debt": net_debt_series,
        "Annual EBITDA": ebitda_series,
        "Annual Net Debt / EBITDA (series)": ratio_series,
        "Net Debt / EBITDA (Latest)": ratio_latest,
    }

def ebitda_margin_volatility(ann_incstm):
    ann_rev    = _get_row(ann_incstm, 'TotalRevenue', 'Revenue', 'OperatingRevenue')
    ann_ebitda = _get_row(ann_incstm, 'EBITDA')
    ann_gm     = ann_ebitda / ann_rev
    ann_gm_vol = ann_gm.sort_index().std()
    return {
        "Annual EBITDA Margin (series)": ann_gm,
        "Annual EBITDA Margin Volatility (stdev)": ann_gm_vol,
    }

def gross_margin_trend_bps(ann_incstm, qtr_incstm):
    ann_rev  = _get_row(ann_incstm, 'TotalRevenue', 'Revenue', 'OperatingRevenue')
    ann_cogs = _get_row(ann_incstm, 'CostOfRevenue', 'CostOfGoodsAndServicesSold')
    ann_gm   = ((ann_rev - ann_cogs) / ann_rev).sort_index()
    ann_trend = ann_gm - ann_gm.shift(1)
    ann_trend_avg_bps = ann_trend.mean() * 10000.0
    qtr_rev  = _get_row(qtr_incstm, 'TotalRevenue', 'Revenue', 'OperatingRevenue')
    qtr_cogs = _get_row(qtr_incstm, 'CostOfRevenue', 'CostOfGoodsAndServicesSold')
    qtr_gm   = ((qtr_rev - qtr_cogs) / qtr_rev).sort_index()
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
    cogs = _get_row(ann_incstm, 'CostOfRevenue', 'CostOfGoodsAndServicesSold')
    inv  = _get_row(ann_bs, 'Inventory')
    inv_clean = inv.dropna()
    if len(inv_clean) >= 2:
        avg_inv_latest_two = inv_clean.iloc[:2].mean()
    elif len(inv_clean) == 1:
        avg_inv_latest_two = inv_clean.iloc[0]
    else:
        avg_inv_latest_two = np.nan
    cogs0 = _iloc0(cogs)
    turnover_latest = (cogs0 / avg_inv_latest_two) if (avg_inv_latest_two and avg_inv_latest_two != 0) else np.nan
    with np.errstate(divide='ignore', invalid='ignore'):
        turnover_series = cogs / inv
    return {
        "Annual COGS": cogs,
        "Annual Inventory": inv,
        "Average Inventory (latest two)": avg_inv_latest_two,
        "Inventory Turnover (series)": turnover_series,
        "Inventory Turnover (Latest)": turnover_latest,
    }

def interest_coverage(ann_incstm):
    ebit    = _get_row(ann_incstm, 'EBIT', 'OperatingIncome')
    int_exp = _get_row(ann_incstm, 'InterestExpense')
    denom0  = _iloc0(int_exp)
    denom_latest = abs(denom0) if not np.isnan(denom0) else 0
    coverage_latest = (_iloc0(ebit) / denom_latest) if denom_latest != 0 else float('inf')
    with np.errstate(divide='ignore', invalid='ignore'):
        coverage_series = ebit / abs(int_exp)
    return {
        "Annual EBIT": ebit,
        "Annual Interest Expense": int_exp,
        "Interest Coverage (series)": coverage_series,
        "Interest Coverage (Latest)": coverage_latest,
    }

def cash_to_debt(ann_bs):
    cash       = _get_row(ann_bs, 'CashAndCashEquivalents', 'Cash')
    sti        = _get_row(ann_bs, 'ShortTermInvestments', 'OtherShortTermInvestments')
    total_debt = _get_row(ann_bs, 'TotalDebt')
    cash_sti   = cash + sti
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio_series = cash_sti / total_debt
    den_latest   = _iloc0(total_debt)
    ratio_latest = (_iloc0(cash_sti) / den_latest) if (den_latest and den_latest != 0) else float('inf')
    return {
        "Annual Cash": cash,
        "Annual Short Term Investments": sti,
        "Annual Total Debt": total_debt,
        "Cash+STI (series)": cash_sti,
        "Cash+STI / Total Debt (series)": ratio_series,
        "Cash+STI / Total Debt (Latest)": ratio_latest,
    }

def dso_change_yoy(ann_incstm, ann_bs, days=365):
    ar  = _get_row(ann_bs, 'AccountsReceivable', 'NetReceivables')
    rev = _get_row(ann_incstm, 'TotalRevenue', 'Revenue', 'OperatingRevenue')
    dso_series   = (ar / rev.replace(0, np.nan)) * days
    dso_series   = dso_series.dropna()
    delta_latest = (dso_series.iloc[0] - dso_series.iloc[1]) if len(dso_series) >= 2 else np.nan
    return {
        "Annual Accounts Receivable": ar,
        "Annual Revenue": rev,
        "DSO (series, days)": dso_series,
        "DSO Change (YoY, days) Latest": delta_latest,
    }

# -- Financials Metrics ---------------------------------------------

def ppnr(ann_incstm):
    nii       = _get_row(ann_incstm, 'NetInterestIncome')
    total_rev = _get_row(ann_incstm, 'TotalRevenue', 'Revenue', 'OperatingRevenue')
    nonint_income = total_rev - nii
    sga   = ann_incstm.loc['SellingGeneralAndAdministration', :] if 'SellingGeneralAndAdministration' in ann_incstm.index else 0
    other = ann_incstm.loc['OtherNonInterestExpense', :] if 'OtherNonInterestExpense' in ann_incstm.index else 0
    nonint_expense = sga + other
    ppnr_series = (nii + nonint_income - nonint_expense).sort_index(ascending=False)
    return {
        "PPNR (series)": ppnr_series,
        "PPNR (Latest)": _iloc0(ppnr_series),
        "PPNR Growth YoY (Latest)": _yoy(ppnr_series),
    }

def efficiency_ratio(ann_incstm):
    nii       = _get_row(ann_incstm, 'NetInterestIncome')
    total_rev = _get_row(ann_incstm, 'TotalRevenue', 'Revenue', 'OperatingRevenue')
    nonint_income = total_rev - nii
    sga   = ann_incstm.loc['SellingGeneralAndAdministration', :] if 'SellingGeneralAndAdministration' in ann_incstm.index else 0
    other = ann_incstm.loc['OtherNonInterestExpense', :] if 'OtherNonInterestExpense' in ann_incstm.index else 0
    nonint_expense = sga + other
    eff_series = (nonint_expense / (nii + nonint_income)).sort_index(ascending=False)
    eff0 = _iloc0(eff_series)
    eff1 = _iloc1(eff_series)
    eff_delta = ((eff0 - eff1) * 10000.0) if not np.isnan(eff1) else np.nan
    return {
        "Efficiency Ratio (series)": eff_series,
        "Efficiency Ratio (Latest)": eff0,
        "Efficiency Ratio Δ YoY (bps) Latest": eff_delta,
    }

def nii_growth_yoy(ann_incstm):
    nii = _get_row(ann_incstm, 'NetInterestIncome').sort_index(ascending=False)
    return {
        "Net Interest Income (series)": nii,
        "NII Growth YoY (Latest)": _yoy(nii),
    }

def ppnr_growth_volatility_qtr(qtr_incstm):
    nii       = _get_row(qtr_incstm, 'NetInterestIncome')
    total_rev = _get_row(qtr_incstm, 'TotalRevenue', 'Revenue', 'OperatingRevenue')
    nonint_income = total_rev - nii
    sga   = qtr_incstm.loc['SellingGeneralAndAdministration', :] if 'SellingGeneralAndAdministration' in qtr_incstm.index else 0
    other = qtr_incstm.loc['OtherNonInterestExpense', :] if 'OtherNonInterestExpense' in qtr_incstm.index else 0
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
    net_inc = _get_row(ann_incstm, 'NetIncome')
    equity  = _get_row(ann_bs, 'TotalEquityGrossMinorityInterest', 'StockholdersEquity')
    assets  = _get_row(ann_bs, 'TotalAssets')
    roe_series = (net_inc / equity).sort_index(ascending=False)
    roa_series = (net_inc / assets).sort_index(ascending=False)
    return {
        "ROE (series)": roe_series,
        "ROE (Latest)": _iloc0(roe_series),
        "ROA (series)": roa_series,
        "ROA (Latest)": _iloc0(roa_series),
    }

def equity_to_assets(ann_bs):
    equity = _get_row(ann_bs, 'TotalEquityGrossMinorityInterest', 'StockholdersEquity')
    assets = _get_row(ann_bs, 'TotalAssets')
    ea_series = (equity / assets).sort_index(ascending=False)
    return {
        "Equity / Assets (series)": ea_series,
        "Equity / Assets (Latest)": _iloc0(ea_series),
    }

def ppnr_to_assets(ann_incstm, ann_bs):
    pp_series = ppnr(ann_incstm)["PPNR (series)"]
    assets    = _get_row(ann_bs, 'TotalAssets')
    pa_series = (pp_series / assets).sort_index(ascending=False)
    return {
        "PPNR / Assets (series)": pa_series,
        "PPNR / Assets (Latest)": _iloc0(pa_series),
    }
