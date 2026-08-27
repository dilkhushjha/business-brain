import re


def classify_intent(question: str) -> str:
    text = question.lower().strip()
    if any(term in text for term in ("how is my business", "business doing", "overall performance", "overall health")):
        return "business_health"
    if any(term in text for term in ("revenue", "sales", "turnover")):
        return "sales_performance"
    if any(term in text for term in ("customer", "client")):
        return "customer_analysis"
    if any(term in text for term in ("product", "item", "sku")):
        return "product_analysis"
    if any(term in text for term in ("why", "reason", "caused", "cause")):
        return "root_cause"
    return "general_business"
