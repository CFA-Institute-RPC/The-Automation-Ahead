# Sustainability Research Agent

An AI-powered research agent for conducting comprehensive research tailored to sustainability screening using LangGraph.

## Key Features

- **LangGraph State Management**: Robust workflow orchestration with state tracking
- **Multi-Model AI**: Leverages both Gemini and OpenAI models for different tasks
- **Intelligent Query Generation**: AI-powered research query formulation
- **Web Research Integration**: Automated information gathering and validation
- **Reflection & Analysis**: Multi-pass analysis with quality assurance
- **Configurable Research Depth**: Adjustable query count and research iterations

## Prerequisites

### API Keys Required
- **Google Gemini API Key**: Set `GOOGLE_API_KEY` for query generation (primary model)
- **OpenAI API Key**: Set `OPENAI_API_KEY` for reflection and reasoning models

### Dependencies
```bash
pip install langgraph langchain-google-genai langchain-openai pydantic python-dotenv
```

## Quick Start

### From the Jupyter Notebook

Open `research_agent.ipynb` to see a complete demonstration of the agent, including:
- Configuration setup and model selection
- Step-by-step research workflow execution
- ESG analysis examples with real companies
- Output formatting and interpretation

### Programmatic Usage

```python
from graph import graph_builder
from configuration import Configuration
from state import OverallState

# Configure the agent
config = Configuration(
    query_generator_model="gemini-2.0-flash",
    reflection_model="gpt-5-nano-2025-08-07", 
    reasoning_model="gpt-5-mini-2025-08-07",
    number_of_initial_queries=3
)

# Initialize research state
initial_state = OverallState(
    research_question="What are Tesla's current sustainability initiatives and ESG performance?",
    queries=[],
    research_results=[],
    reflection="",
    final_answer=""
)

# Execute research workflow
result = graph_builder.compile().invoke(initial_state, config={"configurable": config.dict()})
```

## Architecture Components

### Core Modules

- **`graph.py`**: LangGraph workflow definition and node connections
- **`nodes.py`**: Individual workflow nodes (query generation, research, reflection, etc.)
- **`state.py`**: State management classes and data structures
- **`configuration.py`**: Agent configuration and model settings
- **`tools_and_schemas.py`**: Research tools and structured output schemas
- **`prompts.py`**: AI prompt templates for different workflow stages
- **`utils.py`**: Utility functions for data processing and formatting

### Workflow Nodes

1. **Generate Queries**: AI-powered research query formulation
2. **Web Research**: Automated information gathering and validation
3. **Reflection**: Quality assurance and analysis validation
4. **Finalize Answer**: Comprehensive report generation

## Configuration Options

### Model Selection
- **Query Generator**: Gemini 2.0 Flash (default) for research planning
- **Reflection Model**: GPT-5 Nano for analysis validation  
- **Reasoning Model**: GPT-5 Mini for complex analysis tasks

### Research Parameters
- **Initial Query Count**: Number of research queries to generate (default: 3)
- **Research Depth**: Configurable iteration levels
- **Output Format**: Structured reporting with customizable templates

## Usage Examples

### ESG Analysis
```python
research_question = "Analyze Microsoft's carbon neutrality commitments and progress"
```

### Sustainability Screening
```python
research_question = "Compare renewable energy adoption across major tech companies"
```

### Impact Assessment
```python
research_question = "Evaluate the social impact of supply chain practices in the fashion industry"
```

## Output Format

The agent produces structured reports including:
- **Executive Summary**: Key findings and recommendations
- **Detailed Analysis**: Comprehensive research results with sources
- **ESG Metrics**: Quantitative sustainability indicators where available
- **Risk Assessment**: Potential sustainability-related risks and opportunities
- **Sources**: Referenced materials and validation information

## Usage Notes

- Adapted from [Google Gemini's LangGraph Research Agent](https://github.com/google-gemini/gemini-fullstack-langgraph-quickstart)
- Requires active internet connection for web research capabilities
- API costs scale with research depth and complexity
- Results quality improves with more specific, focused research questions
- Built-in logging tracks research progress and debugging information
