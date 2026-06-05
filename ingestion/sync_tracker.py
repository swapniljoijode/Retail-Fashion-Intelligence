"""
Sync Fashion Retail Intelligence project status to the Project Tracker API.

Does three things in order:
  1. POST /api/sync  — seeds project + all phases + all tasks (idempotent upsert)
  2. POST /api/tasks/:id/events — marks every completed task as success
  3. Prints a summary of what was sent

Usage (from project root):
    uv run python -m ingestion.sync_tracker

Environment variables (.env):
    TRACKER_API_URL    https://project-tracker-lyart-seven.vercel.app
    TRACKER_API_TOKEN  <your token>
"""

import os
import sys
from datetime import date
from pathlib import Path

import requests
import yaml
from dotenv import load_dotenv

load_dotenv()

BASE_URL   = os.environ.get("TRACKER_API_URL", "").rstrip("/")
TOKEN      = os.environ.get("TRACKER_API_TOKEN", "")
REPO_URL   = "https://github.com/swapniljoijode/Retail-Fashion-Intelligence"
PROJECT_ID = "fashion-retail-intelligence"

# tracker_migration.yml status → tracker API status
STATUS_MAP = {
    "completed":   "success",
    "in_progress": "ongoing",
    "failed":      "failure",
    "skipped":     "success",
    "pending":     "ongoing",
}

# Commit links for each phase — used as artifactLinks on completion events
PHASE_COMMITS = {
    "p0": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/e97e48d",
    "p1": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/c9565ec",
    "p2": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/8995161",
    "p3": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/911a75d",
    "p4": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/70686ea",
    "p5": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/0374983",
    "p6": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/183706b",
    "p7": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/0ca132f",
    "p8": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/e91f749",
    "p9": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/c561c07",
}


def _headers() -> dict:
    return {
        "x-tracker-token": TOKEN,
        "Content-Type":    "application/json",
    }


def _post(path: str, body: dict) -> requests.Response:
    return requests.post(
        f"{BASE_URL}{path}",
        headers=_headers(),
        json=body,
        timeout=20,
    )


def _load_migration() -> dict:
    path = Path("docs/tracker_migration.yml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def step1_sync(migration: dict) -> bool:
    """Seed project + all phases + all tasks via POST /api/sync."""
    print("[1/2] Syncing project structure via POST /api/sync ...")

    template = {
        "version": int(migration["project"]["version"].replace(".", "")),
        "project": PROJECT_ID,
        "phases": [
            {
                "id":    phase["id"],
                "name":  phase["name"],
                "tasks": [
                    {"id": task["id"], "title": task["name"]}
                    for task in phase.get("tasks", [])
                ],
            }
            for phase in migration["phases"]
        ],
    }

    r = _post("/api/sync", template)
    if r.ok:
        data = r.json()
        phases = data.get("phases", {})
        tasks  = data.get("tasks",  {})
        print(
            f"  OK  phases  created={phases.get('created',0)}"
            f"  updated={phases.get('updated',0)}"
            f"  unchanged={phases.get('unchanged',0)}"
        )
        print(
            f"  OK  tasks   created={tasks.get('created',0)}"
            f"  updated={tasks.get('updated',0)}"
            f"  unchanged={tasks.get('unchanged',0)}"
        )
        return True
    print(f"  ERR {r.status_code}: {r.text[:300]}")
    return False


def step2_post_events(migration: dict) -> None:
    """Post a success event for every completed task."""
    print("\n[2/2] Posting completion events ...")
    today    = date.today().isoformat()
    ok = errors = skipped = 0

    for phase in migration["phases"]:
        artifact = PHASE_COMMITS.get(phase["id"], REPO_URL)
        for task in phase.get("tasks", []):
            raw_status = task.get("status", "pending")
            api_status = STATUS_MAP[raw_status]

            if api_status == "ongoing":
                skipped += 1
                continue

            idempotency_key = f"{task['id']}-sync-{today}"
            body = {
                "status":         api_status,
                "note":           (
                    f"{phase['name']}: {task['name']}. "
                    f"Completed as part of the full medallion build "
                    f"(Phase {phase['id'].upper()})."
                ),
                "artifactLink":   artifact,
                "idempotencyKey": idempotency_key,
            }

            r = _post(f"/api/tasks/{task['id']}/events", body)
            if r.ok or r.status_code == 201:
                print(f"  OK  {task['id']:12s} → {api_status:<8}  {task['name'][:52]}")
                ok += 1
            else:
                print(f"  ERR {task['id']:12s}  {r.status_code}: {r.text[:100]}")
                errors += 1

    print(f"\n  {ok} events posted  |  {skipped} pending (skipped)  |  {errors} errors")


def main() -> None:
    if not BASE_URL or not TOKEN:
        print("ERROR: set TRACKER_API_URL and TRACKER_API_TOKEN in .env")
        sys.exit(1)

    migration = _load_migration()
    print(f"\nProject Tracker sync — {BASE_URL}")
    print("=" * 60)

    if step1_sync(migration):
        step2_post_events(migration)

    print("\nDone. Visit the tracker to verify:")
    print(f"  {BASE_URL}/?projectId={PROJECT_ID}")


if __name__ == "__main__":
    main()
