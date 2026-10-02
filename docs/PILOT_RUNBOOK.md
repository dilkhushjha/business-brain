# Business Brain V1 — Real-Business Pilot Runbook

This runbook is for a supervised, read-only pilot. Do not use a live business as a test database, and do not treat a green readiness result as proof that every business conclusion is correct.

## 1. Pilot boundary

Start with one business and one accountable owner. The initial pilot is for observing data ingestion, reconciliation, business metrics, signals, and decision support. Business Brain does not execute recommendations or change source records.

Use a dedicated business workspace. Keep the source system (Tally/Excel/CSV) as the record of truth during the pilot.

## 2. Before importing

- Confirm the business owner has authorized the data upload.
- Agree which date range will be imported and which source files are in scope.
- Keep an untouched copy of every source file.
- Confirm the business name, industry, currency, timezone, and fiscal-year start.
- Identify the meaning of each source column and whether amounts are tax-inclusive.
- Confirm how returns, credit notes, partial payments, and opening stock are represented.
- Do not upload customer or supplier data that the owner has not approved for this pilot.

## 3. Import sequence

1. Import customer/product/supplier masters where available.
2. Import purchase documents for the agreed period.
3. Import sales documents for the same period.
4. Review every preview and rejected row before committing.
5. Record the source file names, date range, row counts, and import summary.
6. Do not resolve ambiguous product/customer/supplier matches by silently merging names.

If a file is rejected or a total does not reconcile, stop and resolve it with the business owner before interpreting downstream metrics.

## 4. Run the integrity and readiness checks

After import and after any correction, open **Data & Imports → Data Integrity**.

Review these checks:
- Imported-data quality: ambiguous entity names, missing document identity/date, invalid values, and document totals.
- Inventory ledger: purchase/sale line reconciliation, orphan movements, and negative movement-derived balances.
- Financial linkage: document paid amounts versus linked payment ledger entries, plus unlinked payments.
- Pilot readiness: blockers and warnings, including data freshness and future-dated documents.

A `ready` result means the configured pilot gates passed; `ready_with_warnings` requires explicit review; `not_ready` means do not proceed to business interpretation until blockers are addressed. A clean audit only covers the checks currently implemented.

## 5. Validate a small sample against the source

Choose at least:
- 5 sales invoices (or all, if fewer)
- 5 purchase invoices (or all, if fewer)
- 3 products with purchase, sale, and remaining stock
- 3 customer balances and 3 supplier balances, where available

For each sample, compare the source document with the imported document and related ledger entries. Record discrepancies and the owner's explanation. Do not assume a mismatch is a software defect until source semantics (tax, discount, returns, dates, and payment allocation) are confirmed.

## 6. Review Business Brain conclusions

For each high-priority situation:
1. Open the supporting evidence.
2. Confirm the relevant source records.
3. Check whether the explanation distinguishes evidence from hypothesis.
4. Review the recommended investigation/action with the owner.
5. Record whether the recommendation was useful, unclear, or incorrect.

Do not use a situation or recommendation as an instruction to make a financial, procurement, staffing, or pricing decision without human review.

## 7. Pilot exit criteria

A pilot can move to a broader evaluation only when:
- the owner confirms the imported period and source files are representative;
- all blockers are resolved;
- remaining warnings are documented and accepted;
- sampled documents and balances have been checked against the source;
- false positives, missed issues, and confusing explanations are recorded;
- the owner understands that recommendations are decision support, not automated decisions.

## 8. Known limitations to disclose

- Readiness is a gate over implemented checks, not a certification of accounting correctness.
- Inventory derived from movements may not reflect opening stock or adjustments unless those are represented correctly in the source ledger.
- Document paid amounts and payment-ledger entries can differ in timing or allocation; investigate rather than assuming either is authoritative.
- Missing source data is not estimated. In particular, do not interpret an unavailable cash position as zero.
- Situation prioritization is an explainable heuristic, not a forecast or guarantee.

## 9. Pilot log template

| Field | Value |
|---|---|
| Business / owner | |
| Pilot start and end dates | |
| Source systems and files | |
| Imported date range | |
| Sales / purchase rows accepted | |
| Readiness status | |
| Open blockers / warnings | |
| Sample reconciliation outcome | |
| Incorrect or missed signals | |
| Owner feedback | |
| Go / pause decision and rationale | |
