import re


def classify_intent(question: str) -> str:
    """Keyword-based intent classification. Order matters: more specific
    categories (margin, receivables, payables, suppliers) are checked before
    the broader ones they could otherwise be swallowed by (e.g. "why is my
    margin low" must hit margin_analysis, not fall through to root_cause;
    "what do my customers owe me" should hit receivables_analysis, not
    customer_analysis). This is still pattern matching, not real language
    understanding -- a question that doesn't use any of these words won't
    be recognized even if a human would obviously know what it's asking."""
    text = question.lower().strip()
    if any(term in text for term in ("how is my business", "business doing", "overall performance", "overall health")):
        return "business_health"
    if any(term in text for term in ("margin", "profit", "profitability", "gross profit")):
        return "margin_analysis"
    if any(term in text for term in ("receivable", "outstanding payment", "who owes me", "unpaid invoice", "money owed to me", "collections")):
        return "receivables_analysis"
    if any(term in text for term in ("payable", "what do i owe", "bills due", "bills", "supplier payment", "vendor payment", "money i owe")):
        return "payables_analysis"
    if any(term in text for term in ("supplier", "vendor", "procurement", "purchase cost")):
        return "supplier_analysis"
    if any(term in text for term in ("expense", "expenses", "overhead", "operating cost", "running cost", "spending")):
        return "expense_analysis"
    if any(term in text for term in ("revenue", "sales", "turnover")):
        return "sales_performance"
    if any(term in text for term in ("customer", "client")):
        return "customer_analysis"
    if any(term in text for term in ("product", "item", "sku", "inventory", "stock")):
        return "product_analysis"
    if any(term in text for term in ("why", "reason", "caused", "cause")):
        return "root_cause"
    return "general_business"
