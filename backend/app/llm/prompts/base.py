"""
DSRA V2 — Base Prompt Class
============================
Defines standard format protocols for versioned, typed system prompts.
"""

from abc import ABC, abstractmethod


class BasePrompt(ABC):
    """
    Abstract base for all structured LLM prompts.
    Forces subclassing prompts to return version and system templates.
    """

    @property
    @abstractmethod
    def version(self) -> str:
        """Version of the prompt template (e.g. '1.0.0')."""
        pass

    @property
    @abstractmethod
    def system_template(self) -> str:
        """The core instructions for the LLM system message."""
        pass
