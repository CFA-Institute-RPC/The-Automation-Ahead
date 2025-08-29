from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
import operator

class OverallState(TypedDict):
    messages: Annotated[list, add_messages]
    sources_gathered: Annotated[list, operator.add]
    sources_used:Annotated[list, operator.add]
    web_research_result: Annotated[list, operator.add]
    search_query: Annotated[list, operator.add]
    initial_search_query_count: int
    max_research_loops: int
    research_loop_count: int
    

class Query(TypedDict):
    query: str
    rationale: str

class QueryGenerationState(TypedDict):
    query_list: list[Query]

class WebSearchState(TypedDict):
    search_query: str
    id: str

class ReflectionState(TypedDict):
    is_sufficient: bool
    knowledge_gap: str
    follow_up_queries: Annotated[list, operator.add]
    research_loop_count: int
    number_of_ran_queries: int
