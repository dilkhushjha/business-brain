from ..base import PredictionModel
class CustomerRiskModel(PredictionModel):
    def fit(self, data): raise NotImplementedError
    def predict(self, data): raise NotImplementedError
