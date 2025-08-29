from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableConfig
from typing import Any, Optional
import os

class Configuration(BaseModel):
    """The configuration for the agent."""

    # Must be a google model
    query_generator_model: str = Field(
        default="gemini-2.0-flash",
        metadata={
            "description": "The name of the language model to use for the agent's query generation."
        },
    )

    reflection_model: str = Field(
        default="gpt-5-nano-2025-08-07",
        metadata={
            "description": "The name of the language model to use for the agent's reflection."
        },
    )

    reasoning_model: str = Field(
        default='gpt-5-mini-2025-08-07',
        metadata={"description": "The reasoning model for complex analysis."},
    )

    number_of_initial_queries: int = Field(
        default=3,
        metadata={"description": "The number of initial search queries to generate."},
    )

    max_research_loops: int = Field(
        default=2,
        metadata={"description": "The maximum number of research loops to perform."},
    )
    
    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )

        # Get raw values from environment or config
        raw_values: dict[str, Any] = {
            name: os.environ.get(name.upper(), configurable.get(name))
            for name in cls.model_fields.keys()
        }

        # Filter out None values
        values = {k: v for k, v in raw_values.items() if v is not None}

        return cls(**values)

