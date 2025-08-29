# Regime Aligned Fundamental Screener

This agentic workflow is designed to assess whether current economic conditions are favorable for a specific company, based on fundamental financial criteria. It introduces an economic regime-aware screening process, using a prompt-chaining structure and optional human-in-the-loop inputs. This use case demonstrates how reasoning-capable LLM agents can blend macroeconomic awareness, financial data retrieval, and conditional logic to generate informed assessments.

## Workflow Summary

This use case follows a **router workflow pattern**, with regime-specific branching. It can be broken down into the following steps:

1. **Get Ticker** 
2. **Pull Financial Data**
3. **Route to Economic Regime**
4. **Calculate Regime-Specific Metrics**
5. **Provide Data Validation Commentary using React Agent** 
6. **Evaluation against Criteria and Provide Score**

Each step can be more or less autonomous, depending on user preference.

![Economic Regime Fundamentals](../assets/svgs/economic_regime_fundamentals.drawio.svg)

## Key Features

- **LlamaIndex Integration**: Used LlamaIndex workflows and agents to automate fundamental stock screening 
- **Workflow Demonstration**: Uses the the routing, and parellel processing workflows to demonstrate their use with financial data.
- **React Agent Demonstration**: Demostration of the use of react agents to cross-validate data accuracy from a predefined outlier table. 

## Workflow Summary

This use case follows a router workflow pattern, with regime-specific branching. Steps:
	1.	Get Ticker
	2.	Pull Financial Data
	3.	Route to Economic Regime
	4.	Calculate Regime-Specific Metrics
	5.	Provide Data Validation Commentary
	6.	Generate Scored Assessment

## Prerequisites

### API Keys Required
- **OpenAI API Key**: Set `OPENAI_API_KEY` in your environment for LLM validation and scoring steps

### Dependencies
```bash
pip install pydantic pandas numpy yfinance llama-index python-dotenv
```

## Quick Start

### From the Jupyter Notebook

Open `regime_screening_agent.ipynb` to see a complete walkthrough of the agentic workflow.

### Usage

#### Single Ticker Workflow

```python
import sys, os
sys.path.append(os.path.abspath(".."))

from regime_screening_agent import RegimeScreeningWorkflow, ParallelRegimeScreeningWorkflow
from regime_state import RegimeScreeningWorkflowState

async def main():
    w = RegimeScreeningWorkflow(timeout=600, verbose=True)

    handler = w.run() 

    async for ev in handler.stream_events():
        if isinstance(ev, InputRequiredEvent):
            user_text = input(ev.prefix if ev.prefix else "Enter value: ")
            handler.ctx.send_event(HumanResponseEvent(response=user_text))

    result = await handler

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

#### Multi-ticker Workflow
```python
async def main():
from regime_workflows import ParallelRegimeScreeningWorkflow
from llama_index.core.workflow import InputRequiredEvent,HumanResponseEvent
w = ParallelRegimeScreeningWorkflow(timeout=600, verbose=True)

handler = w.run()  

async for ev in handler.stream_events():
    if isinstance(ev, InputRequiredEvent):
        user_text = input(ev.prefix if ev.prefix else "Enter value: ")
        handler.ctx.send_event(HumanResponseEvent(response=user_text))

result = await handler

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Core Components

- **`regime_workflows.py`**: Main workflow definitions and execution logic
- **`regime_state.py`**: State management for workflow data
- **`metrics.py`**: Financial metrics calculation functions
- **`evaluation_tables.py`**: LLM scoring criteria and validation tables
- **`regime_utils.py`**: Utility functions for data processing
- **`events.py`**: Workflow event handling



