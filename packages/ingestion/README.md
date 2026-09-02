# packages/ingestion (legacy)

This package predates `packages/data/business_brain/ingestion`, which is the
ingestion pipeline actually used by the API (`apps/api/app/api/routes/ingestion.py`)
and the connector. It duplicates a subset of that functionality with a
different (simpler, `difflib`-based) field-mapping heuristic and no
Tally-specific handling (report preambles, GST columns, quoted amounts, etc.).

Nothing outside this package's own tests imports from here. Keeping it around
is a source of confusion — two "suggest a column mapping" implementations
with different alias lists and different results for the same input column
name. New ingestion work should go in `packages/data/business_brain/ingestion`
and `packages/data/business_brain/normalization`.

This package is kept for now only because its tests exercise it; it should be
removed (and the tests either deleted or ported to the canonical package)
once nothing depends on it.
