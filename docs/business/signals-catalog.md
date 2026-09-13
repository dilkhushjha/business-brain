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
from a material drop in sales velocity), payable/payment deterioration
(PAYABLE_OVERDUE, the payables-side mirror of receivable deterioration),
supplier price increase (SUPPLIER_PRICE_INCREASE, quantity-weighted average
purchase cost per product/supplier vs. the prior period), discount
anomaly (DISCOUNT_ANOMALY, an invoice's discount rate vs. this business's
own recent average -- not a fixed external threshold, since normal
discounting varies a lot by trade), expense spike (EXPENSE_SPIKE, a
category's total spend vs. the prior period of equal length), stockout
risk (STOCKOUT_RISK) and excess inventory (EXCESS_INVENTORY, both from
`metrics.inventory.stock_risk()`: current stock-on-hand from a real
InventorySnapshot divided by recent sales velocity gives days-of-cover;
low days-of-cover is a stockout risk, very high days-of-cover is excess
stock tying up capital).

Purchase-register ingestion now exists end to end
(`/ingestion/import-purchases/{business_id}` ->
`packages/data/business_brain/ingestion/purchase_repository.py`), reusing
the same generic column-mapper canonical fields the sales pipeline uses
(unit_price/total_amount/etc., relabeled to unit_cost/net_amount for
PurchaseLineModel) rather than a parallel alias system, and mirrors the
sales pipeline's per-invoice reconciliation behavior. Supplier concentration
(GET /supplier-risk/{business_id}/concentration, spend-share mirror of
customer concentration) and payables aging (GET
/payables/{business_id}/summary, mirror of receivables aging) are also live.
Verified with a real CSV file, through the real ingestion path, into a
firing SUPPLIER_PRICE_INCREASE signal -- not just a hand-built fixture
(tests/integration/test_ingestion_pipeline_e2e.py).

Expense ingestion (`/ingestion/import-expenses/{business_id}` ->
`packages/data/business_brain/ingestion/expense_repository.py`) required its
own validation rule set (`prepare_expense_file()` in orchestrator.py), not a
reuse of `prepare_file()`: a real Tally expense/payment voucher register
commonly has no distinct voucher-number column at all, and `prepare_file()`
hard-requires `invoice_number` for every row (correct for sales/purchase
registers, wrong for expenses). Confirmed this was a real problem, not a
hypothetical one, before building the fix -- the same CSV that
`prepare_expense_file()` accepts is rejected outright by `prepare_file()`
(`tests/integration/test_expense_pipeline_e2e.py`). Also has no natural
invoice-number-style unique key for reconciliation the way sales/purchases
do (`ExpenseModel.external_id` has no unique constraint, and most real
expense exports won't populate it) -- falls back to exact-match dedup
(date + category + amount + description) when no voucher number is present.

Not yet implemented:
- **Demand spike** -- not built as its own signal. slow_moving_products()
  already detects a material velocity *drop*; a symmetric "material
  velocity *increase*" detector would be a small addition on top of the
  same current-vs-previous-window machinery, but hasn't been written.
- **InventoryMovement-based tracking** -- InventorySnapshotModel is now
  ingested (a Tally Stock Summary export: closing quantity/value per item
  as of a date) and drives STOCKOUT_RISK/EXCESS_INVENTORY above.
  InventoryMovementModel (a full per-transaction stock ledger) is still
  unused -- largely redundant with what Sale/PurchaseLine already capture,
  and wasn't needed to get real stockout/excess detection working.
- **Dead stock** (stock on hand with zero recent sales velocity) --
  stock_risk() deliberately excludes products with zero velocity, since
  dividing by zero isn't meaningful for a days-of-cover calculation. A
  product with real stock and truly no sales isn't "excess" by this
  measure, it's a different, currently-undetected problem.

12 of 14 catalogued signal types are now wired (accounting demand spike
and dead stock as distinct from what's listed above). Inventory ingestion
(`/ingestion/import-inventory/{business_id}` ->
`packages/data/business_brain/ingestion/inventory_repository.py`) needed
its own validation rules for the same reason expenses did -- a Tally
Stock Summary export has no invoice_number, no customer/supplier, no line
items, just one row per item as of a date (`prepare_inventory_file()` in
orchestrator.py). Unlike expenses, InventorySnapshotModel has a real
natural key (business_id, product_id, snapshot_date) with a unique
constraint, so reconciling a re-exported snapshot is a straightforward
upsert, not the exact-match fallback expenses need.

Verified with a real CSV file, through the real ingestion path
(prepare_inventory_file + persist_inventory_snapshots), into a firing
STOCKOUT_RISK signal -- not a hand-built fixture
(tests/integration/test_inventory_pipeline_e2e.py). The dashboard's
inventory card (apps/web/components/InventoryIntelligence.tsx) now
prefers this real stock-risk data when available, falling back to the
sales-velocity proxy view (with its existing honest caveat) when it isn't.
