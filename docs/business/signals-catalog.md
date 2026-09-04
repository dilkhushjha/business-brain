# Signals Catalog

Customer: decline, inactivity, payment deterioration.
Inventory: slow-moving, excess, stockout risk, demand spike.
Margin: deterioration, purchase-cost increase, discount anomaly.
Finance: receivable deterioration, expense spike.
Supplier: price increase, concentration.

## Implementation status

Wired into `detect_signals()` (signal code in parens): revenue decline/spike
(REVENUE_DECLINE/SPIKE), customer decline (CUSTOMER_REVENUE_DECLINE),
customer inactivity (CUSTOMER_INACTIVE), margin deterioration
(PRODUCT_MARGIN_DETERIORATION), receivable deterioration
(RECEIVABLE_OVERDUE), inventory slow-moving (PRODUCT_SLOW_MOVING, approximated
from a material drop in sales velocity -- there's no stock-on-hand tracking
in the schema to compute true days-of-inventory-remaining).

Not implemented, and blocked on schema/ingestion rather than just wiring:
- **Supplier price increase / concentration** -- there is no `Supplier` or
  `Purchase` table at all. Needs a schema migration and a new ingestion
  source type before any detection logic is possible.
- **Expense spike** -- same: no `Expense` table exists.
- **Discount anomaly** -- `SaleModel.discount_amount` exists in the schema,
  but ingestion (`packages/data/business_brain/ingestion/repository.py`)
  currently hard-codes it to 0 rather than parsing it from source files, so
  there's no real discount data to detect anomalies in yet. Fix ingestion
  first, then this becomes a wiring task like the others above.
- **Inventory excess / stockout risk** -- both need stock-on-hand data,
  which isn't tracked anywhere in the current schema.
