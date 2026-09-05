from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from packages.shared.database.session import Base


class BusinessModel(Base):
    __tablename__ = "businesses"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class CustomerModel(Base):
    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("business_id", "external_id"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(64))
    email: Mapped[str | None] = mapped_column(String(255))
    credit_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))


class ProductModel(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("business_id", "sku"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    sku: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(255))
    unit: Mapped[str | None] = mapped_column(String(64))


class SupplierModel(Base):
    __tablename__ = "suppliers"
    __table_args__ = (UniqueConstraint("business_id", "external_id"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(64))
    email: Mapped[str | None] = mapped_column(String(255))
    credit_period_days: Mapped[int | None] = mapped_column()


class SourceFileModel(Base):
    __tablename__ = "source_files"
    __table_args__ = (UniqueConstraint("business_id", "checksum"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class SaleModel(Base):
    __tablename__ = "sales"
    __table_args__ = (UniqueConstraint("business_id", "invoice_number"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    customer_id: Mapped[UUID | None] = mapped_column(ForeignKey("customers.id"), index=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    invoice_number: Mapped[str] = mapped_column(String(255), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, index=True)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)


class SaleLineModel(Base):
    __tablename__ = "sale_lines"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    sale_id: Mapped[UUID] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    cost_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))


class PurchaseModel(Base):
    __tablename__ = "purchases"
    __table_args__ = (UniqueConstraint("business_id", "invoice_number"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    supplier_id: Mapped[UUID | None] = mapped_column(ForeignKey("suppliers.id"), index=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    invoice_number: Mapped[str] = mapped_column(String(255), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, index=True)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)


class PurchaseLineModel(Base):
    __tablename__ = "purchase_lines"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    purchase_id: Mapped[UUID] = mapped_column(ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)


class PaymentModel(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("direction IN ('in', 'out')", name="ck_payments_direction"),
        CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    customer_id: Mapped[UUID | None] = mapped_column(ForeignKey("customers.id"), index=True)
    supplier_id: Mapped[UUID | None] = mapped_column(ForeignKey("suppliers.id"), index=True)
    sale_id: Mapped[UUID | None] = mapped_column(ForeignKey("sales.id"), index=True)
    purchase_id: Mapped[UUID | None] = mapped_column(ForeignKey("purchases.id"), index=True)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(255))


class ExpenseModel(Base):
    __tablename__ = "expenses"
    __table_args__ = (CheckConstraint("amount > 0", name="ck_expenses_amount_positive"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class InventorySnapshotModel(Base):
    __tablename__ = "inventory_snapshots"
    __table_args__ = (UniqueConstraint("business_id", "product_id", "snapshot_date"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)


class InventoryMovementModel(Base):
    __tablename__ = "inventory_movements"
    __table_args__ = (
        CheckConstraint("movement_type IN ('purchase', 'sale', 'return_in', 'return_out', 'adjustment')", name="ck_inventory_movement_type"),
        CheckConstraint("quantity > 0", name="ck_inventory_movement_quantity_positive"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    movement_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    movement_type: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    reference: Mapped[str | None] = mapped_column(String(255))


class IngestionRunModel(Base):
    __tablename__ = "ingestion_runs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    source_file_id: Mapped[UUID] = mapped_column(ForeignKey("source_files.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    rows_read: Mapped[int] = mapped_column(default=0, nullable=False)
    rows_accepted: Mapped[int] = mapped_column(default=0, nullable=False)
    rows_rejected: Mapped[int] = mapped_column(default=0, nullable=False)
    error_summary: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
