# Domain Ingestion Persistence

This milestone wires canonical business-domain records into persistence without changing the dashboard contract.

## Invariants

- Every persisted record belongs to exactly one business.
- Source identity/fingerprint is retained for auditability.
- Monetary values are normalized before persistence.
- Replaying the same source is idempotent.
- Failed imports leave no partial business data.
- Unresolved references remain explicit rather than being invented.
