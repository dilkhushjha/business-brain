from packages.shared.database.models import (
    Base,
    CustomerModel,
    ExpenseModel,
    InventoryMovementModel,
    InventorySnapshotModel,
    PaymentModel,
    ProductModel,
    PurchaseLineModel,
    PurchaseModel,
    SupplierModel,
)


def test_core_sme_tables_are_registered():
    expected = {
        "businesses",
        "customers",
        "products",
        "suppliers",
        "sales",
        "sale_lines",
        "purchases",
        "purchase_lines",
        "payments",
        "expenses",
        "inventory_snapshots",
        "inventory_movements",
        "source_files",
        "ingestion_runs",
    }

    assert expected.issubset(set(Base.metadata.tables))


def test_counterparty_models_expose_business_scope():
    for model in (CustomerModel, ProductModel, SupplierModel, ExpenseModel):
        assert "business_id" in model.__table__.c
        assert model.__table__.c.business_id.nullable is False


def test_purchase_model_supports_supplier_and_payable_state():
    columns = PurchaseModel.__table__.c

    assert {"supplier_id", "total_amount", "tax_amount", "discount_amount", "due_date", "paid_amount"}.issubset(columns)


def test_purchase_line_model_supports_product_level_costs():
    columns = PurchaseLineModel.__table__.c

    assert {"purchase_id", "product_id", "quantity", "unit_cost", "tax_amount", "discount_amount", "net_amount"}.issubset(columns)


def test_payment_model_supports_both_business_cash_directions():
    columns = PaymentModel.__table__.c

    assert {"customer_id", "supplier_id", "sale_id", "purchase_id", "amount", "direction"}.issubset(columns)
    constraint_names = {constraint.name for constraint in PaymentModel.__table__.constraints}
    assert "ck_payments_direction" in constraint_names
    assert "ck_payments_exactly_one_counterparty" in constraint_names


def test_inventory_models_support_snapshot_and_audit_trail():
    snapshot_columns = InventorySnapshotModel.__table__.c
    movement_columns = InventoryMovementModel.__table__.c

    assert {"product_id", "snapshot_date", "quantity", "value"}.issubset(snapshot_columns)
    assert {"product_id", "movement_date", "movement_type", "quantity", "unit_cost"}.issubset(movement_columns)

    snapshot_constraints = {constraint.name for constraint in InventorySnapshotModel.__table__.constraints}
    movement_constraints = {constraint.name for constraint in InventoryMovementModel.__table__.constraints}
    assert "ck_inventory_snapshots_quantity_nonnegative" in snapshot_constraints
    assert "ck_inventory_movement_type" in movement_constraints
