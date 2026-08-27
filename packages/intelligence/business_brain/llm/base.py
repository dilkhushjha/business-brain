from abc import ABC, abstractmethod
from typing import Any
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, messages: list[dict[str, str]], response_schema: dict[str, Any] | None = None) -> Any:
        raise NotImplementedError
