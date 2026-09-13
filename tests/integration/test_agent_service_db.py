"""End-to-end tests for packages.agent.business_brain.agent.service.answer().

This is the function actually wired to POST /agent/{business_id}/ask, and
before this file, it had never been tested against a real database at
all -- only render_grounded_response() was tested, with hand-built context
dicts. This proves the whole chain (real seeded data -> build_business_context
-> classify_intent -> render_grounded_response) actually works together for
each of the newly-added intents, the same way test_ingestion_pipeline_e2e.py
and test_signal_engine_db.py proved their own layers end to end rather than
trusting unit tests in isolation.
"""
from datetime import date
from decimal import Decimal

from packages.agent.business_brain.agent.service import answer


def test_margin_question_is_grounded_from_real_data(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Clearance Item")
    seeder.sale_with_line(business.id, product.id, days_ago=5, quantity=10, unit_price=50, cost_price=60)

    result = answer(db_session, business.id, "Why is my margin so low?", date.today())
    assert result.intent == "margin_analysis"
    assert result.confidence == "grounded"
    assert "Clearance Item" in result.answer


def test_receivables_question_is_grounded_from_real_data(db_session, seeder):
    business = seeder.business()
    customer = seeder.customer(business.id, "ABC Electrical")
    seeder.sale(business.id, customer_id=customer.id, total_amount=Decimal("45000"),
                paid_amount=Decimal("0"), due_days_ago=75)

    result = answer(db_session, business.id, "Who owes me money?", date.today())
    assert result.intent == "receivables_analysis"
    assert result.confidence == "grounded"
    assert "ABC Electrical" in result.answer


def test_payables_question_is_grounded_from_real_data(db_session, seeder):
    business = seeder.business()
    supplier = seeder.supplier(business.id, "ABC Distributors")
    seeder.purchase(business.id, supplier_id=supplier.id, total_amount=Decimal("45000"),
                     paid_amount=Decimal("0"), due_days_ago=75)

    result = answer(db_session, business.id, "What bills do I have due?", date.today())
    assert result.intent == "payables_analysis"
    assert result.confidence == "grounded"
    assert "ABC Distributors" in result.answer


def test_supplier_question_is_grounded_from_real_data(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "LED Bulb 9W")
    supplier = seeder.supplier(business.id, "ABC Distributors")
    seeder.purchase_with_line(business.id, product.id, supplier_id=supplier.id,
                               days_ago=45, quantity=100, unit_cost=50)
    seeder.purchase_with_line(business.id, product.id, supplier_id=supplier.id,
                               days_ago=5, quantity=100, unit_cost=70)

    result = answer(db_session, business.id, "Have my suppliers raised prices?", date.today())
    assert result.intent == "supplier_analysis"
    assert result.confidence == "grounded"
    assert "ABC Distributors" in result.answer


def test_customer_question_is_grounded_from_real_data(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Widget")
    customer = seeder.customer(business.id, "Acme Traders")
    seeder.sale_with_line(business.id, product.id, customer_id=customer.id,
                           days_ago=45, quantity=1, unit_price=20000)
    seeder.sale_with_line(business.id, product.id, customer_id=customer.id,
                           days_ago=5, quantity=1, unit_price=5000)

    result = answer(db_session, business.id, "Which customers are at risk?", date.today())
    assert result.intent == "customer_analysis"
    assert result.confidence == "grounded"
    assert "Acme Traders" in result.answer


def test_product_question_is_grounded_from_real_data(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Winter Jacket")
    seeder.sale_with_line(business.id, product.id, days_ago=45, quantity=20, unit_price=100)
    seeder.sale_with_line(business.id, product.id, days_ago=5, quantity=2, unit_price=100)

    result = answer(db_session, business.id, "Which products aren't selling well?", date.today())
    assert result.intent == "product_analysis"
    assert result.confidence == "grounded"
    assert "Winter Jacket" in result.answer


def test_root_cause_question_cites_a_real_signal(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "Widget")
    customer = seeder.customer(business.id, "Acme Traders")
    seeder.sale_with_line(business.id, product.id, customer_id=customer.id,
                           days_ago=45, quantity=1, unit_price=20000)
    seeder.sale_with_line(business.id, product.id, customer_id=customer.id,
                           days_ago=5, quantity=1, unit_price=5000)

    result = answer(db_session, business.id, "Why is this happening to my business?", date.today())
    assert result.intent == "root_cause"
    assert result.confidence == "grounded"
    assert "Acme Traders" in result.answer


def test_margin_question_on_healthy_business_is_not_grounded(db_session, seeder):
    """The agent shouldn't claim confidence it doesn't have -- a business
    with no cost data at all should get an honest 'insufficient evidence'
    answer, not a fabricated margin figure."""
    business = seeder.business()
    result = answer(db_session, business.id, "Why is my margin so low?", date.today())
    assert result.confidence == "insufficient_evidence"
    assert "don't have enough" in result.answer


def test_expense_question_is_grounded_from_real_data(db_session, seeder):
    business = seeder.business()
    seeder.expense(business.id, days_ago=45, category="Transport", amount=Decimal("5000"))
    seeder.expense(business.id, days_ago=5, category="Transport", amount=Decimal("12000"))

    result = answer(db_session, business.id, "Why are my expenses so high?", date.today())
    assert result.intent == "expense_analysis"
    assert result.confidence == "grounded"
    assert "Transport" in result.answer


def test_stock_question_is_grounded_from_real_data(db_session, seeder):
    business = seeder.business()
    product = seeder.product(business.id, "LED Bulb 9W")
    seeder.sale_with_line(business.id, product.id, days_ago=5, quantity=300, unit_price=10)
    seeder.inventory_snapshot(business.id, product.id, days_ago=1, quantity=20, value=200)

    result = answer(db_session, business.id, "Which products aren't selling well?", date.today())
    assert result.intent == "product_analysis"
    assert result.confidence == "grounded"
    assert "LED Bulb 9W" in result.answer
