.PHONY: setup seed seed-large upload bronze bronze-reset ingest \
        dbt-deps dbt-run dbt-run-snowflake dbt-test dbt-docs dbt-build dbt-clean \
        airflow-init airflow-up airflow-down airflow-logs airflow-trigger airflow-backfill \
        docker-build docker-test docker-test-all docker-pipeline \
        export-snapshot dashboard-install dashboard-dev dashboard-build \
        test test-all test-ci lint lint-fix pipeline ci up down clean help

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
dbt-deps:  ## Install dbt packages (dbt-expectations) — run once after clone or packages.yml change
	cd dbt && uv run dbt deps --profiles-dir .

dbt-run:  ## Run dbt models against DuckDB
	cd dbt && uv run dbt run --target duckdb --profiles-dir .

dbt-run-snowflake:  ## Run dbt models against Snowflake trial
	cd dbt && uv run dbt run --target snowflake --profiles-dir .

dbt-build-snowflake:  ## dbt deps + run + test against Snowflake trial (full build)
	cd dbt && uv run dbt deps --profiles-dir . && uv run dbt build --target snowflake --profiles-dir .

dbt-docs-snowflake:  ## Generate dbt docs from Snowflake catalog and serve on :8080
	cd dbt && uv run dbt docs generate --target snowflake --profiles-dir .
	cd dbt && uv run dbt docs serve --port 8080

dbt-test:  ## Run dbt tests against DuckDB
	cd dbt && uv run dbt test --target duckdb --profiles-dir .

dbt-docs:  ## Generate dbt docs and serve on localhost:8080
	cd dbt && uv run dbt docs generate --target duckdb --profiles-dir .
	cd dbt && uv run dbt docs serve --port 8080

dbt-build:  ## dbt deps + run + test against DuckDB in one step
	cd dbt && uv run dbt deps --profiles-dir . && uv run dbt build --target duckdb --profiles-dir .

dbt-clean:  ## Remove dbt target and dbt_packages directories
	cd dbt && uv run dbt clean

# ── Testing ───────────────────────────────────────────────────────────────────
test:  ## Run unit + bronze tests (fast; excludes integration smoke test)
	uv run pytest tests/ -v

test-all:  ## Run every test including the end-to-end smoke test (slow)
	uv run pytest tests/ -v -m ""

test-ci:  ## CI full test run: unit + integration + short traceback output
	uv run pytest tests/ -v --tb=short --no-header -m ""

# ── Docker (Phase 6) ──────────────────────────────────────────────────────────
docker-build:  ## Build the Python app Docker image
	docker compose -f docker/docker-compose.yml build app

docker-test:  ## Run unit + bronze tests inside the app container
	docker compose -f docker/docker-compose.yml run --rm app \
		uv run pytest tests/ -v --tb=short -m "not integration"

docker-test-all:  ## Run all tests (incl. smoke) inside the app container
	docker compose -f docker/docker-compose.yml run --rm app \
		uv run pytest tests/ -v --tb=short -m ""

docker-pipeline:  ## Run the full pipeline (seed → bronze → dbt) inside the container
	docker compose -f docker/docker-compose.yml run --rm app \
		bash -c "make seed && make bronze-reset && make dbt-build"

# ── Dashboard (Phase 8 + 9) ──────────────────────────────────────────────────
fetch-images:  ## Fetch category images from Pexels → dashboard/public/data/images.json (needs PEXELS_API_KEY)
	uv run python -m ingestion.fetch_product_images

sync-tracker:  ## Seed Project Tracker with all completed phase status events
	uv run python -m ingestion.sync_tracker

export-snapshot:  ## Export DuckDB gold marts to dashboard/public/data/*.json
	uv run python -m ingestion.export_snapshot \
		--db-path    data/fashion_retail.duckdb \
		--output-dir dashboard/public/data

dashboard-install:  ## Install Next.js dashboard dependencies (requires Node.js)
	cd dashboard && npm install

dashboard-dev:  ## Run Next.js dashboard in dev mode (requires npm install first)
	cd dashboard && npm run dev

dashboard-build:  ## Build the Next.js dashboard for production
	cd dashboard && npm run build

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
pipeline:  ## Full local pipeline: seed → bronze → dbt build
	$(MAKE) seed
	$(MAKE) bronze-reset
	$(MAKE) dbt-build
	@echo "Pipeline complete."

ci:  ## Replicate CI locally: lint → all tests → dbt build (mirrors GitHub Actions)
	$(MAKE) lint
	$(MAKE) test-all
	$(MAKE) dbt-build
	@echo "Local CI passed."

# ── Airflow (Phase 5) ─────────────────────────────────────────────────────────
AIRFLOW_COMPOSE = docker compose -f docker/airflow/docker-compose.yml

airflow-init:  ## First-time setup: migrate DB and create admin user (run once)
	$(AIRFLOW_COMPOSE) run --rm airflow-init

airflow-up:  ## Start Airflow webserver + scheduler (UI on http://localhost:8080)
	$(AIRFLOW_COMPOSE) up -d airflow-webserver airflow-scheduler

airflow-down:  ## Stop and remove Airflow containers (data volumes are preserved)
	$(AIRFLOW_COMPOSE) down

airflow-logs:  ## Tail combined Airflow logs
	$(AIRFLOW_COMPOSE) logs -f

airflow-trigger:  ## Manually trigger the pipeline DAG
	$(AIRFLOW_COMPOSE) exec airflow-scheduler \
		airflow dags trigger fashion_retail_pipeline

airflow-backfill:  ## Backfill the pipeline for 2024 (demo — adjust dates as needed)
	$(AIRFLOW_COMPOSE) exec airflow-scheduler \
		airflow dags backfill \
		  --start-date 2024-01-01 --end-date 2024-01-07 \
		  --reset-dagruns fashion_retail_pipeline

# ── Docker (Phase 6 full stack — placeholder until Phase 6) ──────────────────
up:
	$(AIRFLOW_COMPOSE) up -d

down:
	$(AIRFLOW_COMPOSE) down

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
	@echo "  make dbt-deps       Install dbt packages (run once after clone)"
	@echo "  make dbt-run        Run dbt models against DuckDB"
	@echo "  make dbt-test       Run dbt tests against DuckDB"
	@echo "  make dbt-docs       Generate and serve dbt docs on :8080"
	@echo "  make dbt-build      dbt deps + run + test against DuckDB"
	@echo "  make dbt-clean      Remove dbt target and dbt_packages"
	@echo "  make airflow-init   First-time Airflow setup (run once)"
	@echo "  make airflow-up     Start Airflow webserver + scheduler (:8080)"
	@echo "  make airflow-down   Stop Airflow containers"
	@echo "  make airflow-logs   Tail Airflow logs"
	@echo "  make airflow-trigger Manually trigger the pipeline DAG"
	@echo "  make airflow-backfill Backfill the pipeline for 2024-01 (demo)"
	@echo "  make docker-build   Build the Python app Docker image"
	@echo "  make docker-test    Run unit tests inside the app container"
	@echo "  make docker-test-all Run all tests (incl. smoke) in container"
	@echo "  make docker-pipeline Seed + bronze + dbt inside container"
	@echo "  make test           Run unit + bronze tests (fast)"
	@echo "  make test-all       Run all tests incl. integration smoke test"
	@echo "  make lint           Check code style (ruff, black, sqlfluff)"
	@echo "  make lint-fix       Auto-fix code style issues"
	@echo "  make pipeline       Full local pipeline: seed → bronze → dbt build"
	@echo "  make ci             Replicate CI locally (lint + all tests + dbt)"
	@echo "  make export-snapshot Export DuckDB gold marts to dashboard JSON"
	@echo "  make dashboard-install Install Next.js deps (needs Node.js)"
	@echo "  make dashboard-dev  Start Next.js dev server"
	@echo "  make dashboard-build Build Next.js for production"
	@echo "  make up             Start Docker Compose stack"
	@echo "  make down           Stop Docker Compose stack"
	@echo "  make clean          Remove generated artifacts and caches"
