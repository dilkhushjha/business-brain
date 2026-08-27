from decimal import Decimal


def _money(value):
    if value is None:
        return "n/a"
    return f"₹{Decimal(str(value)):,.2f}"


def render_grounded_response(question: str, intent: str, context: dict) -> str:
    evidence = context.get("evidence", [])
    signals = context.get("signals", [])
    recommendations = context.get("recommendations", [])

    if intent == "business_health":
        revenue = next((item for item in evidence if item.get("metric") == "revenue"), None)
        if revenue:
            change = revenue.get("metadata", {}).get("change")
            answer = f"Your current-month revenue is {_money(revenue.get('value'))}."
            if change is not None:
                answer += f" Compared with the baseline period, it changed by {Decimal(str(change)):.1%}."
        else:
            answer = "I don't have enough sales evidence to assess overall business health yet."
    elif intent == "sales_performance":
        revenue = next((item for item in evidence if item.get("metric") == "revenue"), None)
        answer = f"Current-month revenue is {_money(revenue.get('value'))}." if revenue else "I don't have enough sales evidence yet."
    else:
        answer = "I can answer this once the relevant business evidence is available."

    if signals:
        answer += f" I detected {len(signals)} business signal(s) that may need attention."
    if recommendations:
        answer += f" There are {len(recommendations)} evidence-backed recommendation(s) available."
    return answer
