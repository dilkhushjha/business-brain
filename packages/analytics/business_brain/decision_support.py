from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class DecisionAction:
    """An evidence-backed action produced from a prioritized business situation."""

    code: str
    situation_code: str
    title: str
    priority_level: str
    priority_score: Decimal
    confidence: Decimal
    why_now: str
    evidence: dict[str, Any]
    actions: list[str]


_SITUATION_ACTION_CODES = {
    "MARGIN_PRESSURE": "INVESTIGATE_MARGIN_PRESSURE",
    "SUPPLIER_DEPENDENCY_PRESSURE": "REDUCE_SUPPLIER_DEPENDENCY",
    "PROCUREMENT_DEMAND_PRESSURE": "ALIGN_PROCUREMENT_WITH_DEMAND",
    "WORKING_CAPITAL_PRESSURE": "REVIEW_WORKING_CAPITAL_PRESSURE",
    "PROFITABILITY_PRESSURE": "REVIEW_PROFITABILITY_PRESSURE",
    "REVENUE_COST_SQUEEZE": "REVIEW_REVENUE_COST_SQUEEZE",
}

_BASE_ACTIONS = {
    "MARGIN_PRESSURE": [
        "Review supplier pricing for the affected products.",
        "Compare current selling prices with higher procurement costs.",
        "Check alternative suppliers or renegotiate buying terms.",
    ],
    "SUPPLIER_DEPENDENCY_PRESSURE": [
        "Identify viable secondary suppliers.",
        "Review negotiation leverage and current buying terms.",
        "Check the margin impact if this supplier raises prices further.",
    ],
    "PROCUREMENT_DEMAND_PRESSURE": [
        "Check stock coverage for products with rising demand.",
        "Confirm supplier lead times and reorder requirements.",
        "Separate repeatable demand growth from one-off orders.",
    ],
    "WORKING_CAPITAL_PRESSURE": [
        "Prioritize collection of overdue customer receivables.",
        "Review supplier payment priorities and available terms.",
        "Check near-term cash requirements before committing to new purchases.",
    ],
    "PROFITABILITY_PRESSURE": [
        "Review products with deteriorating margins.",
        "Review the expense categories behind the increase.",
        "Separate one-off costs from recurring operating costs.",
    ],
    "REVENUE_COST_SQUEEZE": [
        "Identify the customers and products driving the revenue decline.",
        "Review the expense categories increasing during the revenue decline.",
        "Separate temporary changes from a persistent cost/revenue trend.",
    ],
}


def _priority_for(code: str, priorities: list[Any]) -> Any | None:
    return next((p for p in priorities if getattr(p, "situation_code", "") == code), None)


def _analysis_for(code: str, analyses: list[Any]) -> Any | None:
    return next((a for a in analyses if getattr(a, "situation_code", "") == code), None)


def _why_now(situation: Any, priority: Any, analysis: Any | None) -> str:
    level = getattr(priority, "level", "monitor") if priority else "monitor"
    score = getattr(priority, "score", None) if priority else None
    confidence = getattr(situation, "confidence", Decimal("0"))

    parts = [f"{str(level).capitalize()} attention is warranted"]
    if score is not None:
        parts.append(f"on an explainable priority score of {Decimal(str(score)):.1f}")
    parts.append(f"with {Decimal(str(confidence)) * 100:.0f}% situation confidence")

    if analysis:
        measurable = [
            impact for impact in (getattr(analysis, "impacts", []) or [])
            if getattr(impact, "value", None) is not None
        ]
        if measurable:
            parts.append("and measurable business impact evidence")

    return ", ".join(parts) + "."


def build_decision_actions(
    situations: list[Any],
    priorities: list[Any] | None = None,
    analyses: list[Any] | None = None,
    recommendations: list[Any] | None = None,
) -> list[DecisionAction]:
    """Turn prioritized situations into concrete, evidence-backed action plans.

    This engine does not invent new evidence or financial outcomes. It combines
    the already-detected situation, its priority, root-cause/impact analysis,
    and the existing recommendation action list.
    """
    priorities = priorities or []
    analyses = analyses or []
    recommendations = recommendations or []

    actions: list[DecisionAction] = []
    for situation in situations:
        code = str(getattr(situation, "code", ""))
        recommendation_code = _SITUATION_ACTION_CODES.get(code)
        recommendation = next(
            (r for r in recommendations if getattr(r, "code", "") == recommendation_code),
            None,
        )

        priority = _priority_for(code, priorities)
        analysis = _analysis_for(code, analyses)
        action_list = (
            list(getattr(recommendation, "actions", []) or [])
            if recommendation is not None
            else list(_BASE_ACTIONS.get(code, []))
        )

        if not action_list:
            action_list = [str(getattr(situation, "recommended_next_step", "Review the supporting evidence."))]

        actions.append(DecisionAction(
            code=recommendation_code or f"REVIEW_{code}",
            situation_code=code,
            title=(
                str(getattr(recommendation, "title", "Review business situation"))
                if recommendation is not None
                else str(getattr(situation, "title", "Review business situation"))
            ),
            priority_level=str(getattr(priority, "level", "monitor")),
            priority_score=Decimal(str(getattr(priority, "score", "0"))),
            confidence=Decimal(str(getattr(situation, "confidence", "0"))),
            why_now=_why_now(situation, priority, analysis),
            evidence=dict(getattr(situation, "evidence", {}) or {}),
            actions=action_list,
        ))

    return sorted(actions, key=lambda item: (-item.priority_score, item.code))
