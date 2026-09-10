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
discounting varies a lot by trade), and expense spike (EXPENSE_SPIKE, a
category's total spend vs. the prior period of equal length).

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
- **Inventory excess / stockout risk / demand spike** -- InventorySnapshot
  and InventoryMovement models exist, but nothing populates them yet (no
  ingestion path writes to either table) and no query/signal logic reads
  them. PRODUCT_SLOW_MOVING is a sales-velocity proxy for "slow-moving",
  not a real stock-on-hand calculation -- true inventory signals need
  actual snapshot/movement data flowing in first.

10 of 14 catalogued signal types are now wired. The one remaining gap
(true inventory signals) is blocked on a missing ingestion source type
(no inventory/stock-register file format is parsed anywhere), the same
shape of gap expense spike, discount anomaly, and purchase/supplier
signals were each in before their respective passes.
