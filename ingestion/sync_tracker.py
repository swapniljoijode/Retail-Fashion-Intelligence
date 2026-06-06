"""
Sync Fashion Retail Intelligence project status to the Project Tracker API.

Reads tracker_tasks.yaml (the canonical task registry in the repo root),
calls POST /api/sync to seed the project structure, then posts a success
event for every task.

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

BASE_URL = os.environ.get("TRACKER_API_URL", "").rstrip("/")
TOKEN    = os.environ.get("TRACKER_API_TOKEN", "")
REPO_URL = "https://github.com/swapniljoijode/Retail-Fashion-Intelligence"

# Commit links for each phase — used as artifactLinks on completion events
PHASE_ARTIFACTS: dict[str, str] = {
    "P0": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/e97e48d",
    "P1": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/c9565ec",
    "P2": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/8995161",
    "P3": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/911a75d",
    "P4": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/70686ea",
    "P5": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/0374983",
    "P6": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/183706b",
    "P7": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/0ca132f",
    "P8": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/e91f749",
    "P9": "https://github.com/swapniljoijode/Retail-Fashion-Intelligence/commit/303e9d4",
}


def _headers() -> dict:
    return {"x-tracker-token": TOKEN, "Content-Type": "application/json"}


def _post(path: str, body: dict) -> requests.Response:
    return requests.post(
        f"{BASE_URL}{path}", headers=_headers(), json=body, timeout=20
    )


def step1_sync(data: dict) -> bool:
    """Seed project + phases + tasks via POST /api/sync."""
    print("[1/2] Syncing project structure via POST /api/sync ...")
    r = _post("/api/sync", data)
    if r.ok:
        d = r.json()
        phases = d.get("phases", {})
        tasks = d.get("tasks", {})
        print(
            f"  OK  phases  created={phases.get('created', 0)}"
            f"  updated={phases.get('updated', 0)}"
            f"  unchanged={phases.get('unchanged', 0)}"
        )
        print(
            f"  OK  tasks   created={tasks.get('created', 0)}"
            f"  updated={tasks.get('updated', 0)}"
            f"  unchanged={tasks.get('unchanged', 0)}"
        )
        return True
    print(f"  ERR {r.status_code}: {r.text[:300]}")
    return False


def step2_post_events(phases: list) -> None:
    """Post a success event for every task in every phase."""
    print("\n[2/2] Posting completion events ...")
    today = date.today().isoformat()
    ok = errors = 0

    for phase in phases:
        phase_id = phase["id"]
        artifact = PHASE_ARTIFACTS.get(phase_id, REPO_URL)
        for task in phase.get("tasks", []):
            task_id = task["id"]
            idempotency_key = f"{task_id}-sync-{today}"
            body = {
                "status": "success",
                "note": (
                    f"{phase['name']}: {task['title']}. "
                    f"Completed as part of the full medallion build."
                ),
                "artifactLink": artifact,
                "idempotencyKey": idempotency_key,
            }
            r = _post(f"/api/tasks/{task_id}/events", body)
            if r.ok or r.status_code == 201:
                print(f"  OK  {task_id:<10} {task['title'][:55]}")
                ok += 1
            else:
                print(f"  ERR {task_id:<10} {r.status_code}: {r.text[:80]}")
                errors += 1

    print(f"\n  {ok} events posted  |  {errors} errors")


def main() -> None:
    if not BASE_URL or not TOKEN:
        print("ERROR: set TRACKER_API_URL and TRACKER_API_TOKEN in .env")
        sys.exit(1)

    tasks_path = Path("tracker_tasks.yaml")
    if not tasks_path.exists():
        print(f"ERROR: {tasks_path} not found — run from project root")
        sys.exit(1)

    data = yaml.safe_load(tasks_path.read_text(encoding="utf-8"))

    print(f"\nProject Tracker sync — {BASE_URL}")
    print("=" * 60)

    if step1_sync(data):
        step2_post_events(data.get("phases", []))

    print(f"\nDone. Visit: {BASE_URL}/?projectId={data.get('project', '')}")


if __name__ == "__main__":
    main()
