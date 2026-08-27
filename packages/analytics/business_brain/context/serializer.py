from dataclasses import asdict
from decimal import Decimal

from packages.analytics.business_brain.context.models import BusinessContext


def _json_safe(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def serialize_context(context: BusinessContext) -> dict:
    return _json_safe(asdict(context))
