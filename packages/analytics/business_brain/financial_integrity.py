from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.shared.database.models import ExpenseModel, PaymentModel, PurchaseModel, SaleModel


def _d(value) -> Decimal:
    return Decimal(str(value or 0))


def audit_financial_linkage(db: Session, business_id: UUID) -> dict:
    """Audit invoice payment fields against payment ledger records.

    The audit deliberately reports differences instead of choosing which
    source is correct. Invoice paid_amount is document-level state; PaymentModel
    is the payment-event ledger.
    """
    sales = db.execute(
        select(SaleModel.id, SaleModel.invoice_number, SaleModel.paid_amount)
        .where(SaleModel.business_id == business_id)
    ).all()
    purchases = db.execute(
        select(PurchaseModel.id, PurchaseModel.invoice_number, PurchaseModel.paid_amount)
        .where(PurchaseModel.business_id == business_id)
    ).all()

    customer_payments = dict(
        db.execute(
            select(PaymentModel.sale_id, func.coalesce(func.sum(PaymentModel.amount), 0))
            .where(
                PaymentModel.business_id == business_id,
                PaymentModel.direction == "in",
                PaymentModel.sale_id.is_not(None),
            )
            .group_by(PaymentModel.sale_id)
        ).all()
    )
    supplier_payments = dict(
        db.execute(
            select(PaymentModel.purchase_id, func.coalesce(func.sum(PaymentModel.amount), 0))
            .where(
                PaymentModel.business_id == business_id,
                PaymentModel.direction == "out",
                PaymentModel.purchase_id.is_not(None),
            )
            .group_by(PaymentModel.purchase_id)
        ).all()
    )

    receivable_mismatches = []
    for sale_id, invoice, paid in sales:
        document_paid = _d(paid)
        ledger_paid = _d(customer_payments.get(sale_id))
        if document_paid != ledger_paid:
            receivable_mismatches.append({
                "invoice_number": invoice,
                "document_paid": float(document_paid),
                "payment_ledger_paid": float(ledger_paid),
                "difference": float(ledger_paid - document_paid),
            })

    payable_mismatches = []
    for purchase_id, invoice, paid in purchases:
        document_paid = _d(paid)
        ledger_paid = _d(supplier_payments.get(purchase_id))
        if document_paid != ledger_paid:
            payable_mismatches.append({
                "invoice_number": invoice,
                "document_paid": float(document_paid),
                "payment_ledger_paid": float(ledger_paid),
                "difference": float(ledger_paid - document_paid),
            })

    unlinked_rows = db.execute(
        select(PaymentModel.id, PaymentModel.direction, PaymentModel.amount, PaymentModel.reference)
        .where(
            PaymentModel.business_id == business_id,
            PaymentModel.sale_id.is_(None),
            PaymentModel.purchase_id.is_(None),
        )
    ).all()
    unlinked = [
        {
            "payment_id": str(payment_id),
            "direction": direction,
            "amount": float(amount),
            "reference": reference,
        }
        for payment_id, direction, amount, reference in unlinked_rows
    ]

    expense_total = _d(
        db.scalar(
            select(func.coalesce(func.sum(ExpenseModel.amount), 0))
            .where(ExpenseModel.business_id == business_id)
        )
    )

    issues = len(receivable_mismatches) + len(payable_mismatches) + len(unlinked)
    return {
        "status": "attention_required" if issues else "reconciled",
        "summary": {
            "receivable_mismatch_count": len(receivable_mismatches),
            "payable_mismatch_count": len(payable_mismatches),
            "unlinked_payment_count": len(unlinked),
            "expense_total": float(expense_total),
            "issue_count": issues,
        },
        "receivable_payment_mismatches": receivable_mismatches[:50],
        "payable_payment_mismatches": payable_mismatches[:50],
        "unlinked_payments": unlinked[:50],
    }
