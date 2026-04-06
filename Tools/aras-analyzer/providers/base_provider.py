from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """
    Abstract base class for all LLM providers.
    Every provider implements call() — the rest of the system
    always goes through llm_client.py which resolves the provider from config.
    """

    @abstractmethod
    def call(self, system_prompt: str, user_prompt: str) -> str:
        """Send a prompt to the LLM and return the raw text response."""
        pass

    def name(self) -> str:
        return self.__class__.__name__.replace("Provider", "").lower()
