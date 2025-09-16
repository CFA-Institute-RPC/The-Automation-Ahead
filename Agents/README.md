# Agents Directory

This directory contains the code for the Agentic AI in Finance case studies for [**Agentic AI For Finance: Workflows, Tips, and Case Studies**](https://rpc.cfainstitute.org/research/the-automation-ahead-content-series/agentic-ai-for-finance#4257225834-1376932270).

## Getting Started

### Prerequisites

Before running any notebooks in this directory, you'll need to obtain API keys for:

- **OpenAI API**: Required for GPT models used throughout the regime screening and sustainability workflows. Go [here](https://platform.openai.com/api-keys) to create an OpenaAI api key.
- **Google Gemini API**: Required for Gemini models used in the sustainability research workflow. Go [here](https://aistudio.google.com/apikey) to create a Gemini API Key.


## Main Case Study

### Agent-Augmented Portfolio Construction Case Study

Run in Colab: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1RAjncZkUlsDZSDj2r8uMa3w9OCw8YsK8?usp=sharing)

**File**: `Agent-Augmented Portfolio Construction - Case Study.ipynb`

This is the **primary entry point** and comprehensive case study that demonstrates how Agentic workflows can enhance traditional portfolio construction processes. The notebook showcases:

- Integration of agentic workflows for financial screening aligned to forecased economic regimes
- Automated research and sustianability screening 
- Data-driven portfolio optimization techniques
- Real-world application of agent-augmented investment strategies

**Start here** if you want to understand the full workflow and see how all the agents work together in practice.

## Individual Workflow Deep Dives

If you want to examine the inner workings of specific agents, you can explore these individual agentic workflow directories:

### Regime Screening Agentic Workflow

**Directory**: `regime_screening_workflow/`  
**Notebook**: `regime_screening_workflow/regime_screening_workflow.ipynb`

This workflow specializes in:
- Running financial screening based on user defined economic regime focecasts and predifined metric criteria tailored for different regimes and sectors.
- ReAct Agent based data validation. 


### Sustainability Research Agentic Workflow  

**Directory**: `sustainability_research_workflow/`  
**Notebook**: `sustainability_research_workflow/research_workflow.ipynb`

This workflow focuses on:
- Running deep research on any topic
- The use case is tailored to sustainability research screening

## Recommended Learning Path

1. **Start with the Case Study**: Open `Agent-Augmented Portfolio Construction - Case Study.ipynb` to see the complete workflow
2. **Explore Individual Agents**: Dive into the specific agent notebooks to understand implementation details

