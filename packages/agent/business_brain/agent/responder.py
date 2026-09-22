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
    """Return an evidence-first answer with explicit cause-vs-impact separation."""
    evidence = context.get("evidence", [])
    signals = context.get("signals", [])
    recommendations = context.get("recommendations", [])
    decision_actions = context.get("decision_actions", [])
    situations = context.get("situations", [])
    analyses = context.get("analyses", [])
    grounded = False

    if intent == "data_integrity":
        integrity = context.get("integrity") or {}
        if integrity.get("status") == "attention_required":
            grounded = True
            domains = integrity.get("affected_domains") or []
            issue_count = int(integrity.get("issue_count") or 0)
            answer = (
                f"Business data has {issue_count} integrity issue(s) affecting: "
                f"{', '.join(domains) if domains else 'one or more domains'}. "
                "I would resolve these exceptions before relying on affected cross-domain conclusions."
            )
        elif integrity:
            grounded = True
            answer = "The current integrity audits found no unresolved data-quality, inventory, or financial-linkage exceptions."
        else:
            answer = "I don't have an integrity audit available for this business yet."

    elif intent == "situation_history":
        history = context.get("situation_history", [])
        active = [item for item in history if item.get("status") == "active"]
        resolved = [item for item in history if item.get("status") == "resolved"]
        if history:
            grounded = True
            answer = (
                f"I have {len(history)} tracked business situation(s): "
                f"{len(active)} active and {len(resolved)} resolved."
            )
            if active:
                top = active[0]
                answer += (
                    f" Active: {top.get('title', 'an identified situation')} "
                    f"({top.get('trend', 'stable')})."
                )
            if resolved:
                top = resolved[0]
                answer += f" Recently resolved: {top.get('title', 'a tracked situation')}."
        else:
            grounded = True
            answer = "There are no tracked business situations yet."

    elif intent == "decision_support":
        if decision_actions:
            grounded = True
            top = decision_actions[0]
            answer = (
                f"Based on the current business evidence, the next action to consider is: "
                f"{top.get('title', 'review the highest-priority issue')}."
            )
            why_now = top.get("why_now")
            if why_now:
                answer += f" Why now: {why_now}"
            actions = top.get("actions") or []
            if actions:
                answer += " Suggested checks: " + " ".join(
                    f"{idx + 1}) {item}" for idx, item in enumerate(actions[:3])
                ) + "."
        elif situations:
            grounded = True
            answer = (
                "Business Brain has identified a situation that needs review, "
                f"but it does not yet have a specific action plan for {situations[0].get('title', 'it')}."
            )
        else:
            answer = "I don't have enough evidence to recommend a specific business action yet."

    elif intent == "general_business":
        # Give broad questions a useful executive answer instead of falling
        # through to the generic insufficient-context response.
        state = context.get("state") or {}
        if situations or decision_actions or evidence:
            grounded = True
            parts = []
            revenue = _evidence_for(evidence, "revenue")
            margin = _evidence_for(evidence, "gross_margin_pct")
            if revenue:
                parts.append(f"Revenue is {_money(revenue.get('value'))}.")
            if margin:
                parts.append(f"Gross margin is {Decimal(str(margin.get('value'))):.1f}%.")
            if situations:
                top = situations[0]
                parts.append(
                    f"The main cross-domain situation to review is {top.get('title', 'an identified business situation')}."
                )
            if decision_actions:
                action = decision_actions[0]
                parts.append(f"Suggested next step: {action.get('title', 'review the highest-priority action')}.")
            answer = " ".join(parts)
        else:
            answer = "I don't have enough business evidence yet to summarize what needs attention."

    elif intent == "business_health":
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
            pressure = next(
                (item for item in situations if item.get("code") in {"MARGIN_PRESSURE", "PROFITABILITY_PRESSURE", "REVENUE_COST_SQUEEZE"}),
                None,
            )
            if pressure:
                answer += f" Cross-domain signal: {pressure.get('title', 'margin pressure')}."
                analysis = next((item for item in analyses if item.get("situation_code") == pressure.get("code")), None)
                if analysis and analysis.get("root_causes"):
                    answer += f" Likely contributing factor: {analysis['root_causes'][0].get('title', 'a detected factor')}."
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
        product_signals = _signals_with_codes(signals, {"PRODUCT_MARGIN_DETERIORATION", "PRODUCT_SLOW_MOVING", "STOCKOUT_RISK", "EXCESS_INVENTORY", "DEMAND_SPIKE", "DEAD_STOCK"})
        if product_signals:
            grounded = True
            names = sorted({s.get("evidence", {}).get("product", "a product") for s in product_signals})
            answer = f"{len(product_signals)} product-level issue(s) detected, including: {', '.join(names[:3])}."
            stockouts = _signals_with_codes(signals, {"STOCKOUT_RISK"})
            if stockouts:
                worst = stockouts[0]
                product = worst.get("evidence", {}).get("product", "one product")
                answer += f" {product} is at risk of running out soon."
        else:
            answer = "I don't have enough product-level evidence yet."

    elif intent == "root_cause":
        if analyses:
            grounded = True
            analysis = analyses[0]
            causes = analysis.get("root_causes", [])
            impacts = analysis.get("impacts", [])
            if causes:
                cause = causes[0]
                answer = (
                    "I can't call this a proven single cause, but Business Brain found an evidence-backed "
                    f"contributing factor: {cause.get('title', 'a detected factor')}."
                )
                cause_evidence = cause.get("evidence", {})
                if cause_evidence.get("products"):
                    answer += f" Affected products: {', '.join(map(str, cause_evidence['products'][:5]))}."
            else:
                answer = "Business Brain found a related situation but does not yet have enough evidence to name a contributing factor."
            if impacts:
                impact = impacts[0]
                description = impact.get("description")
                if description:
                    answer += f" Impact: {description}"
        elif signals:
            grounded = True
            # Prefer an entity-specific signal so root-cause answers identify
            # the actual customer/product/supplier involved rather than a
            # generic KPI decline that happened to be emitted first.
            top = next(
                (
                    item for item in signals
                    if any(
                        key in (item.get("evidence") or {})
                        for key in ("customer", "product", "supplier", "category")
                    )
                ),
                signals[0],
            )
            answer = (
                "I can't assign a single definitive cause, but the detected signals provide candidate factors -- "
                f"most notably: {top.get('title', 'a detected issue')}."
            )
        else:
            answer = "I don't have any detected signals to point to a cause yet."

    else:
        answer = "I can answer this once the relevant business evidence is available."

    integrity = context.get("integrity") or {}
    if integrity.get("status") == "attention_required" and intent != "data_integrity":
        domains = integrity.get("affected_domains") or []
        domain_text = ", ".join(domains) if domains else "part of the data"
        answer += (
            " Data-quality caveat: unresolved integrity issues affect "
            f"{domain_text}; treat this conclusion as provisional."
        )
    if signals:
        answer += f" I detected {len(signals)} business signal(s) that may need attention."
    if situations:
        answer += f" Business Brain also identified {len(situations)} cross-domain business situation(s) linking related signals."
        top_situation = situations[0]
        if top_situation.get("title"):
            answer += " The most relevant is: " + str(top_situation.get("title")) + "."
    if recommendations:
        answer += f" There are {len(recommendations)} evidence-backed recommendation(s) available."
    return answer, "grounded" if grounded else "insufficient_evidence"
