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
    return recommendations
