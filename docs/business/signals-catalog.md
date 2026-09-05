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
from a material drop in sales velocity).

The core domain now contains Supplier, Purchase/PurchaseLine, Payment,
Expense, InventorySnapshot and InventoryMovement persistence models. These
models provide the data foundation for the remaining supplier, procurement,
expense and true inventory signals, but the corresponding ingestion and
detection logic is intentionally not claimed as implemented yet.

Not yet implemented:
- **Supplier price increase / concentration** -- requires supplier and
  purchase ingestion plus comparative procurement analytics.
- **Expense spike** -- requires expense ingestion plus historical baselines.
- **Discount anomaly** -- discount data is now preserved during production
  ingestion; detection still needs to be wired to the signal engine.
- **Inventory excess / stockout risk / demand spike** -- true detection needs
  inventory snapshots/movements plus sales velocity and coverage calculations.
