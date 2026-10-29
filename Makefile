.PHONY: test lint up down repro feast-apply feast-materialize

PROFILE ?= local

# Run Python tests
test:
	pytest tests/

# Run formatting and linting
lint:
	ruff check . --fix

up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down

repro:
	dvc repro

train-local:
	@docker compose -f infra/docker-compose.yml up -d --quiet-pull
	@act push -W .github/workflows/train.yml --network act-network --secret-file .secrets.local

feast-apply:
	python feature_repo/main.py
	cp feature_repo/feature_store.$(PROFILE).yaml feature_repo/feature_store.yaml
	cd feature_repo && feast apply

feast-materialize:
	cd feature_repo && feast materialize-incremental $$(date -u +%Y-%m-%dT%H:%M:%S)