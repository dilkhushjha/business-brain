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
stock tying up capital), demand spike (DEMAND_SPIKE, the symmetric
opposite of PRODUCT_SLOW_MOVING -- a material sales-velocity *increase*
vs. the prior period, same comparison machinery), and dead stock
(DEAD_STOCK, real stock-on-hand with literally zero sales over a longer
trailing window -- the case stock_risk() deliberately excludes since a
days-of-cover ratio isn't meaningful at zero velocity, detected on its
own terms via `metrics.inventory.dead_stock()` instead).

**All 14 catalogued signal types are now wired.**

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

Inventory ingestion (`/ingestion/import-inventory/{business_id}` ->
`packages/data/business_brain/ingestion/inventory_repository.py`) needed
its own validation rules for the same reason expenses did -- a Tally
Stock Summary export has no invoice_number, no customer/supplier, no line
items, just one row per item as of a date (`prepare_inventory_file()` in
orchestrator.py). Unlike expenses, InventorySnapshotModel has a real
natural key (business_id, product_id, snapshot_date) with a unique
constraint, so reconciling a re-exported snapshot is a straightforward
upsert, not the exact-match fallback expenses need.

Verified with real CSV files, through the real ingestion path, into
firing STOCKOUT_RISK and DEAD_STOCK signals -- not hand-built fixtures
(tests/integration/test_inventory_pipeline_e2e.py). The dashboard's
inventory card (apps/web/components/InventoryIntelligence.tsx) prefers
this real stock-risk data when available, falling back to the
sales-velocity proxy view (with its existing honest caveat) when it isn't.

## What's still genuinely open, distinct from catalog coverage

- **InventoryMovement-based tracking** -- InventorySnapshotModel is
  ingested and drives every inventory signal above.
  InventoryMovementModel (a full per-transaction stock ledger) is still
  unused -- largely redundant with what Sale/PurchaseLine already
  capture, and wasn't needed to get real inventory signals working.
- **PaymentModel** -- still unused schema. No ingestion path writes to
  it and nothing reads it; Sale.paid_amount/Purchase.paid_amount already
  drive receivables/payables without it.
- **Signal thresholds are reasonable defaults, not calibrated** -- every
  threshold in this file (10% margin, 40% velocity drop, 100% demand
  spike, 7/90-day stock cover, etc.) is a defensible guess, not a number
  tuned against a real business's data. The pilot plan's own success
  criteria (signal usefulness) requires exactly that kind of validation,
  which hasn't happened yet.
