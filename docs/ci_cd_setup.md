# CI/CD Setup Guide

## Overview

The project ships two equivalent CI/CD configurations:

| Platform | File | Trigger | Status |
|---|---|---|---|
| **GitHub Actions** | `.github/workflows/ci.yml` | Push to `main`, pull requests | Active (code on GitHub) |
| **GitHub Actions** | `.github/workflows/scheduled.yml` | Weekly cron + manual dispatch | Active |
| **GitLab CI/CD** | `.gitlab-ci.yml` | Push to `main`, merge requests, schedules | Portfolio artifact |

GitHub Actions is the live CI/CD system. The GitLab file demonstrates the same pipeline for teams on GitLab and is kept in sync with the GitHub version.

---

## GitHub Actions — Pipeline stages

```
push / PR
    │
    ▼
lint ─────────────────────────────────────── (ruff · black · sqlfluff)
    │
    ├──────────────────────────┐
    ▼                          ▼
test-unit                test-integration    (parallel)
(86 pytest tests)        (13 smoke tests:
                          generate → bronze
                          → dbt build →
                          gold assertions)
    │                          │
    └──────────────┬───────────┘
                   ▼
            docker-build          (only on green tests)
            fashion-retail-app
```

The `docker-build` job only runs after **both** test jobs pass. A failing pipeline blocks merges into `main`.

---

## Required GitHub secrets

Navigate to **Settings → Secrets and variables → Actions → New repository secret**.

### Always required
None — DuckDB runs in-process, no external service needed for CI.

### For R2 upload (scheduled pipeline)

| Secret | Description |
|---|---|
| `R2_ACCOUNT_ID` | Cloudflare account ID (Dashboard → R2 → Manage API tokens) |
| `R2_ACCESS_KEY_ID` | R2 API token access key |
| `R2_SECRET_ACCESS_KEY` | R2 API token secret |
| `R2_RAW_BUCKET` | Name of the raw landing bucket (e.g., `fashion-retail-raw`) |
| `R2_SERVED_BUCKET` | Name of the served snapshot bucket (e.g., `fashion-retail-served`) |

### For Snowflake (optional — trial build only)

| Secret | Description |
|---|---|
| `SNOWFLAKE_ACCOUNT` | Account identifier (e.g., `abc12345.us-east-1`) |
| `SNOWFLAKE_USER` | Snowflake username |
| `SNOWFLAKE_PRIVATE_KEY_PATH` | Path to private key inside the runner (or use base64 secret) |

### For the Project Tracker (optional)

| Secret | Description |
|---|---|
| `TRACKER_API_URL` | Base URL of the deployed tracker app |
| `TRACKER_API_KEY` | Bearer token for the tracker's pipeline-status endpoint |

---

## Branch protection — require a green pipeline before merge

1. Go to **Settings → Branches**.
2. Click **Add branch protection rule**.
3. Set **Branch name pattern**: `main`.
4. Enable:
   - ✅ **Require status checks to pass before merging**
   - ✅ **Require branches to be up to date before merging**
5. Under **Status checks that are required**, add:
   - `lint (ruff · black · sqlfluff)`
   - `Unit + bronze tests`
   - `Integration smoke (generate → bronze → dbt build → gold assertions)`
   - `Docker build — app image`
6. Enable:
   - ✅ **Do not allow bypassing the above settings**
7. Click **Save changes**.

After this setup, any pull request that fails lint, tests, or the Docker build cannot be merged.

---

## Scheduled pipeline (GitHub)

The scheduled pipeline runs every **Monday at 02:00 UTC** and mirrors what the Airflow DAG does locally:

```
generate_data → bronze_load → dbt build (212 tests) → export_snapshot → [upload_r2]
```

To trigger it manually:
1. Go to **Actions → Scheduled Pipeline**.
2. Click **Run workflow**.
3. Select the **volume** (test / small / large) and click **Run workflow**.

The generated gold snapshot is uploaded as a **workflow artifact** (`gold-snapshot-<run-id>`) and retained for 30 days. When R2 secrets are configured, it is also uploaded to `fashion-retail-served/snapshot/`.

---

## GitLab CI/CD — setup steps

If the project is mirrored to GitLab:

1. **Add CI/CD variables**: Settings → CI/CD → Variables. Add the same secrets listed above. Mark sensitive values as **Masked** and **Protected**.

2. **Protect `main`**: Settings → Repository → Protected Branches.
   - Branch: `main`
   - Allowed to merge: Maintainers
   - Allowed to push: No one (forces merge requests)
   - ✅ Require pipeline to succeed before merge

3. **Set up a scheduled pipeline**: CI/CD → Schedules → New schedule.
   - Description: `Weekly medallion run`
   - Interval: `0 2 * * 1` (Mondays at 02:00 UTC)
   - Target branch: `main`
   - Variables: override `GENERATION_VOLUME` here if needed

4. **Verify the pipeline** by pushing a commit to a feature branch and opening a merge request.

---

## Running the full CI locally

```bash
make ci        # lint + test-all + dbt-build in sequence
```

This replicates what the pipeline does on every push, without Docker.
