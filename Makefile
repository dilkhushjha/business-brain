install:
	pip install -e ".[dev]"
api:
	uvicorn apps.api.app.main:app --reload
test:
	pytest
lint:
	ruff check .
up:
	docker compose up -d
down:
	docker compose down
seed-demo:
	python scripts/seed_demo_business.py
