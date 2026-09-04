"""Backwards-compatible import path.

This module used to define its own KPI/growth/average_invoice_value,
independently of metrics.kpis -- two structurally identical classes with
the same name, in different modules. That "worked" only because nothing
here does an isinstance() check: monthly_sales_kpis() (via service.py)
returned instances of THIS module's KPI, while signals/rules.py and several
tests imported and type-hinted against metrics.kpis.KPI instead. Same shape,
different class objects -- a landmine waiting for anyone who adds a real
type check.

Re-exporting from metrics.kpis instead makes both import paths resolve to
the exact same objects, so existing `from .kpi_compat import KPI` call
sites (service.py) keep working unchanged, with no duplicate logic to
drift out of sync.
"""
from packages.analytics.business_brain.metrics.kpis import (  # noqa: F401
    KPI,
    average_invoice_value,
    growth,
)
