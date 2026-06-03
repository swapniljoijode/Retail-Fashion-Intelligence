.PHONY: setup seed seed-large upload bronze ingest dbt-run dbt-run-snowflake dbt-test dbt-docs dbt-build test test-ci lint lint-fix pipeline up down clean help

# ── Environment ───────────────────────────────────────────────────────────────
setup:
	uv sync --all-extras
	uv run pre-commit install --install-hooks
	@echo "Environment ready. Copy .env.example to .env and fill in credentials."

# ── Data generation ───────────────────────────────────────────────────────────
seed:
	uv run python -m data_generation.main --volume small

seed-large:
	uv run python -m data_generation.main --volume large

# ── Ingestion ─────────────────────────────────────────────────────────────────
upload:  ## Upload Parquet output to Cloudflare R2 (requires R2_* env vars)
	uv run python -m ingestion.upload_r2

bronze:  ## Load Parquet into DuckDB bronze layer (local, no cloud credentials needed)
	uv run python -m ingestion.bronze_load --source-dir data_generation/output --db-path data/fashion_retail.duckdb

bronze-reset:  ## Drop and reload all DuckDB bronze tables from scratch
	uv run python -m ingestion.bronze_load --source-dir data_generation/output --db-path data/fashion_retail.duckdb --reset

ingest: upload bronze  ## Upload to R2 then load bronze layer

# ── dbt ───────────────────────────────────────────────────────────────────────
dbt-run:
	cd dbt && uv run dbt run --target duckdb

dbt-run-snowflake:
	cd dbt && uv run dbt run --target snowflake

dbt-test:
	cd dbt && uv run dbt test --target duckdb

dbt-docs:
	cd dbt && uv run dbt docs generate --target duckdb
	cd dbt && uv run dbt docs serve

dbt-build:
	cd dbt && uv run dbt build --target duckdb

# ── Testing ───────────────────────────────────────────────────────────────────
test:
	uv run pytest tests/ -v

test-ci:
	uv run pytest tests/ -v --tb=short --no-header

# ── Linting ───────────────────────────────────────────────────────────────────
lint:
	uv run ruff check .
	uv run black --check .
	cd dbt && uv run sqlfluff lint --dialect snowflake models/

lint-fix:
	uv run ruff check --fix .
	uv run black .
	cd dbt && uv run sqlfluff fix --dialect snowflake models/

# ── Pipeline (end-to-end local run) ──────────────────────────────────────────
pipeline:
	$(MAKE) seed
	$(MAKE) ingest
	$(MAKE) dbt-build
	@echo "Pipeline complete."

# ── Docker ────────────────────────────────────────────────────────────────────
up:
	docker compose -f docker/docker-compose.yml up -d

down:
	docker compose -f docker/docker-compose.yml down

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf data_generation/output/ 2>/dev/null || true

# ── Help ─────────────────────────────────────────────────────────────────────
help:
	@echo "Fashion Retail Intelligence Platform — task runner"
	@echo ""
	@echo "  make setup          Install dependencies and pre-commit hooks"
	@echo "  make seed           Generate synthetic data (small volume)"
	@echo "  make seed-large     Generate synthetic data (large volume)"
	@echo "  make upload         Upload Parquet to Cloudflare R2 (needs R2_* env vars)
  make bronze         Load Parquet into DuckDB bronze layer (local, free)
  make bronze-reset   Drop and reload all DuckDB bronze tables from scratch
  make ingest         Upload to R2 then load bronze layer"
	@echo "  make dbt-run        Run dbt models against DuckDB"
	@echo "  make dbt-test       Run dbt tests against DuckDB"
	@echo "  make dbt-docs       Generate and serve dbt docs"
	@echo "  make dbt-build      dbt run + test in one step"
	@echo "  make test           Run pytest suite"
	@echo "  make lint           Check code style (ruff, black, sqlfluff)"
	@echo "  make lint-fix       Auto-fix code style issues"
	@echo "  make pipeline       Full end-to-end local run"
	@echo "  make up             Start Docker Compose stack"
	@echo "  make down           Stop Docker Compose stack"
	@echo "  make clean          Remove generated artifacts and caches"
