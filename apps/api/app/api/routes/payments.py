from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.api.connector_auth import require_business_access
from packages.shared.database.models import CustomerModel, PaymentModel, PurchaseModel, SaleModel, SupplierModel
from packages.shared.database.session import get_db

router = APIRouter(prefix="/payments", tags=["payments"])


class SupplierPaymentRequest(BaseModel):
    supplier_name: str | None = None
    amount: Decimal = Field(gt=0)
    payment_date: date
    reference: str | None = None
    invoice_number: str


class CustomerPaymentRequest(BaseModel):
    customer_name: str | None = None
    amount: Decimal = Field(gt=0)
    payment_date: date
    reference: str | None = None
    invoice_number: str


@router.post("/{business_id}/customer")
def record_customer_payment(
    business_id: UUID,
    request: CustomerPaymentRequest,
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_business_access),
):
    sale = db.scalar(select(SaleModel).where(SaleModel.business_id == business_id, SaleModel.invoice_number == request.invoice_number))
    if sale is None:
        raise HTTPException(status_code=404, detail="Sale invoice not found.")

    if request.customer_name:
        customer = db.scalar(select(CustomerModel).where(CustomerModel.business_id == business_id, CustomerModel.name == request.customer_name))
        if customer is None:
            raise HTTPException(status_code=404, detail="Customer not found.")
        if sale.customer_id is not None and sale.customer_id != customer.id:
            raise HTTPException(status_code=400, detail="Customer does not match the sale invoice.")
        if sale.customer_id is None:
            sale.customer_id = customer.id

    if sale.customer_id is None:
        raise HTTPException(status_code=400, detail="A customer is required for a customer payment.")

    outstanding = max(Decimal(sale.total_amount or 0) - Decimal(sale.paid_amount or 0), Decimal("0"))
    if request.amount > outstanding:
        raise HTTPException(status_code=400, detail=f"Payment exceeds invoice outstanding amount of {outstanding:.2f}.")

    payment = PaymentModel(
        business_id=business_id,
        customer_id=sale.customer_id,
        sale_id=sale.id,
        payment_date=request.payment_date,
        amount=request.amount,
        direction="in",
        reference=request.reference or request.invoice_number,
    )
    sale.paid_amount = Decimal(sale.paid_amount or 0) + request.amount
    db.add(payment)
    db.commit()
    db.refresh(payment)
    db.refresh(sale)

    remaining = max(Decimal(sale.total_amount) - Decimal(sale.paid_amount), Decimal("0"))
    return {
        "payment_id": str(payment.id),
        "invoice_number": sale.invoice_number,
        "payment_amount": float(request.amount),
        "paid_amount": float(sale.paid_amount),
        "remaining_receivable": float(remaining),
        "direction": payment.direction,
    }


@router.post("/{business_id}/supplier")
def record_supplier_payment(
    business_id: UUID,
    request: SupplierPaymentRequest,
    db: Session = Depends(get_db),
    _auth: dict = Depends(require_business_access),
):
    purchase = db.scalar(select(PurchaseModel).where(PurchaseModel.business_id == business_id, PurchaseModel.invoice_number == request.invoice_number))
    if purchase is None:
        raise HTTPException(status_code=404, detail="Purchase invoice not found.")

    if request.supplier_name:
        supplier = db.scalar(select(SupplierModel).where(SupplierModel.business_id == business_id, SupplierModel.name == request.supplier_name))
        if supplier is None:
            raise HTTPException(status_code=404, detail="Supplier not found.")
        if purchase.supplier_id is not None and purchase.supplier_id != supplier.id:
            raise HTTPException(status_code=400, detail="Supplier does not match the purchase invoice.")
        if purchase.supplier_id is None:
            purchase.supplier_id = supplier.id

    if purchase.supplier_id is None:
        raise HTTPException(status_code=400, detail="A supplier is required for a supplier payment.")

    outstanding = max(Decimal(purchase.total_amount or 0) - Decimal(purchase.paid_amount or 0), Decimal("0"))
    if request.amount > outstanding:
        raise HTTPException(status_code=400, detail=f"Payment exceeds invoice outstanding amount of {outstanding:.2f}.")

    payment = PaymentModel(
        business_id=business_id,
        supplier_id=purchase.supplier_id,
        purchase_id=purchase.id,
        payment_date=request.payment_date,
        amount=request.amount,
        direction="out",
        reference=request.reference or request.invoice_number,
    )
    purchase.paid_amount = Decimal(purchase.paid_amount or 0) + request.amount
    db.add(payment)
    db.commit()
    db.refresh(payment)
    db.refresh(purchase)

    remaining = max(Decimal(purchase.total_amount) - Decimal(purchase.paid_amount), Decimal("0"))
    return {
        "payment_id": str(payment.id),
        "invoice_number": purchase.invoice_number,
        "payment_amount": float(request.amount),
        "paid_amount": float(purchase.paid_amount),
        "remaining_payable": float(remaining),
        "direction": payment.direction,
    }
