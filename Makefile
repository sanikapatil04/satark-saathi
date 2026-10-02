.PHONY: dev test lint migrate

dev:
	docker compose -f docker-compose.dev.yml up --build

test:
	python -m pytest apps/api/tests
	cd apps/web && npm run typecheck && npm run build

lint:
	python -m ruff check apps/api
	python -m mypy apps/api
	cd apps/web && npm run lint && npm run format

migrate:
	cd apps/api && alembic upgrade head
