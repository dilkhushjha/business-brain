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
            groups[key].append((str(row_id), name))
    return [
        {"normalized_name": key, "records": records, "count": len(records)}
        for key, records in sorted(groups.items())
        if len(records) > 1
    ]


def _entity_identity_audit(db: Session, model, label: str):
    rows = db.execute(
        select(model.id, model.name, model.external_id)
    ).all()
    duplicate_names = _duplicate_names([(row[0], row[1]) for row in rows])
    missing_identifiers = [
        {"id": str(row[0]), "name": row[1]}
        for row in rows
        if not (row[2] and str(row[2]).strip())
    ]
    return {
        "duplicate_name_groups": duplicate_names,
        "missing_external_id_count": len(missing_identifiers),
        "missing_external_ids": missing_identifiers[:50],
        "entity_type": label,
    }


def _line_value(quantity: Decimal, unit_value: Decimal) -> Decimal:
    return quantity * unit_value


def _sale_total_mismatches(db: Session):
    rows = db.execute(
        select(
            SaleModel.id,
            SaleModel.invoice_number,
            SaleModel.total_amount,
            SaleModel.tax_amount,
            SaleModel.discount_amount,
            func.coalesce(func.sum(SaleLineModel.quantity * SaleLineModel.unit_price), 0),
        )
        .outerjoin(SaleLineModel, SaleLineModel.sale_id == SaleModel.id)
        .group_by(
            SaleModel.id,
            SaleModel.invoice_number,
            SaleModel.total_amount,
            SaleModel.tax_amount,
            SaleModel.discount_amount,
        )
    ).all()
    issues = []
    for sale_id, invoice, total, tax, discount, subtotal in rows:
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


def _purchase_total_mismatches(db: Session):
    rows = db.execute(
        select(
            PurchaseModel.id,
            PurchaseModel.invoice_number,
            PurchaseModel.total_amount,
            PurchaseModel.tax_amount,
            PurchaseModel.discount_amount,
            func.coalesce(func.sum(PurchaseLineModel.net_amount), 0),
        )
        .outerjoin(PurchaseLineModel, PurchaseLineModel.purchase_id == PurchaseModel.id)
        .group_by(
            PurchaseModel.id,
            PurchaseModel.invoice_number,
            PurchaseModel.total_amount,
            PurchaseModel.tax_amount,
            PurchaseModel.discount_amount,
        )
    ).all()
    issues = []
    for purchase_id, invoice, total, tax, discount, net_amount in rows:
        # net_amount is the canonical line amount after line-level discounts;
        # do not add header tax/discount again when reconciling purchases.
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


def _numeric_issues(db: Session):
    issues = []

    sale_lines = db.execute(
        select(SaleModel.invoice_number, SaleLineModel.quantity, SaleLineModel.unit_price)
        .join(SaleLineModel, SaleLineModel.sale_id == SaleModel.id)
    ).all()
    for invoice, quantity, unit_price in sale_lines:
        if Decimal(str(quantity)) <= 0:
            issues.append({"type": "sale_line_quantity", "invoice_number": invoice, "value": float(quantity)})
        if Decimal(str(unit_price)) < 0:
            issues.append({"type": "sale_line_unit_price", "invoice_number": invoice, "value": float(unit_price)})

    purchase_lines = db.execute(
        select(PurchaseModel.invoice_number, PurchaseLineModel.quantity, PurchaseLineModel.unit_cost)
        .join(PurchaseLineModel, PurchaseLineModel.purchase_id == PurchaseModel.id)
    ).all()
    for invoice, quantity, unit_cost in purchase_lines:
        if Decimal(str(quantity)) <= 0:
            issues.append({"type": "purchase_line_quantity", "invoice_number": invoice, "value": float(quantity)})
        if Decimal(str(unit_cost)) < 0:
            issues.append({"type": "purchase_line_unit_cost", "invoice_number": invoice, "value": float(unit_cost)})

    return issues


def audit_data_quality(db: Session, business_id: UUID, limit: int = 50) -> dict:
    """Read-only audit of identity, required fields and canonical financial values.

    This audit reports ambiguity and inconsistencies; it never chooses which
    duplicate entity or document is correct and never repairs data.
    """
    limit = max(1, min(limit, 200))

    # Scope every entity/document query to the requested business.
    def scoped_identity(model, label):
        rows = db.execute(
            select(model.id, model.name, model.external_id)
            .where(model.business_id == business_id)
        ).all()
        duplicate_names = _duplicate_names([(row[0], row[1]) for row in rows])
        missing_ids = [
            {"id": str(row[0]), "name": row[1]}
            for row in rows
            if not (row[2] and str(row[2]).strip())
        ]
        return {
            "entity_type": label,
            "duplicate_name_groups": duplicate_names[:limit],
            "duplicate_name_group_count": len(duplicate_names),
            "missing_external_id_count": len(missing_ids),
            "missing_external_ids": missing_ids[:limit],
        }

    sales = db.execute(
        select(SaleModel.id, SaleModel.invoice_number, SaleModel.transaction_date)
        .where(SaleModel.business_id == business_id)
    ).all()
    purchases = db.execute(
        select(PurchaseModel.id, PurchaseModel.invoice_number, PurchaseModel.transaction_date)
        .where(PurchaseModel.business_id == business_id)
    ).all()

    missing_sale_invoices = [
        {"id": str(row[0])} for row in sales if not str(row[1] or "").strip()
    ]
    missing_purchase_invoices = [
        {"id": str(row[0])} for row in purchases if not str(row[1] or "").strip()
    ]
    missing_sale_dates = [{"invoice_number": row[1]} for row in sales if row[2] is None]
    missing_purchase_dates = [{"invoice_number": row[1]} for row in purchases if row[2] is None]

    sale_total_issues = _sale_total_mismatches_for_business(db, business_id)
    purchase_total_issues = _purchase_total_mismatches_for_business(db, business_id)
    numeric = _numeric_issues_for_business(db, business_id)

    sections = {
        "customers": scoped_identity(CustomerModel, "customer"),
        "suppliers": scoped_identity(SupplierModel, "supplier"),
        "products": scoped_identity(ProductModel, "product"),
        "sales": {
            "missing_invoice_number_count": len(missing_sale_invoices),
            "missing_invoice_numbers": missing_sale_invoices[:limit],
            "missing_transaction_date_count": len(missing_sale_dates),
            "missing_transaction_dates": missing_sale_dates[:limit],
            "total_mismatches": sale_total_issues[:limit],
            "total_mismatch_count": len(sale_total_issues),
        },
        "purchases": {
            "missing_invoice_number_count": len(missing_purchase_invoices),
            "missing_invoice_numbers": missing_purchase_invoices[:limit],
            "missing_transaction_date_count": len(missing_purchase_dates),
            "missing_transaction_dates": missing_purchase_dates[:limit],
            "total_mismatches": purchase_total_issues[:limit],
            "total_mismatch_count": len(purchase_total_issues),
        },
        "numeric_issues": numeric[:limit],
        "numeric_issue_count": len(numeric),
    }

    issue_count = (
        sum(sections[x]["duplicate_name_group_count"] + sections[x]["missing_external_id_count"] for x in ("customers", "suppliers", "products"))
        + len(missing_sale_invoices)
        + len(missing_purchase_invoices)
        + len(missing_sale_dates)
        + len(missing_purchase_dates)
        + len(sale_total_issues)
        + len(purchase_total_issues)
        + len(numeric)
    )

    return {
        "status": "attention_required" if issue_count else "reconciled",
        "summary": {
            "issue_count": issue_count,
            "duplicate_entity_group_count": sum(sections[x]["duplicate_name_group_count"] for x in ("customers", "suppliers", "products")),
            "missing_identifier_count": sum(sections[x]["missing_external_id_count"] for x in ("customers", "suppliers", "products")),
            "missing_document_identity_count": len(missing_sale_invoices) + len(missing_purchase_invoices),
            "missing_transaction_date_count": len(missing_sale_dates) + len(missing_purchase_dates),
            "document_total_mismatch_count": len(sale_total_issues) + len(purchase_total_issues),
            "numeric_issue_count": len(numeric),
        },
        "sections": sections,
    }


def _sale_total_mismatches_for_business(db, business_id):
    rows = db.execute(
        select(
            SaleModel.invoice_number, SaleModel.total_amount, SaleModel.tax_amount,
            SaleModel.discount_amount,
            func.coalesce(func.sum(SaleLineModel.quantity * SaleLineModel.unit_price), 0),
        )
        .outerjoin(SaleLineModel, SaleLineModel.sale_id == SaleModel.id)
        .where(SaleModel.business_id == business_id)
        .group_by(SaleModel.id, SaleModel.invoice_number, SaleModel.total_amount, SaleModel.tax_amount, SaleModel.discount_amount)
    ).all()
    issues = []
    for invoice, total, tax, discount, subtotal in rows:
        expected = Decimal(str(subtotal)) + Decimal(str(tax)) - Decimal(str(discount))
        actual = Decimal(str(total))
        if abs(actual - expected) > Decimal("0.01"):
            issues.append({"invoice_number": invoice, "expected_total_from_lines": float(expected), "recorded_total": float(actual), "difference": float(actual - expected)})
    return issues


def _purchase_total_mismatches_for_business(db, business_id):
    rows = db.execute(
        select(
            PurchaseModel.invoice_number, PurchaseModel.total_amount,
            func.coalesce(func.sum(PurchaseLineModel.net_amount), 0),
        )
        .outerjoin(PurchaseLineModel, PurchaseLineModel.purchase_id == PurchaseModel.id)
        .where(PurchaseModel.business_id == business_id)
        .group_by(PurchaseModel.id, PurchaseModel.invoice_number, PurchaseModel.total_amount)
    ).all()
    issues = []
    for invoice, total, net_amount in rows:
        expected = Decimal(str(net_amount))
        actual = Decimal(str(total))
        if abs(actual - expected) > Decimal("0.01"):
            issues.append({"invoice_number": invoice, "expected_total_from_lines": float(expected), "recorded_total": float(actual), "difference": float(actual - expected)})
    return issues


def _numeric_issues_for_business(db, business_id):
    issues = []
    sale_lines = db.execute(
        select(SaleModel.invoice_number, SaleLineModel.quantity, SaleLineModel.unit_price)
        .join(SaleLineModel, SaleLineModel.sale_id == SaleModel.id)
        .where(SaleModel.business_id == business_id)
    ).all()
    for invoice, quantity, unit_price in sale_lines:
        if Decimal(str(quantity)) <= 0:
            issues.append({"type": "sale_line_quantity", "invoice_number": invoice, "value": float(quantity)})
        if Decimal(str(unit_price)) < 0:
            issues.append({"type": "sale_line_unit_price", "invoice_number": invoice, "value": float(unit_price)})
    purchase_lines = db.execute(
        select(PurchaseModel.invoice_number, PurchaseLineModel.quantity, PurchaseLineModel.unit_cost)
        .join(PurchaseLineModel, PurchaseLineModel.purchase_id == PurchaseModel.id)
        .where(PurchaseModel.business_id == business_id)
    ).all()
    for invoice, quantity, unit_cost in purchase_lines:
        if Decimal(str(quantity)) <= 0:
            issues.append({"type": "purchase_line_quantity", "invoice_number": invoice, "value": float(quantity)})
        if Decimal(str(unit_cost)) < 0:
            issues.append({"type": "purchase_line_unit_cost", "invoice_number": invoice, "value": float(unit_cost)})
    return issues
