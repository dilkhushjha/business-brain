# Real-business pilot

Business Brain V1 is ready for a controlled SME pilot when the pilot business passes the readiness gate.

## Pilot flow

1. Create the business and owner account.
2. Import a representative sales history.
3. Import purchase history when available.
4. Verify the import summary and re-import behavior.
5. Run the readiness check:

```
GET /api/pilot/{business_id}/readiness
```

Optionally provide an explicit `as_of=YYYY-MM-DD`.

6. Resolve every blocker before relying on Business Brain conclusions.
7. Review warnings and record which intelligence domains are intentionally unavailable.
8. Compare Business Brain outputs with the owner's source records for a fixed review period.
9. Record false positives, missed issues, and data-mapping problems separately from model/reasoning issues.

## Readiness rules

- Sales data is required because the current V1 is sales-led.
- Purchase data is recommended; without it, procurement, supplier, inventory-cost and COGS intelligence is limited.
- Customer, supplier and product masters are recommended but missing masters are warnings rather than automatic blockers.
- Data-quality, inventory and financial-linkage integrity exceptions are blockers. Business Brain should not be treated as fully trusted while those exceptions remain unresolved.
- The readiness endpoint is a gate, not a business-performance score.

## Pilot acceptance

For the first real business, validate:

- Revenue and invoice counts against the source.
- Purchase totals against the source.
- Inventory movement for a sample of products.
- Receivables/payables against the source ledger.
- At least five Business Brain signals against manually reviewed evidence.
- Every generated situation against its supporting signals.
- Every decision action against the situation evidence.
- Situation history after a second refresh, including improvement and resolution behavior.

The pilot should preserve source files and the date range used for reconciliation so discrepancies can be reproduced.
