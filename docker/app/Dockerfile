# Fashion Retail Intelligence — Python application image
# Used for: data generation, bronze ingestion, dbt transformations, and tests.
#
# Build from project root:
#   docker build -f docker/app/Dockerfile -t fashion-retail-app .
#
# Or via Docker Compose:
#   docker compose -f docker/docker-compose.yml build app

FROM python:3.11-slim

# ── System dependencies ───────────────────────────────────────────────────────
# git   — dbt deps needs git to clone packages from the dbt Hub
# curl  — used by the uv installer
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── uv — fast, reproducible Python packaging ──────────────────────────────────
COPY --from=ghcr.io/astral-sh/uv:0.4.29 /uv /usr/local/bin/uv

WORKDIR /workspace

# ── Python dependencies ───────────────────────────────────────────────────────
# Copy lockfile first for Docker layer caching: dep installs only re-run when
# pyproject.toml or uv.lock changes, not when source code changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra dbt

# ── Source code ───────────────────────────────────────────────────────────────
COPY data_generation/ data_generation/
COPY ingestion/ ingestion/
COPY dbt/ dbt/
COPY tests/ tests/

# ── Runtime directories ───────────────────────────────────────────────────────
RUN mkdir -p data/generated data/served

# ── dbt package cache ─────────────────────────────────────────────────────────
# Pre-install dbt packages at image build time so test runs don't need network.
# dbt deps needs profiles.yml to parse; we supply a minimal in-memory one.
RUN echo "fashion_retail:\n  target: duckdb\n  outputs:\n    duckdb:\n      type: duckdb\n      path: ':memory:'\n      threads: 4" \
        > /tmp/smoke_profiles.yml \
    && cd dbt && uv run dbt deps --profiles-dir /tmp

# ── Environment ───────────────────────────────────────────────────────────────
ENV PYTHONPATH=/workspace
ENV DUCKDB_PATH=/workspace/data/fashion_retail.duckdb

# Default: run the test suite
CMD ["uv", "run", "pytest", "tests/", "-v", "--tb=short"]
