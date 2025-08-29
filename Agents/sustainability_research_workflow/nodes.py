
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
import os
from google.genai import Client
from langgraph.types import Send
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from logging_decorator import log_node_execution, log_node
from utils import (
    get_citations,
    insert_citation_markers,
    get_research_topic, 
    get_current_date,
    resolve_urls
)
from prompts import (
    query_writer_instructions,
    web_searcher_instructions,
    reflection_instructions,
    answer_instructions,
)

from tools_and_schemas import (
    SearchQueryList, 
    Reflection,
)
from state import (
    OverallState, 
    QueryGenerationState,
    WebSearchState,
    ReflectionState,
)
from configuration import Configuration

genai_client = Client(api_key=os.getenv("GEMINI_API_KEY"))

@log_node_execution("🔍 Query Generation")
def generate_queries(state: OverallState, config: RunnableConfig) -> QueryGenerationState:
    """LangGraph node that generates search queries based on the User's question.

    Uses Gemini 2.0 Flash to create an optimized search query for web research based on
    the User's question.

    Args:
        state: Current graph state containing the User's question
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including search_query key containing the generated query
    """
    # Get configurable values
    configurable = Configuration.from_runnable_config(config)
    model = configurable.query_generator_model
    
    # check for custom initial search query count
    if state.get("initial_search_query_count") is None:
        state["initial_search_query_count"] = configurable.number_of_initial_queries or 3

    if 'gemini' in model.lower():
        llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=0,
            max_retries=2,
            api_key=os.getenv("GEMINI_API_KEY"),
        )
    elif ('gpt' in model.lower()) | ('o3' in model.lower()) | ('o4' in model.lower()) | ('o1' in model.lower()):
        llm = ChatOpenAI(
            model=model,
            temperature=1,
            max_retries=2,
            api_key=os.getenv("OPENAI_API_KEY")
        )

    structured_llm = llm.with_structured_output(SearchQueryList)

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = query_writer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        number_queries=state["initial_search_query_count"],
    )
    # Generate the search queries
    result = structured_llm.invoke(formatted_prompt)
    return {"query_list": result.query}

@log_node_execution("🌐 Web Research")
def web_research(state: WebSearchState, config: RunnableConfig) -> OverallState:
    """LangGraph node that performs web research using the native Google Search API tool.

    Executes a web search using the native Google Search API tool in combination with Gemini 2.0 Flash.

    Args:
        state: Current graph state containing the search query and research loop count
        config: Configuration for the runnable, including search API settings

    Returns:
        Dictionary with state update, including sources_gathered, research_loop_count, and web_research_results
    """
    # Get configurable values
    configurable = Configuration.from_runnable_config(config)
    
    # Configure
    formatted_prompt = web_searcher_instructions.format(
        current_date=get_current_date(),
        research_topic=state["search_query"],
    )
    
    # Get model name and ensure it works with Google Search
    model = configurable.query_generator_model or 'gemini-2.0-flash'

    if 'gemini' not in model:
        print("Model not supported for search. Defaulting to google model.")
        model = 'gemini-2.0-flash'
    
    # # For Google GenAI native client, use a model that supports search
    # if model == 'gemini-2.0-flash':
    #     model = 'models/gemini-2.0-flash-exp'  # Use experimental version that supports search
    # elif not model.startswith('models/'):
    #     model = f'models/{model}'

    # Uses the google genai client as the langchain client doesn't return grounding metadata
    response = genai_client.models.generate_content(
        model=model,
        contents=formatted_prompt,
        config={
            "tools": [{"google_search": {}}],
            "temperature": 0,
        },
    )
    # resolve the urls to short urls for saving tokens and time
    resolved_urls = resolve_urls(
        response.candidates[0].grounding_metadata.grounding_chunks, state["id"]
    )

    # Gets the citations and adds them to the generated text
    citations = get_citations(response,resolved_urls)
    modified_text = insert_citation_markers(response.text, citations)
    sources_gathered = [item for citation in citations for item in citation["segments"]]

    return {
        "sources_gathered": sources_gathered,
        "search_query": [state["search_query"]],
        "web_research_result": [modified_text],
    }

@log_node_execution("🤔 Reflection")
def reflection(state: OverallState, config: RunnableConfig) -> ReflectionState:
    """LangGraph node that identifies knowledge gaps and generates potential follow-up queries.

    Analyzes the current summary to identify areas for further research and generates
    potential follow-up queries. Uses structured output to extract
    the follow-up query in JSON format.

    Args:
        state: Current graph state containing the running summary and research topic
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including search_query key containing the generated follow-up query
    """
    configurable = Configuration.from_runnable_config(config)
    # Increment the research loop count and get the reasoning model
    state["research_loop_count"] = state.get("research_loop_count", 0) + 1
    reasoning_model = configurable.reasoning_model or {}

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = reflection_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n\n---\n\n".join(state["web_research_result"]),
    )
    if 'gemini' in reasoning_model.lower():
        llm = ChatGoogleGenerativeAI(
            model=reasoning_model,
            temperature=0,
            max_retries=2,
            api_key=os.getenv("GEMINI_API_KEY"),
        )
    elif ('gpt' in reasoning_model.lower()) | ('o3' in reasoning_model.lower()) | ('o4' in reasoning_model.lower()) | ('o1' in reasoning_model.lower()):
        llm = ChatOpenAI(
            model=reasoning_model,
            temperature=1,
            max_retries=2,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
    result = llm.with_structured_output(Reflection).invoke(formatted_prompt)

    return {
        "is_sufficient": result.is_sufficient,
        "knowledge_gap": result.knowledge_gap,
        "follow_up_queries": result.follow_up_queries,
        "research_loop_count": state["research_loop_count"],
        "number_of_ran_queries": len(state["search_query"]),
    }

@log_node_execution("📋 Finalize Answer")
def finalize_answer(state: OverallState, config: RunnableConfig) -> OverallState:
    """LangGraph node that finalizes the research summary.

    Prepares the final output by combining research results into a well-structured
    research report with proper citations and working markdown links.

    Args:
        state: Current graph state containing the running summary and sources gathered

    Returns:
        Dictionary with state update, including the final answer with working citations
    """
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = configurable.reasoning_model or {}

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = answer_instructions.format(
        current_date=current_date,
        users_question=state['messages'][0],
        research_topic=get_research_topic(state["messages"]),
        summaries="\n---\n\n".join(state["web_research_result"]),
    )

    if 'gemini' in reasoning_model.lower():
        llm = ChatGoogleGenerativeAI(
            model=reasoning_model,
            temperature=0,
            max_retries=2,
            api_key=os.getenv("GEMINI_API_KEY"),
        )
    elif ('gpt' in reasoning_model.lower()) | ('o3' in reasoning_model.lower()) | ('o4' in reasoning_model.lower()) | ('o1' in reasoning_model.lower()):
        llm = ChatOpenAI(
            model=reasoning_model,
            temperature=1,
            max_retries=2,
            api_key=os.getenv("OPENAI_API_KEY")
        )
    else:
        "Model not supported. Only use Google or OpenAI models."

    result = llm.invoke(formatted_prompt)

    # Collect unique sources that are actually used in the final content
    unique_sources = []
    for source in state["sources_gathered"]:
        if source["short_url"] in result.content:
            result.content = result.content.replace(
                f'({source["short_url"]})', f'({source["value"]})'
            )
            unique_sources.append(source)

    return {
        "messages": [AIMessage(content=result.content)],
        "sources_used": unique_sources,
    }

# ==========================================
# CONDITIONAL EDGES
# ==========================================

@log_node
def continue_to_web_research(state: QueryGenerationState):
    """LangGraph node that sends the search queries to the web research node.

    This is used to spawn n number of web research nodes, one for each search query.
    """
    return [
        Send("web_research", {"search_query": search_query, "id": int(idx)})
        for idx, search_query in enumerate(state["query_list"])
    ]

@log_node
def evaluate_research(
    state: ReflectionState,
    config: RunnableConfig,
) -> OverallState:
    """LangGraph routing function that determines the next step in the research flow.

    Controls the research loop by deciding whether to continue gathering information
    or to finalize the summary based on the configured maximum number of research loops.

    Args:
        state: Current graph state containing the research loop count
        config: Configuration for the runnable, including max_research_loops setting

    Returns:
        String literal indicating the next node to visit ("web_research" or "finalize_summary")
    """
    configurable = Configuration.from_runnable_config(config)
    max_research_loops = (
        state.get("max_research_loops")
        if state.get("max_research_loops") is not None
        else configurable.max_research_loops
    )
    if state["is_sufficient"] or state["research_loop_count"] >= max_research_loops:
        return "finalize_answer"
    else:
        return [
            Send(
                "web_research",
                {
                    "search_query": follow_up_query,
                    "id": state["number_of_ran_queries"] + int(idx),
                },
            )
            for idx, follow_up_query in enumerate(state["follow_up_queries"])
        ]
