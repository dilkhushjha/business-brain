from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
class DataSourceAdapter(ABC):
    @abstractmethod
    def inspect(self, path: Path) -> dict[str, Any]: raise NotImplementedError
    @abstractmethod
    def ingest(self, path: Path) -> list[dict[str, Any]]: raise NotImplementedError
