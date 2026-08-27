from decimal import Decimal


def gross_profit(revenue: Decimal, cost_of_goods_sold: Decimal) -> Decimal:
    return revenue - cost_of_goods_sold


def gross_margin(revenue: Decimal, cost_of_goods_sold: Decimal) -> Decimal | None:
    if revenue == 0:
        return None
    return (revenue - cost_of_goods_sold) / revenue
