from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.shared.database.models import (
    CustomerModel,
    ProductModel,
    PurchaseLineModel,
    PurchaseModel,
    SaleLineModel,
    SaleModel,
    SupplierModel,
)


def _norm(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def _duplicate_names(rows):
    groups = defaultdict(list)
    for row_id, name in rows:
        key = _norm(name)
        if key:
            groups[key].append({"id": str(row_id), "name": name})
    return [
        {"normalized_name": key, "records": records, "count": len(records)}
        for key, records in sorted(groups.items())
        if len(records) > 1
    ]


def _entity_duplicates(db: Session, model, business_id: UUID, label: str, limit: int):
    rows = db.execute(
        select(model.id, model.name)
        .where(model.business_id == business_id)
    ).all()
    groups = _duplicate_names(rows)
    return {
        "entity_type": label,
        "duplicate_name_groups": groups[:limit],
        "duplicate_name_group_count": len(groups),
    }


def _sale_total_mismatches(db: Session, business_id: UUID):
    rows = db.execute(
        select(
            SaleModel.invoice_number,
            SaleModel.total_amount,
            SaleModel.tax_amount,
            SaleModel.discount_amount,
            func.coalesce(func.sum(SaleLineModel.quantity * SaleLineModel.unit_price), 0),
        )
        .outerjoin(SaleLineModel, SaleLineModel.sale_id == SaleModel.id)
        .where(SaleModel.business_id == business_id)
        .group_by(
            SaleModel.id,
            SaleModel.invoice_number,
            SaleModel.total_amount,
            SaleModel.tax_amount,
            SaleModel.discount_amount,
        )
    ).all()
    issues = []
    for invoice, total, tax, discount, subtotal in rows:
        # Sales headers store the document total, while lines store the
        # pre-tax/pre-discount selling value.
        expected = Decimal(str(subtotal)) + Decimal(str(tax)) - Decimal(str(discount))
        actual = Decimal(str(total))
        if abs(actual - expected) > Decimal("0.01"):
            issues.append({
                "invoice_number": invoice,
                "expected_total_from_lines": float(expected),
                "recorded_total": float(actual),
                "difference": float(actual - expected),
            })
    return issues


def _purchase_total_mismatches(db: Session, business_id: UUID):
    rows = db.execute(
        select(
            PurchaseModel.invoice_number,
            PurchaseModel.total_amount,
            func.coalesce(func.sum(PurchaseLineModel.net_amount), 0),
        )
        .outerjoin(PurchaseLineModel, PurchaseLineModel.purchase_id == PurchaseModel.id)
        .where(PurchaseModel.business_id == business_id)
        .group_by(PurchaseModel.id, PurchaseModel.invoice_number, PurchaseModel.total_amount)
    ).all()
    issues = []
    for invoice, total, net_amount in rows:
        # Purchase line net_amount is already the canonical line amount after
        # line-level discounts, so header tax/discount are not added again.
        expected = Decimal(str(net_amount))
        actual = Decimal(str(total))
        if abs(actual - expected) > Decimal("0.01"):
            issues.append({
                "invoice_number": invoice,
                "expected_total_from_lines": float(expected),
                "recorded_total": float(actual),
                "difference": float(actual - expected),
            })
    return issues


def _numeric_issues(db: Session, business_id: UUID):
    issues = []

    sales = db.execute(
        select(SaleModel.invoice_number, SaleLineModel.quantity, SaleLineModel.unit_price)
        .join(SaleLineModel, SaleLineModel.sale_id == SaleModel.id)
        .where(SaleModel.business_id == business_id)
    ).all()
    for invoice, quantity, unit_price in sales:
        quantity = Decimal(str(quantity))
        unit_price = Decimal(str(unit_price))
        if quantity <= 0:
            issues.append({"type": "sale_line_quantity", "invoice_number": invoice, "value": float(quantity)})
        if unit_price < 0:
            issues.append({"type": "sale_line_unit_price", "invoice_number": invoice, "value": float(unit_price)})

    purchases = db.execute(
        select(PurchaseModel.invoice_number, PurchaseLineModel.quantity, PurchaseLineModel.unit_cost)
        .join(PurchaseLineModel, PurchaseLineModel.purchase_id == PurchaseModel.id)
        .where(PurchaseModel.business_id == business_id)
    ).all()
    for invoice, quantity, unit_cost in purchases:
        quantity = Decimal(str(quantity))
        unit_cost = Decimal(str(unit_cost))
        if quantity <= 0:
            issues.append({"type": "purchase_line_quantity", "invoice_number": invoice, "value": float(quantity)})
        if unit_cost < 0:
            issues.append({"type": "purchase_line_unit_cost", "invoice_number": invoice, "value": float(unit_cost)})

    return issues


def audit_data_quality(db: Session, business_id: UUID, limit: int = 50) -> dict:
    """Read-only audit of identity, document completeness and numeric consistency.

    Duplicate names are reported as ambiguity, not merged. Optional source
    identifiers such as SKU/external_id are not treated as errors because the
    database schema permits businesses that do not provide them.
    """
    limit = max(1, min(limit, 200))

    customers = _entity_duplicates(db, CustomerModel, business_id, "customer", limit)
    suppliers = _entity_duplicates(db, SupplierModel, business_id, "supplier", limit)
    products = _entity_duplicates(db, ProductModel, business_id, "product", limit)

    sales = db.execute(
        select(SaleModel.id, SaleModel.invoice_number, SaleModel.transaction_date)
        .where(SaleModel.business_id == business_id)
    ).all()
    purchases = db.execute(
        select(PurchaseModel.id, PurchaseModel.invoice_number, PurchaseModel.transaction_date)
        .where(PurchaseModel.business_id == business_id)
    ).all()

    missing_sale_invoices = [{"id": str(row[0])} for row in sales if not str(row[1] or "").strip()]
    missing_purchase_invoices = [{"id": str(row[0])} for row in purchases if not str(row[1] or "").strip()]
    missing_sale_dates = [{"invoice_number": row[1]} for row in sales if row[2] is None]
    missing_purchase_dates = [{"invoice_number": row[1]} for row in purchases if row[2] is None]

    sale_totals = _sale_total_mismatches(db, business_id)
    purchase_totals = _purchase_total_mismatches(db, business_id)
    numeric = _numeric_issues(db, business_id)

    sections = {
        "customers": customers,
        "suppliers": suppliers,
        "products": products,
        "sales": {
            "missing_invoice_number_count": len(missing_sale_invoices),
            "missing_invoice_numbers": missing_sale_invoices[:limit],
            "missing_transaction_date_count": len(missing_sale_dates),
            "missing_transaction_dates": missing_sale_dates[:limit],
            "total_mismatches": sale_totals[:limit],
            "total_mismatch_count": len(sale_totals),
        },
        "purchases": {
            "missing_invoice_number_count": len(missing_purchase_invoices),
            "missing_invoice_numbers": missing_purchase_invoices[:limit],
            "missing_transaction_date_count": len(missing_purchase_dates),
            "missing_transaction_dates": missing_purchase_dates[:limit],
            "total_mismatches": purchase_totals[:limit],
            "total_mismatch_count": len(purchase_totals),
        },
        "numeric_issues": numeric[:limit],
        "numeric_issue_count": len(numeric),
    }

    issue_count = (
        customers["duplicate_name_group_count"]
        + suppliers["duplicate_name_group_count"]
        + products["duplicate_name_group_count"]
        + len(missing_sale_invoices)
        + len(missing_purchase_invoices)
        + len(missing_sale_dates)
        + len(missing_purchase_dates)
        + len(sale_totals)
        + len(purchase_totals)
        + len(numeric)
    )

    return {
        "status": "attention_required" if issue_count else "reconciled",
        "summary": {
            "issue_count": issue_count,
            "duplicate_entity_group_count": (
                customers["duplicate_name_group_count"]
                + suppliers["duplicate_name_group_count"]
                + products["duplicate_name_group_count"]
            ),
            "missing_document_identity_count": len(missing_sale_invoices) + len(missing_purchase_invoices),
            "missing_transaction_date_count": len(missing_sale_dates) + len(missing_purchase_dates),
            "document_total_mismatch_count": len(sale_totals) + len(purchase_totals),
            "numeric_issue_count": len(numeric),
        },
        "sections": sections,
    }
