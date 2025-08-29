import asyncio
import json
import yfinance as yf
from llama_index.llms.openai import OpenAI
from llama_index.core.workflow import (
    StartEvent,
    StopEvent,
    Context,
    step,
    Workflow,
    InputRequiredEvent,
    HumanResponseEvent,
)
from llama_index.core.agent.workflow import ReActAgent
from regime_state import (
    State,
    TickerState,
    ParentState,
    Financials,
    LLMEvaluation
)
from events import (
    ProcessTicker,
    PullFinancialData,
    ExpansionRoute,
    InflationRoute,
    StagflationRoute,
    RecessionRoute,
    MetricsEvent,
    DataCommentary,
    ResultEvent
    )
from regime_utils import *
from metrics import *
from evaluation_tables import (
    OUTLIER_TABLE,
    OUTLIER_TABLE_FINANCIALS
)

# --- Workflow Declarations ------------------------------------------

class RegimeScreeningWorkflow(Workflow): pass
class ParallelRegimeScreeningWorkflow(RegimeScreeningWorkflow): pass

# --- RegimeScreeningWorkflow Steps ---------------------------------------------------------

@step(workflow=RegimeScreeningWorkflow)
async def start_workflow(ctx: Context[State], ev: StartEvent) -> None | ProcessTicker:
    regime_resp = await ctx.wait_for_event(
        HumanResponseEvent,
        waiter_id="EconomicRegime",
        waiter_event=InputRequiredEvent(
            prefix="Select regime by number: 0=Expansionary, 1=Inflationary, 2=Stagflationary, 3=Recession"
        ),
    )
    regime_opts = ['Expansionary', 'Inflationary', 'Stagflationary', 'Recession']
    try:
        regime_choice = regime_opts[int(regime_resp.response.strip())]
    except Exception:
        print('An error occured. Try again...')
        start_workflow(ctx,ev)

    ticker_resp = await ctx.wait_for_event(
        HumanResponseEvent,
        waiter_id="Ticker",
        waiter_event=InputRequiredEvent(prefix="Input a ticker for the stock you want to screen:"),
    )
    ticker = str(ticker_resp.response.strip())
    
    async with ctx.store.edit_state() as st:
        st.EconomicRegime = regime_choice
        st.Ticker = ticker
    return ProcessTicker(ticker=ticker)

@step(workflow=RegimeScreeningWorkflow)
async def pull_financial_data(ctx: Context[State], ev: ProcessTicker) -> PullFinancialData:
    ticker = ev.ticker
    print(f"Fetching financials for {ticker} via yfinance...")
    stock = await asyncio.to_thread(yf.Ticker, ticker)
    sector = await asyncio.to_thread(lambda: stock.info['sector'])
    ann_income_df = await asyncio.to_thread(lambda: stock.get_financials(freq='yearly'))
    ann_bs_df = await asyncio.to_thread(lambda: stock.get_balance_sheet(freq='yearly'))
    qtr_income_df = await asyncio.to_thread(lambda: stock.get_financials(freq='quarterly'))
    qtr_bs_df = await asyncio.to_thread(lambda: stock.get_balance_sheet(freq='quarterly'))

    async with ctx.store.edit_state() as st:
        st.FinancialData = Financials(
                    Ann_BalanceSheet=ann_bs_df.to_dict(),
                    Ann_IncomeStatement=ann_income_df.to_dict(),
                    Qtr_BalanceSheet=qtr_bs_df.to_dict(),
                    Qtr_IncomeStatement=qtr_income_df.to_dict()
                )
        st.Sector = sector
    print("Financial data stored.")
    return PullFinancialData(ticker=ticker)

@step(workflow=RegimeScreeningWorkflow)
async def regime_router(ctx: Context[State], ev: PullFinancialData) -> ExpansionRoute | InflationRoute | StagflationRoute | RecessionRoute:
    state = await ctx.store.get_state()
    regime = state.EconomicRegime
    
    if regime == "Expansionary":
        return ExpansionRoute(ticker=ev.ticker)
    elif regime == "Inflationary":
        return InflationRoute(ticker=ev.ticker)
    elif regime == "Stagflationary":
        return StagflationRoute(ticker=ev.ticker)
    elif regime == "Recession":
        return RecessionRoute(ticker=ev.ticker)
    else:
        print("Invalid regime. Please try again.")
        start_workflow(ctx)
        
@step(workflow=RegimeScreeningWorkflow)
async def ExpansionMetrics(ctx: Context[State], ev: ExpansionRoute) -> MetricsEvent:
    state = await ctx.store.get_state()
    ann_inc, qtr_inc, ann_bs, qtr_bs = get_financials(state)

    if state.Sector == 'Financial Services':
        metrics = calculate_financials_metrics(state.EconomicRegime,ann_inc,ann_bs,qtr_inc)
    else:
        rg  = revenue_growth(ann_inc, qtr_inc)
        em  = ebitda_margin(ann_inc, qtr_inc)
        nd  = net_debt_to_ebitda(ann_inc, ann_bs)
        metrics = {
        "Revenue Growth (YoY)": rg["Annual Revenue Growth"],
        "EBITDA Margin": em["Annual EBITDA Margin (Latest)"],
        "Net Debt / EBITDA": nd["Net Debt / EBITDA (Latest)"],
        "supplemental info": {
            "Revenue Growth": {k: str(v) for k, v in rg.items() if k != "Annual Revenue Growth"},
            "EBITDA Margin": {k: str(v) for k, v in em.items() if k != "Annual EBITDA Margin (Latest)"},
            "Net Debt / EBITDA": {k: str(v) for k, v in nd.items() if k != "Net Debt / EBITDA (Latest)"},
            },
        }
    print("=" *50)
    print("METRICS")
    print("="*50)
    print(str(metrics))
    await save_metrics(ctx, metrics)
    return MetricsEvent(ticker=ev.ticker)

@step(workflow=RegimeScreeningWorkflow)
async def InflationMetrics(ctx: Context[State], ev: InflationRoute) -> MetricsEvent:
    state = await ctx.store.get_state()
    ann_inc, qtr_inc, ann_bs, qtr_bs = get_financials(state)

    if state.Sector == 'Financial Services':
        metrics = calculate_financials_metrics(state.EconomicRegime,ann_inc,ann_bs,qtr_inc)
    else:
        gmt  = gross_margin_trend_bps(ann_inc, qtr_inc)
        it  = inventory_turnover(ann_inc, ann_bs)
        ic  = interest_coverage(ann_inc)

        metrics = {
            "Gross Margin Trend (YoY, bps)": gmt["Annual GM Trend Avg (bps)"],
            "Inventory Turnover (x)": it["Inventory Turnover (Latest)"],
            "Interest Coverage (EBIT/InterestExpense)": ic["Interest Coverage (Latest)"],
            "supplemental info": {
                "Gross Margin Trend": {k: str(v) for k, v in gmt.items() if k != "Annual GM Trend Avg (bps)"},
                "Inventory Turnover (x)": {k: str(v) for k, v in it.items() if k != "Inventory Turnover (Latest)"},
                "Interest Coverage (EBIT/InterestExpense)": {k: str(v) for k, v in ic.items() if k != "Interest Coverage (Latest)"},
            },
        }
    print("=" *50)
    print("METRICS")
    print("="*50)
    print(str(metrics))
    await save_metrics(ctx, metrics)
    return MetricsEvent(ticker=ev.ticker)


@step(workflow=RegimeScreeningWorkflow)
async def StagflationMetrics(ctx: Context[State], ev: StagflationRoute) -> MetricsEvent:
    state = await ctx.store.get_state()
    ann_inc, qtr_inc, ann_bs, qtr_bs = get_financials(state)

    if state.Sector == 'Financial Services':
        metrics = calculate_financials_metrics(state.EconomicRegime,ann_inc,ann_bs,qtr_inc)
    else:
        emv = ebitda_margin_volatility(ann_inc)
        gmt  = gross_margin_trend_bps(ann_inc, qtr_inc)
        nd  = net_debt_to_ebitda(ann_inc, ann_bs)

        metrics = {
            "EBITDA Margin Volatility": emv["Annual EBITDA Margin Volatility (stdev)"],
            "Gross Margin Trend (YoY, bps)": gmt["Annual GM Trend Avg (bps)"],
            "Net Debt / EBITDA": nd["Net Debt / EBITDA (Latest)"],
            "supplemental info": {
                "EBITDA Margin Volatility": {k: str(v) for k, v in emv.items() if k != "Annual EBITDA Margin Volatility (stdev)"},
                "Gross Margin Trend": {k: str(v) for k, v in gmt.items() if k != "Annual GM Trend Avg (bps)"},
                "Net Debt / EBITDA": {k: str(v) for k, v in nd.items() if k != "Net Debt / EBITDA (Latest)"},
            },
        }
    print("=" *50)
    print("METRICS")
    print("="*50)
    print(str(metrics))
    await save_metrics(ctx, metrics)
    return MetricsEvent(ticker=ev.ticker)

@step(workflow=RegimeScreeningWorkflow)
async def RecessionMetrics(ctx: Context[State], ev: RecessionRoute) -> MetricsEvent:
    state = await ctx.store.get_state()
    ann_inc, qtr_inc, ann_bs, qtr_bs = get_financials(state)

    if state.Sector == 'Financial Services':
        metrics = calculate_financials_metrics(state.EconomicRegime,ann_inc,ann_bs,qtr_inc)
    else:
        ctd = cash_to_debt(ann_bs)
        ic  = interest_coverage(ann_inc)
        dso = dso_change_yoy(ann_inc, ann_bs)

        metrics = {
            "Cash & ST Inv. / Total Debt": ctd["Cash+STI / Total Debt (Latest)"],
            "Interest Coverage (EBIT/InterestExpense)": ic["Interest Coverage (Latest)"],
            "DSO Change (YoY, days)": dso["DSO Change (YoY, days) Latest"],
            "supplemental info": {
                "Cash & ST Inv. / Total Debt": {k: str(v) for k, v in ctd.items() if k != "Cash+STI / Total Debt (Latest)"},
                "Interest Coverage (EBIT/InterestExpense)": {k: str(v) for k, v in ic.items() if k != "Interest Coverage (Latest)"},
                "DSO Change (YoY, days)": {k: str(v) for k, v in dso.items() if k != "DSO Change (YoY, days) Latest"},
            },
        }
    print("=" *50)
    print("METRICS")
    print("="*50)
    print(str(metrics))
    await save_metrics(ctx, metrics)
    return MetricsEvent(ticker=ev.ticker)

@step(workflow=RegimeScreeningWorkflow)
async def data_validation(ctx: Context[State], ev: MetricsEvent) -> DataCommentary:
    state = await ctx.store.get_state()
    metrics = state.MetricData.MetricData or {}
    sector = state.Sector
    outlier_table = OUTLIER_TABLE if sector=='Financial Services' else OUTLIER_TABLE_FINANCIALS
    
    if not metrics:
        return StopEvent(result="No financial metrics available for evaluation.")
    
    llm = OpenAI(model="gpt-4.1-mini",temperature=0)
    calls=[]
    
    def get_annual_income_data():
        """Get annual income statement data"""
        result = to_df(state.FinancialData.Ann_IncomeStatement)
        calls.append('Called Annual Income')
        return result
    
    def get_quarterly_income_data():
        """Get quarterly income statement data"""
        result = to_df(state.FinancialData.Qtr_IncomeStatement)
        calls.append('Called Quarterly Income')
        return result
    
    def get_annual_balance_data():
        """Get annual balance sheet data"""
        result = to_df(state.FinancialData.Ann_BalanceSheet)
        calls.append('Called Annual Balance Sheet')
        return result
    
    def get_quarterly_balance_data():
        """Get quarterly balance sheet data"""
        result = to_df(state.FinancialData.Qtr_BalanceSheet)
        calls.append('Called Quarterly Balance Sheet')
        return result
    
    tools = [
        get_annual_income_data,
        get_quarterly_income_data, 
        get_annual_balance_data,
        get_quarterly_balance_data,
    ]
    
    agent = ReActAgent(tools=tools, llm=llm, verbose=True)  # Add verbose=True
    
    prompt = (
        f"Evaluate the following financial metrics for accuracy, completeness, and nuance.\n\n"
        f"{json.dumps(metrics, indent=2)}\n\n"
        "Look at the outlier table:\n\n"   
        f"{outlier_table}"
        "and comment on any metrics that fall in the extreme upper and lower bounds by looking at the input data by accessing the financial data through your tools."
        "and determine if the metrics are reasonable based on the input data or if there are odd/missing items that are affecting their calculations."
        "Lastly, comment on the nuance that may be affecting these metrics that would be important to determine their value."
        "For example, if gross margin volatility is in the extreme upper bound but the volatility is mostly comming from the upside or extremely high values of gross margin then provide this nuance in the commentary. YOU MUST LIST ALL THE TOOLS YOU HAVE ACCESS TO AND CALL AT LEAST ONE!!!"
    )
    
    resp = await agent.run(prompt)

    print(calls)
    print("=" * 50)
    print("DATA VALIDATION COMMENTARY")
    print("=" * 50)
    print(resp)
    
    async with ctx.store.edit_state() as st:
        st.DataCommentary = resp
    
    return DataCommentary(ticker=ev.ticker)

@step(workflow=RegimeScreeningWorkflow)
async def evaluate_financials(ctx: Context[State], ev: DataCommentary) -> StopEvent:
    state = await ctx.store.get_state()
    regime = state.EconomicRegime or ""
    is_financials = True if state.Sector=='Financial Services' else False
    criteria = regime_to_criteria(state, regime, is_financials)
    metrics = state.MetricData.MetricData or {}
    if not metrics:
        return StopEvent(result=f"No financial metrics available for evaluation (Ticker:{state.Ticker}).")
    data_commentary = state.DataCommentary
    llm = OpenAI(model="gpt-4.1-mini",temperature=0)
    sllm = llm.as_structured_llm(LLMEvaluation)
    prompt = (
        "You are a seasoned portfolio manager and you are evaluating potential investments in companies based on "
        "how well their financial metrics align with the favorability metrics for different economic regimes."
        f"Evaluate the following financial metrics based on the criteria for {regime} regime:\n\n"
        f"{json.dumps(metrics, indent=2)}\n\n"
        f"Criteria:\n{criteria}\n\n"
        f"Look at the data validation commentary to determine if the data is accurate, complete or if there is nuance you need to incorporate in your evaluation."
        f"Data Validation Commentary:\n{data_commentary}\n\n"
        "Provide an explanation and a score from 0 to 100, where 0 is poor fitness for the regime and 100 is excellent. Put your response in json format {'explanation':<your explanation>,'score':<your score>}"
    )
    resp = await sllm.acomplete(prompt)
    evaluation: LLMEvaluation = resp.raw
    print("=" *50)
    print("SCORE EVALUATION")
    print("="*50)
    print(evaluation.explanation)

    async with ctx.store.edit_state() as st:
        st.EvaluationResult = LLMEvaluation(
            explanation=evaluation.explanation,
            score=evaluation.score,
        )

    return StopEvent(result=evaluation)

# --- ParallelRegimeScreeningWorkflow Steps ---------------------------------------------------------
@step(workflow=ParallelRegimeScreeningWorkflow)
async def start_workflow(ctx: Context[ParentState], ev: StartEvent) -> None | ProcessTicker:
    regime_resp = await ctx.wait_for_event(
        HumanResponseEvent,
        waiter_id="EconomicRegime",
        waiter_event=InputRequiredEvent(
            prefix="Select regime by number: 0=Expansionary, 1=Inflationary, 2=Stagflationary, 3=Recession"
        ),
    )
    regime_opts = ['Expansionary', 'Inflationary', 'Stagflationary', 'Recession']
    try:
        regime_choice = regime_opts[int(regime_resp.response.strip())]
    except Exception:
        print("Invalid regime. Try again.")
        return ctx.send_event(StartEvent())

    tickers_resp = await ctx.wait_for_event(
        HumanResponseEvent,
        waiter_id="Tickers",
        waiter_event=InputRequiredEvent(prefix="Enter comma-separated tickers (e.g. aapl,nvda,jnj):"),
    )
    tickers = [t.strip().upper() for t in tickers_resp.response.split(",") if t.strip()]

    async with ctx.store.edit_state() as st:
        st.EconomicRegime = regime_choice
        st.Tickers = tickers
        st.children = {t: TickerState(Ticker=t) for t in tickers}
        st.completed = set()

    for t in tickers:
        ctx.send_event(ProcessTicker(ticker=t))

@step(workflow=ParallelRegimeScreeningWorkflow, num_workers=10)
async def pull_financial_data(ctx: Context[ParentState], ev: ProcessTicker) -> PullFinancialData:
    t = ev.ticker
    print(f"Fetching financials for {t} via yfinance...")
    stock = await asyncio.to_thread(yf.Ticker, t)
    sector = await asyncio.to_thread(lambda: stock.info['sector'])
    ann_income_df = await asyncio.to_thread(lambda: stock.get_financials(freq='yearly'))
    ann_bs_df    = await asyncio.to_thread(lambda: stock.get_balance_sheet(freq='yearly'))
    qtr_income_df= await asyncio.to_thread(lambda: stock.get_financials(freq='quarterly'))
    qtr_bs_df    = await asyncio.to_thread(lambda: stock.get_balance_sheet(freq='quarterly'))

    async with ctx.store.edit_state() as st:
        child = st.children[t]
        child.Sector = sector
        child.FinData = Financials(
            Ann_BalanceSheet=ann_bs_df.to_dict(),
            Ann_IncomeStatement=ann_income_df.to_dict(),
            Qtr_BalanceSheet=qtr_bs_df.to_dict(),
            Qtr_IncomeStatement=qtr_income_df.to_dict(),
        )
        st.children[t] = child  
    return PullFinancialData(ticker=t)

@step(workflow=ParallelRegimeScreeningWorkflow,num_workers=10)
async def regime_router(ctx: Context[ParentState], ev: PullFinancialData) -> ExpansionRoute | InflationRoute | StagflationRoute | RecessionRoute:
    regime = (await ctx.store.get_state()).EconomicRegime
    t = ev.ticker
    if regime == "Expansionary":
        return ExpansionRoute(ticker=t)
    if regime == "Inflationary":
        return InflationRoute(ticker=t)
    if regime == "Stagflationary":
        return StagflationRoute(ticker=t)
    if regime == "Recession":
        return RecessionRoute(ticker=t)
    print("Invalid regime in state; restarting.")
    return None

@step(workflow=ParallelRegimeScreeningWorkflow,num_workers=10)
async def expansion_metrics(ctx: Context[ParentState], ev: ExpansionRoute) -> MetricsEvent:
    t = ev.ticker
    state = await ctx.store.get_state()
    child = state.children[t]
    ann_inc = child.FinData.Ann_IncomeStatement
    qtr_inc = child.FinData.Qtr_IncomeStatement
    ann_bs  = child.FinData.Ann_BalanceSheet

    if child.Sector == 'Financial Services':
        metrics = calculate_financials_metrics(state.EconomicRegime,to_df(ann_inc),to_df(ann_bs),to_df(qtr_inc))
    else:
        rg  = revenue_growth(to_df(ann_inc), to_df(qtr_inc))
        em  = ebitda_margin(to_df(ann_inc), to_df(qtr_inc))
        nd  = net_debt_to_ebitda(to_df(ann_inc), to_df(ann_bs))
        metrics = {
        "Revenue Growth (YoY)": rg["Annual Revenue Growth"],
        "EBITDA Margin": em["Annual EBITDA Margin (Latest)"],
        "Net Debt / EBITDA": nd["Net Debt / EBITDA (Latest)"],
        "supplemental info": {
            "Revenue Growth": {k: str(v) for k, v in rg.items() if k != "Annual Revenue Growth"},
            "EBITDA Margin": {k: str(v) for k, v in em.items() if k != "Annual EBITDA Margin (Latest)"},
            "Net Debt / EBITDA": {k: str(v) for k, v in nd.items() if k != "Net Debt / EBITDA (Latest)"},
            },
        }
    async with ctx.store.edit_state() as st:
        st.children[t].MetricData.MetricData = metrics

    print(f"[{t}] metrics computed")
    return MetricsEvent(ticker=t)

@step(workflow=ParallelRegimeScreeningWorkflow,num_workers=10)
async def inflation_metrics(ctx: Context[ParentState], ev: InflationRoute) -> MetricsEvent:
    t = ev.ticker
    state = await ctx.store.get_state()
    child = state.children[t]
    ann_inc = child.FinData.Ann_IncomeStatement
    qtr_inc = child.FinData.Qtr_IncomeStatement
    ann_bs  = child.FinData.Ann_BalanceSheet

    if child.Sector == 'Financial Services':
        metrics = calculate_financials_metrics(state.EconomicRegime,to_df(ann_inc),to_df(ann_bs),to_df(qtr_inc))
    else:
        gmt  = gross_margin_trend_bps(to_df(ann_inc), to_df(qtr_inc))
        it  = inventory_turnover(to_df(ann_inc), to_df(ann_bs))
        ic  = interest_coverage(to_df(ann_inc))

        metrics = {
            "Gross Margin Trend (YoY, bps)": gmt["Annual GM Trend Avg (bps)"],
            "Inventory Turnover (x)": it["Inventory Turnover (Latest)"],
            "Interest Coverage (EBIT/InterestExpense)": ic["Interest Coverage (Latest)"],
            "supplemental info": {
                "Gross Margin Trend": {k: str(v) for k, v in gmt.items() if k != "Annual GM Trend Avg (bps)"},
                "Inventory Turnover (x)": {k: str(v) for k, v in it.items() if k != "Inventory Turnover (Latest)"},
                "Interest Coverage (EBIT/InterestExpense)": {k: str(v) for k, v in ic.items() if k != "Interest Coverage (Latest)"},
            },
        }
    async with ctx.store.edit_state() as st:
        st.children[t].MetricData.MetricData = metrics

    print(f"[{t}] metrics computed")
    return MetricsEvent(ticker=t)

@step(workflow=ParallelRegimeScreeningWorkflow,num_workers=10)
async def stagflation_metrics(ctx: Context[ParentState], ev: StagflationRoute) -> MetricsEvent:
    t = ev.ticker
    state = await ctx.store.get_state()
    child = state.children[t]
    ann_inc = child.FinData.Ann_IncomeStatement
    qtr_inc = child.FinData.Qtr_IncomeStatement
    ann_bs  = child.FinData.Ann_BalanceSheet

    if child.Sector == 'Financial Services':
        metrics = calculate_financials_metrics(state.EconomicRegime,to_df(ann_inc),to_df(ann_bs),to_df(qtr_inc))
    else:
        emv = ebitda_margin_volatility(to_df(ann_inc))
        gmt  = gross_margin_trend_bps(to_df(ann_inc), to_df(qtr_inc))
        nd  = net_debt_to_ebitda(to_df(ann_inc), to_df(ann_bs))

        metrics = {
            "EBITDA Margin Volatility": emv["Annual EBITDA Margin Volatility (stdev)"],
            "Gross Margin Trend (YoY, bps)": gmt["Annual GM Trend Avg (bps)"],
            "Net Debt / EBITDA": nd["Net Debt / EBITDA (Latest)"],
            "supplemental info": {
                "EBITDA Margin Volatility": {k: str(v) for k, v in emv.items() if k != "Annual EBITDA Margin Volatility (stdev)"},
                "Gross Margin Trend": {k: str(v) for k, v in gmt.items() if k != "Annual GM Trend Avg (bps)"},
                "Net Debt / EBITDA": {k: str(v) for k, v in nd.items() if k != "Net Debt / EBITDA (Latest)"},
            },
        }
    async with ctx.store.edit_state() as st:
        st.children[t].MetricData.MetricData = metrics

    print(f"[{t}] metrics computed")
    return MetricsEvent(ticker=t)

@step(workflow=ParallelRegimeScreeningWorkflow,num_workers=10)
async def recession_metrics(ctx: Context[ParentState], ev: RecessionRoute) -> MetricsEvent:
    t = ev.ticker
    state = await ctx.store.get_state()
    child = state.children[t]
    ann_inc = child.FinData.Ann_IncomeStatement
    ann_bs  = child.FinData.Ann_BalanceSheet
    qtr_inc = child.FinData.Qtr_IncomeStatement

    if child.Sector == 'Financial Services':
        metrics = metrics = calculate_financials_metrics(state.EconomicRegime,to_df(ann_inc),to_df(ann_bs),to_df(qtr_inc))
    else:

        ctd = cash_to_debt(to_df(ann_bs))
        ic  = interest_coverage(to_df(ann_inc))
        dso = dso_change_yoy(to_df(ann_inc), to_df(ann_bs))

        metrics = {
            "Cash & ST Inv. / Total Debt": ctd["Cash+STI / Total Debt (Latest)"],
            "Interest Coverage (EBIT/InterestExpense)": ic["Interest Coverage (Latest)"],
            "DSO Change (YoY, days)": dso["DSO Change (YoY, days) Latest"],
            "supplemental info": {
                "Cash & ST Inv. / Total Debt": {k: str(v) for k, v in ctd.items() if k != "Cash+STI / Total Debt (Latest)"},
                "Interest Coverage (EBIT/InterestExpense)": {k: str(v) for k, v in ic.items() if k != "Interest Coverage (Latest)"},
                "DSO Change (YoY, days)": {k: str(v) for k, v in dso.items() if k != "DSO Change (YoY, days) Latest"},
            },
        }
    async with ctx.store.edit_state() as st:
        st.children[t].MetricData.MetricData = metrics

    print(f"[{t}] metrics computed")
    return MetricsEvent(ticker=t)

@step(workflow=ParallelRegimeScreeningWorkflow,num_workers=10)
async def data_validation(ctx:Context[ParentState],ev: MetricsEvent) -> DataCommentary:
    t = ev.ticker
    state = await ctx.store.get_state()
    child = state.children[t]
    sector = child.Sector
    outlier_table = OUTLIER_TABLE if sector=='Financial Services' else OUTLIER_TABLE_FINANCIALS
    metrics = child.MetricData.MetricData
    if not metrics:
        return DataCommentary(ticker=t)

    ann_inc = child.FinData.Ann_IncomeStatement
    qtr_inc = child.FinData.Qtr_IncomeStatement
    ann_bs  = child.FinData.Ann_BalanceSheet
    qtr_bs  = child.FinData.Qtr_BalanceSheet

    if not metrics:
        return StopEvent(result="No financial metrics available for evaluation.")
    
    llm = OpenAI(model="gpt-4.1",temperature=0,)
    calls=[]
    
    def get_annual_income_data():
        """Get annual income statement data"""
        result = to_df(ann_inc)
        calls.append('Called Annual Income')
        return result
    
    def get_quarterly_income_data():
        """Get quarterly income statement data"""
        result = to_df(qtr_inc)
        calls.append('Called Quarterly Income')
        return result
    
    def get_annual_balance_data():
        """Get annual balance sheet data"""
        result = to_df(ann_bs)
        calls.append('Called Annual Balance Sheet')
        return result
    
    def get_quarterly_balance_data():
        """Get quarterly balance sheet data"""
        result = to_df(qtr_bs)
        calls.append('Called Quarterly Balance Sheet')
        return result
    
    tools = [
        get_annual_income_data,
        get_quarterly_income_data, 
        get_annual_balance_data,
        get_quarterly_balance_data,
    ]
    
    agent = ReActAgent(tools=tools, llm=llm, verbose=True)  # Add verbose=True
    
    prompt = (
        f"Evaluate the following financial metrics for accuracy, completeness, and nuance.\n\n"
        f"{json.dumps(metrics, indent=2)}\n\n"
        "Look at the outlier table:\n\n"   
        f"{outlier_table}"
        "and comment on any metrics that fall in the extreme upper and lower bounds by looking at the input data by accessing the financial data through your tools."
        "and determine if the metrics are reasonable based on the input data or if there are odd/missing items that are affecting their calculations."
        "Lastly, comment on the nuance that may be affecting these metrics that would be important to determine their value."
        "For example, if gross margin volatility is in the extreme upper bound but the volatility is mostly comming from the upside or extremely high values of gross margin then provide this nuance in the commentary. YOU MUST LIST ALL THE TOOLS YOU HAVE ACCESS TO AND CALL AT LEAST ONE!!!"
    )
    
    resp = await agent.run(prompt)

    print(calls)
    async with ctx.store.edit_state() as st:
        st.children[t].DataCommentary = resp

    print(f"[{t}] data validation commentary saved")
    return DataCommentary(ticker=t)

@step(workflow=ParallelRegimeScreeningWorkflow,num_workers=10)
async def evaluate_financials(ctx: Context[ParentState], ev: DataCommentary) -> ResultEvent:
    t = ev.ticker
    state = await ctx.store.get_state()
    regime = state.EconomicRegime or ""
    child = state.children[t]
    is_financials = True if child.Sector=='Financial Services' else False
    metrics = child.MetricData.MetricData or {}
    print(metrics)

    if not metrics:
        # still emit a result so fan-in can proceed
        async with ctx.store.edit_state() as st:
            st.children[t].EvaluationResult = LLMEvaluation(explanation="No metrics", score=0.0)
        return ResultEvent(ticker=t)

    criteria = regime_to_criteria(state, regime, is_financials)
    data_commentary = child.DataCommentary or ""
    llm = OpenAI(model="gpt-4.1",temperature=0, request_timeout=180.0)  # 2 minute timeout
    sllm = llm.as_structured_llm(LLMEvaluation)
    prompt = (
        "You are a seasoned portfolio manager and you are evaluating potential investments in companies based on "
        "how well their financial metrics align with the favorability metrics for different economic regimes."
        f"Evaluate the following financial metrics based on the criteria for {regime} regime:\n\n"
        f"{json.dumps(metrics, indent=2)}\n\n"
        f"Criteria:\n{criteria}\n\n"
        f"Look at the data validation commentary to determine if the data is accurate, complete or if there is nuance you need to incorporate in your evaluation."
        f"Data Validation Commentary:\n{data_commentary}\n\n"
        "Add nuance but ground heavily on the bands provided in the criteria and the metrics."
        "Provide an explanation and a score from 0 to 100, where 0 is poor fitness for the regime and 100 is excellent. Put your response in json format {'explanation':<your explanation>,'score':<your score>}"
    )
    resp = await sllm.acomplete(prompt)
    evaluation: LLMEvaluation = resp.raw

    async with ctx.store.edit_state() as st:
        st.children[t].EvaluationResult = LLMEvaluation(
            explanation=evaluation.explanation,
            score=evaluation.score,
        )

    print(f"[{t}] evaluation saved")
    return ResultEvent(ticker=t)

@step(workflow=ParallelRegimeScreeningWorkflow)
async def combine_scores(ctx: Context[ParentState], ev: ResultEvent) -> StopEvent | None:
    t = ev.ticker
    async with ctx.store.edit_state() as st:
        st.completed.add(t)
        done = len(st.completed)
        total = len(st.Tickers)

    print(f"Completed {done}/{total}")

    if done == total:
        state = await ctx.store.get_state()
        
        result = {
            "regime": state.EconomicRegime,
            "tickers": state.Tickers,
            "evaluations": {
                tk: (
                    state.children[tk].EvaluationResult.model_dump()
                    if state.children[tk].EvaluationResult else None
                )
                for tk in state.Tickers
            },
            "metrics": {
                tk: state.children[tk].MetricData.MetricData
                for tk in state.Tickers
            },
        }
        return StopEvent(result=result)

    return None
