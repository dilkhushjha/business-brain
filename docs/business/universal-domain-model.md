# Universal Domain Model

Business Brain models the economic primitives needed to understand an SME
across sales, procurement, cash flow, inventory and operating expenses.

## Core primitives

- **Business** -- tenant boundary and business identity.
- **Customer** -- buyer identity and credit profile.
- **Product** -- item identity, SKU, category and unit of measure.
- **Supplier** -- vendor identity and procurement terms.
- **Sale / Invoice** -- customer transaction, tax, discount, receivable and
  payment state.
- **Purchase** -- supplier transaction, tax, discount, payable and payment
  state.
- **SaleLine / PurchaseLine** -- product-level quantity and economics.
- **Payment** -- inbound customer receipt or outbound supplier payment, with
  optional allocation to a sale or purchase.
- **InventorySnapshot** -- point-in-time stock quantity and valuation.
- **InventoryMovement** -- auditable stock changes from purchases, sales,
  returns or adjustments.
- **Expense** -- operating expenditure with category and source identity.

## Invariants

All operational records are scoped to a Business. External source identifiers
are retained where available for reconciliation and auditability. Monetary
values use fixed-precision decimals rather than floating point. Quantities use
higher precision decimals for units such as metres, kilograms or pieces.

Payments must have exactly one counterparty (customer or supplier), have a
positive amount, and declare direction (`in` or `out`). Inventory snapshots
cannot contain negative stock/value, while inventory movements require a
positive quantity and a supported movement type.

## Implementation

The canonical Pydantic contracts live in `packages/domain/business_brain/schema.py`.
Immutable domain entities live under `packages/domain/business_brain/entities/`.
The SQLAlchemy persistence model lives in `packages/shared/database/models.py`.
Database migrations `0003_core_sme_domain` and `0004_domain_invariants` create
and constrain the expanded model.

Retail extensions can include size, color, style and season. Distribution
extensions can include lead time, credit period, procurement price and reorder
quantity.
