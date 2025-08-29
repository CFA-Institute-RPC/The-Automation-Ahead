from llama_index.core.workflow import (
    Event,
)

class ProcessTicker(Event):
    ticker: str

class PullFinancialData(Event):
    ticker: str

class ExpansionRoute(Event):
    ticker: str

class InflationRoute(Event):
    ticker: str

class StagflationRoute(Event):
    ticker: str

class RecessionRoute(Event):
    ticker: str

class MetricsEvent(Event):
    ticker: str

class DataCommentary(Event):
    ticker: str

class ResultEvent(Event):
    ticker: str