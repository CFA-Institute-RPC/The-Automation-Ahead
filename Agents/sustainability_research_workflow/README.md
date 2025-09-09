# Deep Research Sustainability Screening Workflow
This agent uses a hybrid Parallelization and Evaluator–Optimizer workflow pattern to perform deep research on a company’s adoption of innovative sustainable technologies. It enables investment teams to assess sustainability leadership using dynamic, internet-scale data.

## Workflow Structure
![sustainability screening workflow](../assets/svgs/sustainability_screening.drawio.svg)

## Prerequisites

### API Keys Required
- **Google Gemini API Key**: Set `GOOGLE_API_KEY` for query generation (primary model)
- **OpenAI API Key**: Set `OPENAI_API_KEY` for reflection and reasoning models

### Dependencies
```bash
pip pip install langgraph langchain-google-genai langchain-openai pydantic python-dotenv langchain-core google-genai 
```

## Quick Start

### From the Jupyter Notebook

Open `research_workflow.ipynb` to see a complete demonstration of the agent, including:
- Configuration setup and model selection
- Step-by-step research workflow execution

### Usage

```python
import sys
import os
from configuration import Configuration
from graph import graph

# Add research_workflow to path
sys.path.insert(0, os.path.join(os.getcwd(), 'sustainability_research_workflow'))

config = Configuration

state = graph.invoke(
        {"messages": [{"role": "user", "content": formated_prompt}]}
    )
report = state["messages"][-1].content
```

## Core Components

### Core Modules

- **`graph.py`**: LangGraph workflow definition and node connections
- **`nodes.py`**: Individual workflow nodes (query generation, research, reflection, etc.)
- **`state.py`**: State management classes and data structures
- **`configuration.py`**: Agent configuration and model settings
- **`tools_and_schemas.py`**: Research tools and structured output schemas
- **`prompts.py`**: AI prompt templates for different workflow stages
- **`utils.py`**: Utility functions for data processing and formatting


## Usage Notes

- Adapted from [Google Gemini's LangGraph Research Agent](https://github.com/google-gemini/gemini-fullstack-langgraph-quickstart)

