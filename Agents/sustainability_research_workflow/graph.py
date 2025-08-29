from langgraph.graph import StateGraph, START, END
from state import OverallState
from configuration import Configuration

from dotenv import load_dotenv
from nodes import (
    generate_queries,
    web_research,
    continue_to_web_research,
    reflection,
    finalize_answer,
    evaluate_research
)

load_dotenv()

graph_builder = StateGraph(OverallState, config_schema=Configuration)

# ==========================================
# Define Nodes
# ==========================================

graph_builder.add_node("generate_queries",generate_queries)
graph_builder.add_node("web_research",web_research)
graph_builder.add_node("reflection",reflection)
graph_builder.add_node("finalize_answer",finalize_answer)


# ==========================================
# Define Edges
# ==========================================

graph_builder.add_edge(START, "generate_queries")  
graph_builder.add_conditional_edges(
    "generate_queries", continue_to_web_research, ["web_research"]
)
graph_builder.add_edge('web_research','reflection')
graph_builder.add_conditional_edges(
    "reflection", evaluate_research, ["web_research", "finalize_answer"]
)
graph_builder.add_edge("web_research", END)

# ==========================================
# Compile The Graph
# ==========================================

graph = graph_builder.compile()
