from decimal import Decimal


def _money(value):
    if value is None:
        return "n/a"
    return f"₹{Decimal(str(value)):,.2f}"


def render_grounded_response(question: str, intent: str, context: dict) -> tuple[str, str]:
    """Return (answer, confidence). confidence is "grounded" only when the
    answer is actually backed by retrieved evidence, and "insufficient_evidence"
    when we had to say we don't know yet -- the caller should never report
    "grounded" for an answer that admits it has no evidence."""
    evidence = context.get("evidence", [])
    signals = context.get("signals", [])
    recommendations = context.get("recommendations", [])
    grounded = False

    if intent == "business_health":
        revenue = next((item for item in evidence if item.get("metric") == "revenue"), None)
        if revenue:
            grounded = True
            change = revenue.get("metadata", {}).get("change")
            answer = f"Your current-month revenue is {_money(revenue.get('value'))}."
            if change is not None:
                # change is a percentage value already (e.g. "-15" for -15%),
                # not a 0-1 ratio -- do not run it through ":.1%" formatting.
                answer += f" Compared with the baseline period, it changed by {Decimal(str(change)):.1f}%."
        else:
            answer = "I don't have enough sales evidence to assess overall business health yet."
    elif intent == "sales_performance":
        revenue = next((item for item in evidence if item.get("metric") == "revenue"), None)
        if revenue:
            grounded = True
            answer = f"Current-month revenue is {_money(revenue.get('value'))}."
        else:
            answer = "I don't have enough sales evidence yet."
    else:
        answer = "I can answer this once the relevant business evidence is available."

    if signals:
        answer += f" I detected {len(signals)} business signal(s) that may need attention."
    if recommendations:
        answer += f" There are {len(recommendations)} evidence-backed recommendation(s) available."
    return answer, "grounded" if grounded else "insufficient_evidence"
