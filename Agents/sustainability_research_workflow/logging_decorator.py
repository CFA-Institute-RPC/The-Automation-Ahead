# logging_decorator.py - Enhanced debugging for research agent

import functools
import logging
import time
import json
from datetime import datetime
from typing import Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('research_agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('research_agent')

def safe_truncate(text: str, max_length: int = 200) -> str:
    """Safely truncate text for logging"""
    if not text:
        return "None"
    text = str(text)
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def log_node_execution(node_name: str = None):
    """
    Enhanced decorator to log research agent node execution with detailed content
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get node name
            name = node_name or func.__name__
            
            # Extract state info for logging (safely)
            state_info = {}
            if args and isinstance(args[0], dict):
                state = args[0]
                
                # Detailed state logging
                messages = state.get('messages', [])
                search_queries = state.get('search_query', [])
                research_results = state.get('web_research_result', [])
                sources = state.get('sources_gathered', [])
                
                state_info = {
                    'search_queries_count': len(search_queries),
                    'research_results_count': len(research_results),
                    'sources_count': len(sources),
                    'research_loop': state.get('research_loop_count', 0),
                    'messages_count': len(messages)
                }
                
                # Log actual content for debugging
                logger.info(f"🚀 Starting {name}")
                logger.info(f"   State Counts: {state_info}")
                
                # Show recent queries if any
                if search_queries:
                    logger.info(f"   Recent Queries: {search_queries[-3:]}")
                
                # Show input message if it's the start
                if messages and name == "🔍 Query Generation":
                    last_msg = messages[-1]
                    if hasattr(last_msg, 'content'):
                        logger.info(f"   Input Query: {safe_truncate(last_msg.content, 300)}")
                
                # Show research results summary if available
                if research_results and name in ["🤔 Reflection", "📋 Finalize Answer"]:
                    logger.info(f"   Research Results Available: {len(research_results)} summaries")
                    for i, result in enumerate(research_results[-2:]):  # Show last 2
                        logger.info(f"     Summary {i+1}: {safe_truncate(result, 150)}")
            
            start_time = time.time()
            
            try:
                # Log when starting model calls
                if name in ["🔍 Query Generation", "🤔 Reflection", "📋 Finalize Answer"]:
                    logger.info(f"🤖 {name}: Starting LLM call...")
                elif name == "🌐 Web Research":
                    if args and isinstance(args[0], dict):
                        query = args[0].get('search_query', 'Unknown query')
                        logger.info(f"🌐 {name}: Searching for '{safe_truncate(query, 100)}'")
                
                # Execute the function
                result = func(*args, **kwargs)
                
                # Log success with timing
                execution_time = time.time() - start_time
                logger.info(f"✅ Completed {name} in {execution_time:.2f}s")
                
                # Log detailed result info
                if isinstance(result, dict):
                    result_info = {}
                    
                    # Query generation results
                    if 'query_list' in result:
                        queries = result['query_list']
                        result_info['queries_generated'] = len(queries)
                        logger.info(f"   Generated Queries: {queries}")
                    
                    # Web research results
                    if 'web_research_result' in result:
                        research = result['web_research_result']
                        result_info['research_results'] = len(research)
                        if research:
                            logger.info(f"   Research Result Preview: {safe_truncate(research[0], 200)}")
                    
                    # Sources gathered
                    if 'sources_gathered' in result:
                        sources = result['sources_gathered']
                        result_info['new_sources'] = len(sources)
                        if sources:
                            source_labels = [s.get('label', 'Unknown') for s in sources[:5]]
                            logger.info(f"   New Sources: {source_labels}")
                    
                    # Reflection results
                    if 'is_sufficient' in result:
                        result_info['research_sufficient'] = result['is_sufficient']
                        if 'knowledge_gap' in result:
                            logger.info(f"   Knowledge Gap: {safe_truncate(result['knowledge_gap'], 150)}")
                        if 'follow_up_queries' in result:
                            follow_ups = result['follow_up_queries']
                            result_info['follow_up_queries'] = len(follow_ups)
                            logger.info(f"   Follow-up Queries: {follow_ups}")
                    
                    # Final answer
                    if 'messages' in result:
                        messages = result['messages']
                        if messages and hasattr(messages[0], 'content'):
                            content = messages[0].content
                            logger.info(f"   Final Answer Preview: {safe_truncate(content, 300)}")
                            logger.info(f"   Final Answer Length: {len(content)} characters")
                    
                    if result_info:
                        logger.info(f"   Result Summary: {result_info}")
                
                return result
                
            except Exception as e:
                # Log detailed error
                execution_time = time.time() - start_time
                logger.error(f"❌ Failed {name} after {execution_time:.2f}s")
                logger.error(f"   Error Type: {type(e).__name__}")
                logger.error(f"   Error Message: {str(e)}")
                logger.error(f"   Args: {[type(arg).__name__ for arg in args]}")
                raise
        
        return wrapper
    return decorator

def log_node(func):
    """Simple decorator that uses function name"""
    return log_node_execution()(func)

def log_model_call(model_name: str, prompt_preview: str = "", max_length: int = 200):
    """Log model calls with timing"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"🤖 MODEL CALL: {model_name}")
            if prompt_preview:
                logger.info(f"   Prompt Preview: {safe_truncate(prompt_preview, max_length)}")
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"✅ MODEL RESPONSE: {model_name} completed in {duration:.2f}s")
                
                # Log response preview if possible
                if hasattr(result, 'content'):
                    logger.info(f"   Response Preview: {safe_truncate(result.content, 200)}")
                elif hasattr(result, 'text'):
                    logger.info(f"   Response Preview: {safe_truncate(result.text, 200)}")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"❌ MODEL ERROR: {model_name} failed after {duration:.2f}s: {str(e)}")
                raise
        return wrapper
    return decorator

# Debug function to dump full state
def debug_state(state: dict, node_name: str = "Unknown"):
    """Dump full state for debugging"""
    logger.info(f"🔍 DEBUG STATE at {node_name}:")
    logger.info(f"   Keys: {list(state.keys())}")
    
    for key, value in state.items():
        if key == 'messages':
            logger.info(f"   {key}: {len(value)} messages")
            for i, msg in enumerate(value):
                if hasattr(msg, 'content'):
                    logger.info(f"     Message {i}: {safe_truncate(msg.content, 100)}")
        elif key in ['search_query', 'web_research_result', 'sources_gathered']:
            logger.info(f"   {key}: {len(value) if isinstance(value, list) else 'Not a list'} items")
            if isinstance(value, list) and value:
                logger.info(f"     Latest: {safe_truncate(str(value[-1]), 100)}")
        else:
            logger.info(f"   {key}: {safe_truncate(str(value), 50)}")

# Performance monitoring
def log_performance_warning(duration: float, threshold: float = 30.0, operation: str = "Operation"):
    """Log performance warnings for slow operations"""
    if duration > threshold:
        logger.warning(f"⚠️  SLOW {operation}: {duration:.2f}s (threshold: {threshold}s)")

# Set log level
def set_research_log_level(level: str = "INFO"):
    """Set logging level: DEBUG, INFO, WARNING, ERROR"""
    logger.setLevel(getattr(logging, level.upper()))
    logger.info(f"🔧 Research agent logging set to {level.upper()}")
