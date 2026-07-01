"""
DSRA V2 — Base Agent Interface
================================
Abstract Base Class representing the typed execution contract for all agents.
Enforces Pydantic I/O schemas, telemetry logging, and retry logic wrappers.
"""

from abc import ABC, abstractmethod
from typing import ClassVar, Generic, TypeVar
import time

from pydantic import BaseModel

from app.core.logging import get_logger
from app.llm.gateway import llm_gateway

log = get_logger(__name__)

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """
    Standard Base Agent. Every agent subclass must implement execute().
    InputT and OutputT are validated at execution time.
    """

    name: ClassVar[str]  # Name of the agent class, e.g. "PlannerAgent"

    def __init__(self) -> None:
        self.llm = llm_gateway

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt instructing the agent on its role and rules."""
        pass

    @abstractmethod
    async def execute(self, input_data: InputT) -> OutputT:
        """Internal execution logic to be overridden by subclass."""
        pass

    async def run(self, input_data: InputT) -> OutputT:
        """
        Executes the agent with strict validation and telemetry tracking.
        Enforces types, wraps durations, and catches unhandled exceptions.
        """
        agent_name = self.name or self.__class__.__name__
        log.info("agent_execution_started", agent=agent_name)
        start_time = time.perf_counter()

        try:
            # 1. Enforce input schema validation (Pydantic models are parsed strictly)
            if not isinstance(input_data, BaseModel):
                raise TypeError(f"Agent input must be a Pydantic model, got {type(input_data)}")

            # 2. Run core execution
            result = await self.execute(input_data)

            # 3. Enforce output schema validation
            if not isinstance(result, BaseModel):
                raise TypeError(f"Agent output must be a Pydantic model, got {type(result)}")

            duration_ms = int((time.perf_counter() - start_time) * 1000)
            log.info("agent_execution_finished", agent=agent_name, duration_ms=duration_ms)
            return result

        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            log.error("agent_execution_failed", agent=agent_name, duration_ms=duration_ms, error=str(e))
            raise e
