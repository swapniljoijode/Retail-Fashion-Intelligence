# Observability with Elementary

[Elementary](https://www.elementary-data.com/) surfaces dbt test results, model freshness, and row-count anomalies as a free HTML report. It runs as a dbt package plus a Python CLI (`edr`).

## How it's wired

### 1. dbt package (`dbt/packages.yml`)

```yaml
- package: elementary-data/elementary
  version: [">=0.15.0", "<1.0.0"]
```

This adds Elementary's models to the dbt project. Run `dbt deps` to install.

### 2. Artifact upload hook (`dbt/dbt_project.yml`)

```yaml
on-run-end:
  - "{{ elementary.upload_dbt_artifacts_v2() }}"
```

After every `dbt run` or `dbt build`, this macro writes the manifest, run results, and source freshness to the `elementary` schema in DuckDB. The `edr` CLI reads from this schema to generate reports.

### 3. Python CLI (`pyproject.toml`)

```toml
[project.optional-dependencies]
dbt = [
    ...
    "elementary-data>=0.15.0",
]
```

Install with `uv sync --extra dbt`.

## Generating a report

After running `dbt build`:

```bash
# Generate the HTML report
edr report \
  --profiles-yml dbt/profiles.yml \
  --profile-target duckdb \
  --project-dir dbt \
  --file-path data/elementary_report.html

# Open the report
open data/elementary_report.html
```

## What the report shows

| Section | Content |
|---|---|
| **Test results** | Pass/fail per test, per model, over the last 14 days |
| **Model runs** | Duration, row counts, and status per dbt model |
| **Anomalies** | Row count and volume anomalies (requires a few pipeline runs to calibrate) |
| **Freshness** | Time since each source was last loaded |
| **Schema changes** | Column additions/removals detected between runs |

## CI integration

The scheduled GitHub Actions workflow (`scheduled.yml`) generates the report after every weekly `dbt build` and uploads it as a 30-day artifact:

```yaml
- name: Generate Elementary observability report
  run: |
    uv run edr report \
      --profiles-yml elementary_profiles.yml \
      --profile-target duckdb \
      --project-dir dbt \
      --file-path data/elementary_report.html || true

- name: Upload Elementary report as artifact
  uses: actions/upload-artifact@v4
  with:
    name: elementary-report-${{ github.run_id }}
    path: data/elementary_report.html
    retention-days: 30
```

The `|| true` ensures the pipeline does not fail if the first few runs haven't accumulated enough data for anomaly detection to calibrate.

## First-run note

Elementary's anomaly detection requires 7–14 runs to establish a baseline. The first few reports will show test results and model run history but no anomaly alerts — this is expected.
