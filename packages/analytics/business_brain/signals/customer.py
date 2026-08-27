from .base import Signal
from packages.domain.business_brain.enums.severity import Severity
def declining_customer(customer_id: str, current: float, baseline: float) -> Signal | None:
    if baseline <= 0 or current >= baseline * 0.7: return None
    confidence = min(0.99, 0.5 + (1 - current / baseline) * 0.5)
    return Signal("CUSTOMER_REVENUE_DECLINE", Severity.HIGH, confidence, customer_id,
                  [{"metric":"revenue","current":current,"baseline":baseline}])
