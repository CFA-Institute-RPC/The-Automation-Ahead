from typing import Optional,List,Dict
from pydantic import BaseModel, Field
from evaluation_tables import (
    EXPANSIONARY_CRITERIA, INFLATIONARY_CRITERIA, STAGFLATIONARY_CRITERIA, RECESSION_CRITERIA
)

class RegimeCriteria(BaseModel):
    Expansionary: str = Field(default=EXPANSIONARY_CRITERIA)
    Inflationary: str = Field(default=INFLATIONARY_CRITERIA)
    Stagflationary: str = Field(default=STAGFLATIONARY_CRITERIA)
    Recession: str = Field(default=RECESSION_CRITERIA)

class Financials(BaseModel):
    Ann_BalanceSheet: dict | None = Field(default=None)
    Ann_IncomeStatement: dict | None = Field(default=None)
    Qtr_BalanceSheet: dict | None = Field(default=None)
    Qtr_IncomeStatement: dict | None = Field(default=None)

class Metrics(BaseModel):
    MetricData: dict = Field(default_factory=dict)

class LLMEvaluation(BaseModel):
    explanation: Optional[str] = None
    score: Optional[int] = None

class State(BaseModel):
    EconomicRegime: Optional[str] = Field(default=None)
    Ticker: Optional[str] = Field(default=None)
    Sector: Optional[str] = Field(default=None)
    FinancialData: Financials = Field(default_factory=Financials)
    ScreeningCriteria: RegimeCriteria = Field(default_factory=RegimeCriteria)
    MetricData: Metrics = Field(default_factory=Metrics)
    DataCommentary:str = Field(default=None)
    EvaluationResult: Optional[LLMEvaluation] = None

class TickerState(BaseModel):
    Ticker: str
    Sector: Optional[str] = Field(default=None)
    FinData: Financials = Field(default_factory=Financials)
    MetricData: Metrics = Field(default_factory=Metrics)
    DataCommentary: Optional[str] = None
    EvaluationResult: Optional[LLMEvaluation] = None

class ParentState(BaseModel):
    EconomicRegime: Optional[str] = None
    ScreeningCriteria: RegimeCriteria = Field(default_factory=RegimeCriteria)
    Tickers: List[str] = Field(default_factory=list)
    children: Dict[str, TickerState] = Field(default_factory=dict)
    completed: set[str] = Field(default_factory=set)
    
