from ..base import PredictionModel
class DemandForecastModel(PredictionModel):
    def fit(self, data): raise NotImplementedError
    def predict(self, data): raise NotImplementedError
