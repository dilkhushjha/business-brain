from decimal import Decimal


def _money(value):
    if value is None:
        return "n/a"
    return f"₹{Decimal(str(value)):,.2f}"


def _evidence_for(evidence: list[dict], metric: str) -> dict | None:
    return next((item for item in evidence if item.get("metric") == metric), None)


def _signals_with_codes(signals: list[dict], codes: set[str]) -> list[dict]:
    return [s for s in signals if s.get("code") in codes]


def render_grounded_response(question: str, intent: str, context: dict) -> tuple[str, str]:
    """Return (answer, confidence). confidence is "grounded" only when the
    answer is actually backed by retrieved evidence, and "insufficient_evidence"
    when we had to say we don't know yet -- the caller should never report
    "grounded" for an answer that admits it has no evidence.

    Each intent branch below either cites a real Evidence value from the
    context (a metric the analytics layer actually computed) or cites real
    Signal objects (things detect_signals() actually found) -- never both
    absent. Signals cited for customer/product/root-cause questions are
    framed as detected findings/candidate factors, not asserted as the
    definitive single cause, since a signal is a DETECTION, not a proven
    causal explanation (see docs/architecture/architecture.md's trust
    model: FACT -> DETECTION -> ... -> HYPOTHESIS -> RECOMMENDATION).
    """
    evidence = context.get("evidence", [])
    signals = context.get("signals", [])
    recommendations = context.get("recommendations", [])
    grounded = False

    if intent == "business_health":
        revenue = _evidence_for(evidence, "revenue")
        if revenue:
            grounded = True
            change = revenue.get("metadata", {}).get("change")
            answer = f"Your current-month revenue is {_money(revenue.get('value'))}."
            if change is not None:
                answer += f" Compared with the baseline period, it changed by {Decimal(str(change)):.1f}%."
        else:
            answer = "I don't have enough sales evidence to assess overall business health yet."

    elif intent == "sales_performance":
        revenue = _evidence_for(evidence, "revenue")
        if revenue:
            grounded = True
            answer = f"Current-month revenue is {_money(revenue.get('value'))}."
        else:
            answer = "I don't have enough sales evidence yet."

    elif intent == "margin_analysis":
        margin = _evidence_for(evidence, "gross_margin_pct")
        if margin:
            grounded = True
            meta = margin.get("metadata", {})
            answer = (
                f"Your gross margin over the trailing 30 days is {Decimal(str(margin['value'])):.1f}%, on "
                f"{_money(meta.get('revenue'))} revenue against {_money(meta.get('cost'))} cost."
            )
            worst = _signals_with_codes(signals, {"PRODUCT_MARGIN_DETERIORATION"})
            if worst:
                product = worst[0].get("evidence", {}).get("product", "one product")
                answer += f" {product} in particular is selling at or below an acceptable margin."
            discount_issues = _signals_with_codes(signals, {"DISCOUNT_ANOMALY"})
            if discount_issues:
                customer = discount_issues[0].get("evidence", {}).get("customer", "one customer")
                answer += f" Also worth checking: an unusually large discount was given to {customer}."
        else:
            answer = "I don't have enough cost data to assess margin yet."

    elif intent == "receivables_analysis":
        receivables = _evidence_for(evidence, "receivables_outstanding")
        if receivables:
            grounded = True
            meta = receivables.get("metadata", {})
            answer = f"You have {_money(receivables['value'])} outstanding in receivables, of which {_money(meta.get('overdue'))} is overdue."
            overdue_signals = _signals_with_codes(signals, {"RECEIVABLE_OVERDUE"})
            if overdue_signals:
                customer = overdue_signals[0].get("evidence", {}).get("customer", "one customer")
                answer += f" {customer} has the largest overdue balance."
        else:
            answer = "I don't have any outstanding receivables on record yet."

    elif intent == "payables_analysis":
        payables = _evidence_for(evidence, "payables_outstanding")
        if payables:
            grounded = True
            meta = payables.get("metadata", {})
            answer = f"You have {_money(payables['value'])} outstanding in payables, of which {_money(meta.get('overdue'))} is overdue."
            overdue_signals = _signals_with_codes(signals, {"PAYABLE_OVERDUE"})
            if overdue_signals:
                supplier = overdue_signals[0].get("evidence", {}).get("supplier", "one supplier")
                answer += f" Your bill to {supplier} is the most overdue."
        else:
            answer = "I don't have any outstanding payables on record yet."

    elif intent == "supplier_analysis":
        price_signals = _signals_with_codes(signals, {"SUPPLIER_PRICE_INCREASE"})
        concentration = _evidence_for(evidence, "supplier_concentration_top_share_pct")
        if price_signals or concentration:
            grounded = True
            parts = []
            if price_signals:
                s = price_signals[0]
                sev = s.get("evidence", {})
                parts.append(f"{sev.get('supplier', 'A supplier')} has raised prices on {sev.get('product', 'a product')}")
            if concentration:
                top = concentration.get("metadata", {}).get("top_suppliers", [])
                if top:
                    parts.append(f"your top supplier accounts for {top[0].get('share_pct', 0):.1f}% of purchase spend")
            joined = "; ".join(parts) + "."
            answer = joined[0].upper() + joined[1:]
        else:
            answer = "I don't have enough purchase data to assess your suppliers yet."

    elif intent == "expense_analysis":
        expenses = _evidence_for(evidence, "total_expenses")
        if expenses:
            grounded = True
            by_category = expenses.get("metadata", {}).get("by_category", {})
            answer = f"Your expenses over the trailing 30 days total {_money(expenses['value'])}."
            if by_category:
                top_category = max(by_category, key=by_category.get)
                answer += f" {top_category} is your largest expense category at {_money(by_category[top_category])}."
            spikes = _signals_with_codes(signals, {"EXPENSE_SPIKE"})
            if spikes:
                category = spikes[0].get("evidence", {}).get("category", "one category")
                answer += f" {category} expenses have risen materially against their prior baseline."
        else:
            answer = "I don't have enough expense data on record yet."

    elif intent == "customer_analysis":
        customer_signals = _signals_with_codes(signals, {"CUSTOMER_REVENUE_DECLINE", "CUSTOMER_INACTIVE"})
        concentration = _evidence_for(evidence, "customer_concentration_top_share_pct")
        if customer_signals:
            grounded = True
            names = sorted({s.get("evidence", {}).get("customer", "a customer") for s in customer_signals})
            answer = f"{len(customer_signals)} customer-level issue(s) detected, including: {', '.join(names[:3])}."
        elif concentration:
            grounded = True
            top = concentration.get("metadata", {}).get("top_customers", [])
            top_name = top[0].get("name", "your top customer") if top else "your top customer"
            answer = f"No customer decline or inactivity detected. {top_name} accounts for {Decimal(str(concentration['value'])):.1f}% of your top-customer revenue share."
        else:
            answer = "I don't have enough customer-level evidence yet."

    elif intent == "product_analysis":
        product_signals = _signals_with_codes(signals, {"PRODUCT_MARGIN_DETERIORATION", "PRODUCT_SLOW_MOVING"})
        if product_signals:
            grounded = True
            names = sorted({s.get("evidence", {}).get("product", "a product") for s in product_signals})
            answer = f"{len(product_signals)} product-level issue(s) detected, including: {', '.join(names[:3])}."
        else:
            answer = "I don't have enough product-level evidence yet."

    elif intent == "root_cause":
        if signals:
            grounded = True
            top = signals[0]
            title = top.get("title", "a detected issue")
            answer = (
                f"I can't assign a single definitive cause, but {len(signals)} detected signal(s) are the most "
                f"likely contributing factors -- most notably: {title}."
            )
        else:
            answer = "I don't have any detected signals to point to a cause yet."

    else:
        answer = "I can answer this once the relevant business evidence is available."

    if signals:
        answer += f" I detected {len(signals)} business signal(s) that may need attention."
    if recommendations:
        answer += f" There are {len(recommendations)} evidence-backed recommendation(s) available."
    return answer, "grounded" if grounded else "insufficient_evidence"
