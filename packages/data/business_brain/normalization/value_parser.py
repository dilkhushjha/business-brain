from datetime import date, datetime
from decimal import Decimal, InvalidOperation


def parse_decimal(value: object) -> Decimal | None:
    if value is None or str(value).strip() == "":
        return None
    text = str(value).strip().replace(",", "").replace("₹", "")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def parse_date(value: object) -> date | None:
    if value is None or str(value).strip() == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d-%b-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None
