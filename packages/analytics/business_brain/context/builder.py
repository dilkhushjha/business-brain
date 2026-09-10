from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from packages.analytics.business_brain.context.models import BusinessContext, Evidence
from packages.analytics.business_brain.metrics.customer_risk import customer_concentration
from packages.analytics.business_brain.metrics.expenses import expense_summary
from packages.analytics.business_brain.metrics.margin import margin_summary
from packages.analytics.business_brain.metrics.payables import payables_summary
from packages.analytics.business_brain.metrics.receivables import receivables_summary
from packages.analytics.business_brain.metrics.supplier_risk import supplier_concentration
from packages.analytics.business_brain.recommendations.engine import recommend
from packages.analytics.business_brain.service import monthly_sales_kpis
from packages.analytics.business_brain.signals.engine import detect_signals


def build_business_context(db: Session, business_id: UUID, as_of: date) -> BusinessContext:
    """Assemble the evidence-first context the agent answers from.

    Originally this only included KPI evidence (revenue, invoice_count,
    units_sold), even though the signal engine was already computing
    margin/receivables/payables/customer- and supplier-concentration data
    to detect signals -- that data just never made it into `evidence`, so
    the agent could never answer a margin or receivables question with a
    real number, only mention that a signal existed. Each metric below is
    only added as evidence when it reflects real activity (not a bare zero
    from an empty business), so an empty result stays "insufficient
    evidence" rather than answering from a meaningless zero.
    """
    kpis = monthly_sales_kpis(db, business_id, as_of)
    signals = detect_signals(db, business_id, as_of)
    recommendations = recommend(db, business_id, as_of)
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

    expenses = expense_summary(db, business_id)
    if expenses["total"]:
        evidence.append(Evidence(
            source="expense_engine", metric="total_expenses",
            value=Decimal(str(expenses["total"])), period="trailing_30_days",
            metadata={"by_category": expenses["by_category"]},
        ))

    return BusinessContext(
        business_id=business_id,
        entities=[],
        evidence=evidence,
        signals=signals,
        recommendations=recommendations,
    )
