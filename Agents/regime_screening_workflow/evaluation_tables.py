# --Non Financials Criteria--
EXPANSIONARY_CRITERIA = """
| Metric                 | Favorable | Neutral   | Unfavorable | Rationale                                                                 |
|------------------------|-----------|-----------|-------------|---------------------------------------------------------------------------|
| Revenue Growth (YoY)   | > 8%      | 5% – 8%   | < 5%        | Strong top-line growth captures upside in expansion without inflation drag. |
| EBITDA Margin          | > 20%     | 15% – 20% | < 15%       | Healthy margins indicate efficient scaling and operating leverage.        |
| Net Debt / EBITDA      | < 1.5x    | 1.5x–3.0x | > 3.0x      | Some leverage is fine in growth phases, but excess adds downside risk.    |"""

INFLATIONARY_CRITERIA = """
| Metric                               | Favorable | Neutral   | Unfavorable | Rationale                                                                 |
|--------------------------------------|-----------|-----------|-------------|---------------------------------------------------------------------------|
| Gross Margin Trend (YoY, bps)        | > +100    | 0 to +100 | < 0         | Sustained gross margin expansion signals pricing power vs. rising inputs. |
| Inventory Turnover (x)               | > 8x      | 5x – 8x   | < 5x        | Faster turns reduce exposure to rapidly rising input costs.               |
| Interest Coverage (EBIT / IntExp)    | > 6x      | 3x – 6x   | < 3x        | Rising rates + inflation stress weak coverage; resilient firms stay >6x.  |"""

STAGFLATIONARY_CRITERIA = """
| Metric                                    | Favorable | Neutral   | Unfavorable | Rationale                                                                  |
|-------------------------------------------|-----------|-----------|-------------|----------------------------------------------------------------------------|
| EBITDA Margin Volatility (stdev).         | < 4%      | 4% – 6%   | > 6%        | Operational stability matters when growth slows and costs rise.            |
| Gross Margin Trend (YoY, bps)             | > +50     | 0 to +50  | < 0         | Ability to hold or expand gross margin indicates pricing power.            |
| Net Debt / EBITDA                         | < 1.0x    | 1.0x–2.0x | > 2.0x      | Low leverage mitigates refinancing and spread-widening risk.               |"""

RECESSION_CRITERIA = """
| Metric                                               | Favorable | Neutral   | Unfavorable | Rationale                                                                 |
|------------------------------------------------------|-----------|-----------|-------------|---------------------------------------------------------------------------|
| Cash & ST Inv. / Total Debt                          | > 50%     | 20%–50%   | < 20%       | A strong cash cushion supports liquidity when prices and demand fall.     |
| Interest Coverage (EBIT / IntExp)                    | > 8x      | 4x – 8x   | < 4x        | High coverage protects in credit-tight, revenue-weak environments.        |
| DSO Change (Days Sales Outstanding, YoY change, days)| < +5      | +5 to +15 | > +15       | Rising DSO signals collection stress and customer weakness.               |"""

OUTLIER_TABLE = """
| Metric | Q1 | Q3 | IQR | Extreme Lower Bound (Q1 − 1.5×IQR) | Extreme Upper Bound (Q3 + 1.5×IQR) | Notes |
|--------|----|----|-----|------------------------------------|------------------------------------|-------|
| Revenue Growth (YoY) | -5% | +25% | 30 pp | -50% | +70% | Very large negative or very high growth warrants checking seasonality, M&A, one-offs. |
| EBITDA Margin | 10% | 30% | 20 pp | -20% | 60% | Implausibly high margins or deep losses need verification of classification/adjustments. |
| Net Debt / EBITDA | 1.0x | 4.0x | 3.0x | -3.5x | 8.5x | High leverage or large net cash (negative) should be validated for definitions and normalization. |
| Gross Margin Trend (YoY, bps) | -100 | +100 | 200 bps | -400 bps | +400 bps | Large swings could reflect mix, pricing, or recognition timing anomalies. |
| Inventory Turnover (x) | 3.0x | 8.0x | 5.0x | -4.5x (floor 0) | 15.5x | Extremely low implies stale inventory; extremely high could mask stockouts or accounting quirks. |
| Interest Coverage (EBIT / Interest) | 3.0x | 15.0x | 12.0x | -15x (floor 0) | 33x | Very low coverage is a risk; very high may hide near-zero interest expense. |
| EBITDA Margin Volatility (std) | 1.0% | 5.0% | 4.0 pp | -5.0% (floor 0) | 11.0% | Excessive volatility suggests instability; near-zero (if seen) might prompt sanity check. |
| Cash & ST Inv. / Total Debt | 0.2x | 1.0x | 0.8x | -1.0x (floor 0) | 2.2x | Very low ratio signals liquidity stress; very high may reflect conservative balance sheet or classification issues. |
| DSO Change (YoY, days) | -5d | +5d | 10d | -20d | +20d | Large positive = slowing collections; large negative = aggressive behavior or write-offs. |"""

# --Financials Criteria--

EXPANSIONARY_CRITERIA_FINANCIALS = """
| Metric              | Favorable | Neutral      | Unfavorable | Rationale                                                              |
|---------------------|-----------|--------------|-------------|------------------------------------------------------------------------|
| PPNR Growth (YoY)   | > 8%      | 3% – 8%      | < 3%        | Core earnings momentum critical in expansion.                          |
| Efficiency Ratio    | < 55%     | 55% – 65%    | > 65%       | Leaner cost structure scales better in growth phases.                  |
| ROE                 | > 12%     | 8% – 12%     | < 8%        | Strong profitability relative to equity capital.                       |
"""

INFLATIONARY_CRITERIA_FINANCIALS = """
| Metric             | Favorable | Neutral       | Unfavorable | Rationale                                                               |
|--------------------|-----------|---------------|-------------|-------------------------------------------------------------------------|
| NII Growth (YoY)   | > 10%     | 3% – 10%      | < 3%        | Rising rates should boost NII in inflationary regimes.                  |
| Efficiency Ratio Δ | ≤ -200bps | -200 to +200  | > +200bps   | Cost control is critical as wage/tech inflation pressures rise.         |
| Equity / Assets    | > 10%     | 7% – 10%      | < 7%        | Strong capital buffers mitigate volatility in higher rate environments. |
"""

STAGFLATIONARY_CRITERIA_FINANCIALS = """
| Metric                       | Favorable | Neutral     | Unfavorable | Rationale                                                               |
|------------------------------|-----------|-------------|-------------|-------------------------------------------------------------------------|
| PPNR Growth Volatility (quarterly)  | < 5%      | 5% – 8%     | > 8%        | Stable *growth* in core earnings is vital when growth is weak and costs rise. |
| ROA                          | > 1.0%    | 0.6% – 1.0% | < 0.6%      | Asset efficiency matters in sluggish macro conditions.                  |
| Equity / Assets              | > 10%     | 7% – 10%    | < 7%        | Stronger capital adequacy helps offset market/credit shocks.            |
"""

RECESSION_CRITERIA_FINANCIALS = """
| Metric          | Favorable | Neutral      | Unfavorable | Rationale                                                              |
|-----------------|-----------|--------------|-------------|------------------------------------------------------------------------|
| Equity / Assets | > 10%     | 7% – 10%     | < 7%        | Thick capital cushion protects against credit losses in downturns.     |
| Efficiency Ratio| < 60%     | 60% – 70%    | > 70%       | Cost discipline becomes critical as revenues weaken.                   |
| PPNR / Assets   | > 1.2%    | 0.8% – 1.2%  | < 0.8%      | Strong pre-provision earnings relative to assets = resilience in stress.|
"""

OUTLIER_TABLE_FINANCIALS = """
| Metric                  | Q1    | Q3    | IQR   | Extreme Lower Bound (Q1 − 1.5×IQR) | Extreme Upper Bound (Q3 + 1.5×IQR) | Notes |
|-------------------------|-------|-------|-------|------------------------------------|------------------------------------|-------|
| PPNR Growth (YoY)       | -2%   | +15%  | 17 pp | -27%                               | +40%                               | Very weak or very high growth may reflect credit cycle extremes, NII shocks, or unusual expenses. |
| Efficiency Ratio        | 50%   | 70%   | 20 pp | 20% (floor 0)                      | 100%+                              | <20% may be misclassified revenues; >100% signals unsustainable costs. |
| ROE                     | 5%    | 15%   | 10 pp | -10% (floor 0)                     | +30%                               | Very low ROE suggests weak profitability; very high may reflect leverage or one-offs. |
| ROA                     | 0.4%  | 1.2%  | 0.8 pp| -0.8% (floor 0)                    | +2.4%                              | Extreme values warrant review of asset base or income recognition. |
| Equity / Assets         | 6%    | 12%   | 6 pp  | -3% (floor 0)                      | +21%                               | Very low = undercapitalization; very high may indicate niche/mix-driven business models. |
| PPNR Growth Volatility (stdev, quarterly)| 2%    | 6%    | 4 pp  | -4% (floor 0)                      | +12%                               | Quarterly growth vol better than annual with sparse data.         |
| PPNR / Assets           | 0.6%  | 1.5%  | 0.9 pp| -0.75% (floor 0)                   | +2.85%                             | Extreme low = weak core earnings; extreme high may reflect temporary windfalls or abnormal quarters. |
| NII Growth (YoY)        | -3%   | +12%  | 15 pp | -25%                               | +34%                               | Very high/low growth may reflect rate shocks, asset/liability mismatches, or trading income noise. |
"""