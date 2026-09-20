from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from packages.analytics.business_brain.context.models import BusinessContext, Evidence
from packages.analytics.business_brain.metrics.customer_risk import customer_concentration
from packages.analytics.business_brain.metrics.expenses import expense_summary
from packages.analytics.business_brain.metrics.margin import margin_summary
from packages.analytics.business_brain.metrics.payables import payables_summary
from packages.analytics.business_brain.metrics.purchase_risk import supplier_spend_risk
from packages.analytics.business_brain.metrics.receivables import receivables_summary
from packages.analytics.business_brain.metrics.supplier_risk import supplier_concentration
from packages.analytics.business_brain.service import monthly_sales_kpis
from packages.analytics.business_brain.signals.engine import detect_signals
from packages.analytics.business_brain.state import build_business_state
from packages.analytics.business_brain.correlations import correlate_signals
from packages.analytics.business_brain.analysis import analyze_situation
from packages.analytics.business_brain.prioritization import prioritize_situations
from packages.analytics.business_brain.decision_support import build_decision_actions
from packages.analytics.business_brain.history import record_situation_history
from packages.analytics.business_brain.recommendations.rules import generate_recommendations
from packages.analytics.business_brain.recommendations.models import RecommendationContext


def build_business_context(db: Session, business_id: UUID, as_of: date) -> BusinessContext:
    """Assemble the evidence-first context the agent answers from."""
    kpis = monthly_sales_kpis(db, business_id, as_of)
    signals = detect_signals(db, business_id, as_of)
    evidence = [
        Evidence(
            source="kpi_engine",
            metric=kpi.name,
            value=kpi.value,
            period=kpi.period,
            metadata={
                "comparison_value": str(kpi.comparison_value) if kpi.comparison_value is not None else None,
                "change": str(kpi.change) if kpi.change is not None else None,
            },
        )
        for kpi in kpis
    ]

    margin = margin_summary(db, business_id)
    if margin["gross_margin_pct"] is not None:
        evidence.append(Evidence(
            source="margin_engine", metric="gross_margin_pct",
            value=Decimal(str(margin["gross_margin_pct"])), period="trailing_30_days",
            metadata={"revenue": margin["revenue"], "cost": margin["cost"],
                      "gross_profit": margin["gross_profit"], "cost_coverage_pct": margin["cost_coverage_pct"]},
        ))

    receivables = receivables_summary(db, business_id)
    if receivables["outstanding"]:
        evidence.append(Evidence(
            source="receivables_engine", metric="receivables_outstanding",
            value=Decimal(str(receivables["outstanding"])), period="as_of_today",
            metadata={"overdue": receivables["overdue"], "overdue_pct": receivables["overdue_pct"]},
        ))

    payables = payables_summary(db, business_id)
    if payables["outstanding"]:
        evidence.append(Evidence(
            source="payables_engine", metric="payables_outstanding",
            value=Decimal(str(payables["outstanding"])), period="as_of_today",
            metadata={"overdue": payables["overdue"], "overdue_pct": payables["overdue_pct"]},
        ))

    concentration = customer_concentration(db, business_id)
    if concentration["top_customers"]:
        evidence.append(Evidence(
            source="customer_risk_engine", metric="customer_concentration_top_share_pct",
            value=Decimal(str(concentration["top_share_pct"])), period="trailing_90_days",
            metadata={"top_customers": concentration["top_customers"], "risk": concentration["risk"]},
        ))

    supplier_conc = supplier_concentration(db, business_id)
    if supplier_conc["top_suppliers"]:
        evidence.append(Evidence(
            source="supplier_risk_engine", metric="supplier_concentration_top_share_pct",
            value=Decimal(str(supplier_conc["top_share_pct"])), period="all_time",
            metadata={"top_suppliers": supplier_conc["top_suppliers"], "risk": supplier_conc["risk"]},
        ))

    purchase_risk = supplier_spend_risk(db, business_id)
    if purchase_risk["total_spend"]:
        evidence.append(Evidence(
            source="purchase_risk_engine", metric="supplier_spend_concentration_pct",
            value=Decimal(str(purchase_risk["top_share_pct"])), period="trailing_90_days",
            metadata={"top_supplier": purchase_risk["top_supplier"], "total_spend": purchase_risk["total_spend"]},
        ))

    expenses = expense_summary(db, business_id)
    if expenses["total"]:
        evidence.append(Evidence(
            source="expense_engine", metric="total_expenses",
            value=Decimal(str(expenses["total"])), period="trailing_30_days",
            metadata={"by_category": expenses["by_category"]},
        ))

    state = build_business_state(
        kpis=kpis,
        margin=margin,
        receivables=receivables,
        payables=payables,
        purchase_risk=purchase_risk,
        customer_concentration=concentration,
        supplier_concentration=supplier_conc,
        expenses=expenses,
        signals=signals,
    )

    situations = correlate_signals(signals, state)
    analyses = [analyze_situation(situation, state) for situation in situations]
    priorities = prioritize_situations(situations, analyses)
    recommendations = generate_recommendations(
        RecommendationContext(signals=signals, drivers=situations)
    )
    situation_history = record_situation_history(
        db=db,
        business_id=business_id,
        as_of=as_of,
        situations=situations,
        priorities=priorities,
    )
    decision_actions = build_decision_actions(
        situations=situations,
        priorities=priorities,
        analyses=analyses,
        recommendations=recommendations,
    )

    return BusinessContext(
        business_id=business_id,
        entities=[],
        evidence=evidence,
        signals=signals,
        recommendations=recommendations,
        state=state,
        situations=situations,
        analyses=analyses,
        priorities=priorities,
        decision_actions=decision_actions,
        situation_history=situation_history,
    )
