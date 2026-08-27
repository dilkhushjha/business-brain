from abc import ABC, abstractmethod
class PredictionModel(ABC):
    @abstractmethod
    def fit(self, data): raise NotImplementedError
    @abstractmethod
    def predict(self, data): raise NotImplementedError
