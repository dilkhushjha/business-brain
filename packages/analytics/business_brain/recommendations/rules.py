from decimal import Decimal

from packages.analytics.business_brain.recommendations.models import Recommendation, RecommendationContext


def generate_recommendations(context: RecommendationContext) -> list[Recommendation]:
    recommendations: list[Recommendation] = []
    for situation in context.drivers:
        if situation.code == "MARGIN_PRESSURE":
            recommendations.append(Recommendation(
                code="INVESTIGATE_MARGIN_PRESSURE",
                title="Investigate procurement-driven margin pressure",
                priority="high" if situation.severity == "critical" else "medium",
                confidence=situation.confidence,
                rationale=situation.explanation,
                evidence=situation.evidence,
                actions=[
                    "Review supplier pricing for the affected products.",
                    "Compare current selling prices with the higher procurement costs.",
                    "Check alternative suppliers or renegotiate buying terms.",
                ],
            ))
        elif situation.code == "SUPPLIER_DEPENDENCY_PRESSURE":
            recommendations.append(Recommendation(
                code="REDUCE_SUPPLIER_DEPENDENCY",
                title="Review concentrated supplier dependency",
                priority="high" if situation.severity == "critical" else "medium",
                confidence=situation.confidence,
                rationale=situation.explanation,
                evidence=situation.evidence,
                actions=[
                    "Identify viable secondary suppliers.",
                    "Review negotiation leverage and current buying terms.",
                    "Check the margin impact if this supplier raises prices further.",
                ],
            ))
        elif situation.code == "PROCUREMENT_DEMAND_PRESSURE":
            recommendations.append(Recommendation(
                code="ALIGN_PROCUREMENT_WITH_DEMAND",
                title="Align purchasing with rising demand",
                priority="high" if situation.severity == "critical" else "medium",
                confidence=situation.confidence,
                rationale=situation.explanation,
                evidence=situation.evidence,
                actions=[
                    "Check stock coverage for products with rising demand.",
                    "Confirm supplier lead times and reorder requirements.",
                    "Separate repeatable demand growth from one-off orders.",
                ],
            ))
        elif situation.code == "WORKING_CAPITAL_PRESSURE":
            recommendations.append(Recommendation(
                code="REVIEW_WORKING_CAPITAL_PRESSURE",
                title="Review near-term working capital pressure",
                priority="high" if situation.severity == "critical" else "medium",
                confidence=situation.confidence,
                rationale=situation.explanation,
                evidence=situation.evidence,
                actions=[
                    "Prioritize collection of overdue customer receivables.",
                    "Review supplier payment priorities and available terms.",
                    "Check near-term cash requirements before committing to new purchases.",
                ],
            ))

    for signal in context.signals:
        if signal.code == "REVENUE_DECLINE":
            recommendations.append(
                Recommendation(
                    code="INVESTIGATE_REVENUE_DECLINE",
                    title="Investigate the revenue decline",
                    priority="high" if signal.severity == "critical" else "medium",
                    confidence=signal.confidence,
                    rationale="Revenue is materially below its comparison period and requires driver-level investigation.",
                    evidence={"signal": signal.code, "change": str(signal.change)},
                    actions=[
                        "Review the largest customer contributors to the decline.",
                        "Review the largest product/category contributors to the decline.",
                        "Check whether the decline is concentrated in recent weeks.",
                    ],
                )
            )
        elif signal.code == "REVENUE_SPIKE":
            recommendations.append(
                Recommendation(
                    code="ANALYZE_REVENUE_SPIKE",
                    title="Analyze the revenue spike",
                    priority="medium",
                    confidence=signal.confidence,
                    rationale="Revenue is materially above its comparison period; identify whether the increase is repeatable.",
                    evidence={"signal": signal.code, "change": str(signal.change)},
                    actions=[
                        "Identify products and customers driving the increase.",
                        "Check whether the increase is due to one-off orders.",
                        "Review inventory capacity before committing to higher demand assumptions.",
                    ],
                )
            )
        elif signal.code == "CUSTOMER_REVENUE_DECLINE":
            customer = signal.evidence.get("customer", "This customer")
            recommendations.append(
                Recommendation(
                    code="RETAIN_DECLINING_CUSTOMER",
                    title=f"Re-engage {customer}",
                    priority="high" if signal.severity == "critical" else "medium",
                    confidence=signal.confidence,
                    rationale=f"{customer}'s order value has dropped materially against their prior baseline.",
                    evidence={"signal": signal.code, "customer": customer, "change": str(signal.change)},
                    actions=[
                        f"Contact {customer} to understand the reason for reduced orders.",
                        "Check for service issues, pricing complaints or a competitor switch.",
                        "Consider a retention offer if the account is high-value.",
                    ],
                )
            )
        elif signal.code == "PRODUCT_MARGIN_DETERIORATION":
            product = signal.evidence.get("product", "This product")
            recommendations.append(
                Recommendation(
                    code="REVIEW_PRODUCT_MARGIN",
                    title=f"Review margin on {product}",
                    priority="high" if signal.severity == "critical" else "medium",
                    confidence=signal.confidence,
                    rationale=f"{product} is selling at or below the acceptable margin threshold.",
                    evidence={"signal": signal.code, "product": product, "margin_pct": str(signal.current_value)},
                    actions=[
                        f"Check whether {product}'s selling price needs adjusting.",
                        f"Check whether {product}'s procurement/cost price has increased.",
                        "Confirm the cost data behind this margin is current and accurate.",
                    ],
                )
            )
        elif signal.code == "RECEIVABLE_OVERDUE":
            customer = signal.evidence.get("customer", "This customer")
            days_overdue = signal.evidence.get("days_overdue")
            recommendations.append(
                Recommendation(
                    code="COLLECT_OVERDUE_RECEIVABLE",
                    title=f"Follow up on {customer}'s overdue payment",
                    priority="high" if signal.severity == "critical" else "medium",
                    confidence=signal.confidence,
                    rationale=f"{customer} has an outstanding payment overdue by {days_overdue} days.",
                    evidence={"signal": signal.code, "customer": customer, "days_overdue": days_overdue},
                    actions=[
                        f"Send a payment reminder to {customer}.",
                        "Confirm there is no invoicing or delivery dispute blocking payment.",
                        "Consider tightening credit terms for this account going forward.",
                    ],
                )
            )
        elif signal.code == "CUSTOMER_INACTIVE":
            customer = signal.evidence.get("customer", "This customer")
            recommendations.append(
                Recommendation(
                    code="REACTIVATE_INACTIVE_CUSTOMER",
                    title=f"Reach out to {customer}",
                    priority="high" if signal.severity == "critical" else "medium",
                    confidence=signal.confidence,
                    rationale=f"{customer} has placed no orders in {signal.current_value} days.",
                    evidence={"signal": signal.code, "customer": customer, "days_inactive": str(signal.current_value)},
                    actions=[
                        f"Check in with {customer} to see if anything has changed on their end.",
                        "Confirm they weren't lost to a competitor or a service issue.",
                        "Consider a win-back offer if their lifetime value was significant.",
                    ],
                )
            )
        elif signal.code == "PRODUCT_SLOW_MOVING":
            product = signal.evidence.get("product", "This product")
            recommendations.append(
                Recommendation(
                    code="REVIEW_SLOW_MOVING_PRODUCT",
                    title=f"Review slow-moving stock: {product}",
                    priority="high" if signal.severity == "critical" else "medium",
                    confidence=signal.confidence,
                    rationale=f"{product}'s sales velocity has dropped materially against its prior baseline.",
                    evidence={"signal": signal.code, "product": product, "change": str(signal.change)},
                    actions=[
                        f"Consider a promotion or discount to move existing {product} stock.",
                        f"Reduce or pause reorder quantity for {product} until demand recovers.",
                        "Check whether a newer product or substitute is cannibalizing demand.",
                    ],
                )
            )
        elif signal.code == "PAYABLE_OVERDUE":
            supplier = signal.evidence.get("supplier", "This supplier")
            days_overdue = signal.evidence.get("days_overdue")
            recommendations.append(
                Recommendation(
                    code="PAY_OVERDUE_PAYABLE",
                    title=f"Pay {supplier}'s overdue bill",
                    priority="high" if signal.severity == "critical" else "medium",
                    confidence=signal.confidence,
                    rationale=f"You have an outstanding bill to {supplier} overdue by {days_overdue} days.",
                    evidence={"signal": signal.code, "supplier": supplier, "days_overdue": days_overdue},
                    actions=[
                        f"Schedule payment to {supplier} to avoid a late fee or supply disruption.",
                        "Confirm there is no invoicing or delivery dispute blocking payment.",
                        "Check whether cash flow supports paying this now vs. negotiating terms.",
                    ],
                )
            )
        elif signal.code == "SUPPLIER_PRICE_INCREASE":
            supplier = signal.evidence.get("supplier", "This supplier")
            product = signal.evidence.get("product", "this product")
            recommendations.append(
                Recommendation(
                    code="REVIEW_SUPPLIER_PRICE_INCREASE",
                    title=f"Review {supplier}'s price increase on {product}",
                    priority="high" if signal.severity == "critical" else "medium",
                    confidence=signal.confidence,
                    rationale=f"{supplier}'s purchase cost for {product} has risen materially against its prior baseline.",
                    evidence={"signal": signal.code, "supplier": supplier, "product": product, "change": str(signal.change)},
                    actions=[
                        f"Confirm the increase with {supplier} and ask for the reason.",
                        f"Check whether {product}'s selling price needs adjusting to protect margin.",
                        f"Get a quote from an alternative supplier for {product}.",
                    ],
                )
            )
        elif signal.code == "DISCOUNT_ANOMALY":
            customer = signal.evidence.get("customer", "a customer")
            invoice = signal.evidence.get("invoice_number", "the invoice")
            recommendations.append(
                Recommendation(
                    code="VERIFY_DISCOUNT_ANOMALY",
                    title=f"Verify the discount given to {customer}",
                    priority="high" if signal.severity == "critical" else "medium",
                    confidence=signal.confidence,
                    rationale=f"{customer}'s discount rate on invoice {invoice} is well above this business's recent average.",
                    evidence={"signal": signal.code, "customer": customer, "invoice_number": invoice},
                    actions=[
                        f"Confirm invoice {invoice} was approved at that discount level.",
                        "Check whether this reflects a policy exception, a data entry error, or unauthorized discounting.",
                        "Consider whether a standing discount policy needs to be written down for this customer or product.",
                    ],
                )
            )
        elif signal.code == "EXPENSE_SPIKE":
            category = signal.evidence.get("category", "an expense category")
            recommendations.append(
                Recommendation(
                    code="REVIEW_EXPENSE_SPIKE",
                    title=f"Review the rise in {category} expenses",
                    priority="high" if signal.severity == "critical" else "medium",
                    confidence=signal.confidence,
                    rationale=f"{category} spend has increased materially against its prior baseline.",
                    evidence={"signal": signal.code, "category": category, "change": str(signal.change)},
                    actions=[
                        f"Review the individual {category} expenses behind the increase.",
                        "Confirm whether this reflects a one-off cost or a new ongoing rate.",
                        f"Check if a vendor or rate change is behind the {category} increase.",
                    ],
                )
            )
        elif signal.code == "STOCKOUT_RISK":
            product = signal.evidence.get("product", "a product")
            days = signal.current_value
            recommendations.append(
                Recommendation(
                    code="REORDER_STOCKOUT_RISK",
                    title=f"Reorder {product} soon",
                    priority="high" if signal.severity == "critical" else "medium",
                    confidence=signal.confidence,
                    rationale=f"At current sales pace, {product}'s stock covers only about {days} more day(s).",
                    evidence={"signal": signal.code, "product": product, "days_of_cover": str(days)},
                    actions=[
                        f"Place a reorder for {product} now to avoid a stockout.",
                        "Confirm supplier lead time still fits within the remaining days of cover.",
                        "Check if demand has picked up recently, which would shorten this further.",
                    ],
                )
            )
        elif signal.code == "EXCESS_INVENTORY":
            product = signal.evidence.get("product", "a product")
            days = signal.current_value
            recommendations.append(
                Recommendation(
                    code="REDUCE_EXCESS_INVENTORY",
                    title=f"Reduce stock on {product}",
                    priority="high" if signal.severity == "critical" else "medium",
                    confidence=signal.confidence,
                    rationale=f"{product}'s current stock covers roughly {days} days at today's sales pace -- capital may be tied up unnecessarily.",
                    evidence={"signal": signal.code, "product": product, "days_of_cover": str(days)},
                    actions=[
                        f"Pause or reduce reordering {product} until stock works down.",
                        f"Consider a promotion or discount to move {product} faster.",
                        "Confirm this isn't seasonal stock being held ahead of demand.",
                    ],
                )
            )
        elif signal.code == "DEMAND_SPIKE":
            product = signal.evidence.get("product", "a product")
            recommendations.append(
                Recommendation(
                    code="REVIEW_DEMAND_SPIKE",
                    title=f"Check stock for {product}'s demand spike",
                    priority="high" if signal.severity == "critical" else "medium",
                    confidence=signal.confidence,
                    rationale=f"{product}'s sales velocity has increased materially against its prior baseline.",
                    evidence={"signal": signal.code, "product": product, "change": str(signal.change)},
                    actions=[
                        f"Confirm there's enough {product} stock to meet the increased demand.",
                        f"Check reorder lead time for {product} in case a stockout risk follows.",
                        "Consider whether this is a one-off (promotion, season) or a lasting shift.",
                    ],
                )
            )
        elif signal.code == "DEAD_STOCK":
            product = signal.evidence.get("product", "a product")
            days = signal.evidence.get("velocity_window_days")
            recommendations.append(
                Recommendation(
                    code="CLEAR_DEAD_STOCK",
                    title=f"Clear dead stock: {product}",
                    priority="medium",
                    confidence=signal.confidence,
                    rationale=f"{product} has real stock on hand but hasn't sold at all in {days} days.",
                    evidence={"signal": signal.code, "product": product, "quantity_on_hand": str(signal.current_value)},
                    actions=[
                        f"Consider a clearance sale or bundle to move {product}.",
                        f"Check whether {product} is discontinued or superseded by another item.",
                        "Consider writing down its stock value if it's unlikely to sell.",
                    ],
                )
            )
    return recommendations
