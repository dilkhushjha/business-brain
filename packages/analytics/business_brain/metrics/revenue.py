from .base import Metric
class RevenueMetric(Metric):
    name = "revenue"
    def calculate(self, context): return context.sales_amount
