from decimal import Decimal

from packages.analytics.business_brain.recommendations.models import Recommendation, RecommendationContext


def generate_recommendations(context: RecommendationContext) -> list[Recommendation]:
    recommendations: list[Recommendation] = []
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
    return recommendations
