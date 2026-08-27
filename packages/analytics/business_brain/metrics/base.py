from abc import ABC, abstractmethod
class Metric(ABC):
    name: str
    @abstractmethod
    def calculate(self, context): raise NotImplementedError
