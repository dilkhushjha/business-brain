"""Shared fixtures for DB-backed integration tests.

Every analytics/metrics function in this codebase takes `db: Session` as an
explicit parameter rather than reaching for a global session, so tests can
hand them a fully isolated in-memory SQLite session instead of touching the
real Postgres database or any global engine/session state.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from packages.shared.database.models import (
    BusinessModel,
    CustomerModel,
    ProductModel,
    SaleLineModel,
    SaleModel,
)
from packages.shared.database.session import Base


@pytest.fixture()
def db_session():
    """A fresh in-memory SQLite database, schema created from the real
    SQLAlchemy models, torn down at the end of the test.

    poolclass=StaticPool is required, not optional, once any test exercises
    code through FastAPI's TestClient: FastAPI runs endpoint functions in a
    worker thread via run_in_threadpool, and SQLAlchemy's default pooling
    for sqlite:///:memory: hands out a distinct (and therefore blank)
    in-memory database per thread. StaticPool forces every checkout,
    regardless of thread, to reuse the exact same connection, so a table
    created by test setup code is actually visible to the request handler.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


class Seeder:
    """Small builder for populating a test database with sales data.

    Several metric functions (declining_customers, margin_summary,
    overdue_customers, ...) key off date.today() internally rather than an
    `as_of` parameter, so this seeder works in days-ago offsets from today
    rather than fixed calendar dates.
    """

    def __init__(self, db: Session):
        self.db = db

    def business(self, name: str = "Test Business", industry: str = "distribution") -> BusinessModel:
        business = BusinessModel(id=uuid4(), name=name, industry=industry)
        self.db.add(business)
        self.db.commit()
        return business

    def customer(self, business_id: UUID, name: str) -> CustomerModel:
        customer = CustomerModel(id=uuid4(), business_id=business_id, external_id=name, name=name)
        self.db.add(customer)
        self.db.commit()
        return customer

    def product(self, business_id: UUID, name: str, sku: str | None = None) -> ProductModel:
        product = ProductModel(id=uuid4(), business_id=business_id, sku=sku or name, name=name)
        self.db.add(product)
        self.db.commit()
        return product

    def sale(
        self,
        business_id: UUID,
        *,
        customer_id: UUID | None = None,
        days_ago: int = 0,
        total_amount: Decimal | float = 0,
        paid_amount: Decimal | float = 0,
        due_days_ago: int | None = None,
        invoice_number: str | None = None,
    ) -> SaleModel:
        txn_date = date.today() - timedelta(days=days_ago)
        due_date = date.today() - timedelta(days=due_days_ago) if due_days_ago is not None else None
        sale = SaleModel(
            id=uuid4(),
            business_id=business_id,
            customer_id=customer_id,
            transaction_date=txn_date,
            invoice_number=invoice_number or f"INV-{uuid4().hex[:8]}",
            total_amount=Decimal(str(total_amount)),
            paid_amount=Decimal(str(paid_amount)),
            due_date=due_date,
        )
        self.db.add(sale)
        self.db.commit()
        return sale

    def sale_line(
        self,
        sale_id: UUID,
        product_id: UUID,
        *,
        quantity: Decimal | float = 1,
        unit_price: Decimal | float = 0,
        cost_price: Decimal | float | None = None,
    ) -> SaleLineModel:
        line = SaleLineModel(
            id=uuid4(),
            sale_id=sale_id,
            product_id=product_id,
            quantity=Decimal(str(quantity)),
            unit_price=Decimal(str(unit_price)),
            cost_price=None if cost_price is None else Decimal(str(cost_price)),
        )
        self.db.add(line)
        self.db.commit()
        return line

    def sale_with_line(
        self,
        business_id: UUID,
        product_id: UUID,
        *,
        customer_id: UUID | None = None,
        days_ago: int = 0,
        quantity: Decimal | float = 1,
        unit_price: Decimal | float = 100,
        cost_price: Decimal | float | None = None,
        due_days_ago: int | None = None,
        paid_amount: Decimal | float = 0,
    ) -> SaleModel:
        """Convenience: one sale with a single matching sale line, amount
        derived from quantity * unit_price (matching how revenue is computed
        from sale_lines in margin.py / kpis.py)."""
        total = Decimal(str(quantity)) * Decimal(str(unit_price))
        sale = self.sale(
            business_id,
            customer_id=customer_id,
            days_ago=days_ago,
            total_amount=total,
            paid_amount=paid_amount,
            due_days_ago=due_days_ago,
        )
        self.sale_line(sale.id, product_id, quantity=quantity, unit_price=unit_price, cost_price=cost_price)
        return sale


@pytest.fixture()
def seeder(db_session: Session) -> Seeder:
    return Seeder(db_session)
