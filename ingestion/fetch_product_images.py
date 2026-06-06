"""
Phase 9 — Product Image Pipeline

Fetches one representative image per fashion category from the Pexels API,
uploads 300x300 thumbnails to Cloudflare R2 (images/ prefix), and writes
dashboard/public/data/images.json so the dashboard renders category thumbnails.

Usage (from project root):
    uv run python -m ingestion.fetch_product_images

Environment variables (.env):
    PEXELS_API_KEY          Free key — https://www.pexels.com/api/ (instant signup)
    R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_SERVED_BUCKET

Free tier: 200 requests/hour, 20 000/month — 6 requests total.
Pexels License: free for commercial and non-commercial use; no attribution
required (photographer credited in the metadata we store as good practice).
"""

import json
import os
import re
from pathlib import Path

import boto3
import requests
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY_ID", "")
R2_SECRET = os.environ.get("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET = os.environ.get("R2_SERVED_BUCKET", "fashion-retail-served")

OUTPUT_JSON = Path("dashboard/public/data/images.json")
LOCAL_DIR = Path("data/product_images")

CATEGORY_QUERIES: dict[str, str] = {
    "Tops": "women fashion top blouse clothing",
    "Bottoms": "women jeans trousers fashion",
    "Dresses": "women dress fashion elegant",
    "Outerwear": "women jacket coat fashion outerwear",
    "Footwear": "fashion shoes heels sneakers",
    "Accessories": "fashion handbag accessories leather",
}


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _r2_client():
    if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY, R2_SECRET]):
        return None
    return boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def search_pexels(query: str) -> list[dict]:
    r = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": PEXELS_API_KEY},
        params={
            "query": query,
            "per_page": 3,
            "size": "medium",
            "orientation": "square",
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("photos", [])


def run() -> None:
    if not PEXELS_API_KEY:
        print("ERROR: PEXELS_API_KEY not set in .env")
        print("  Get a free key at https://www.pexels.com/api/ (takes ~60 seconds)")
        return

    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    r2 = _r2_client()

    # Load existing data so we can merge (don't overwrite categories not re-fetched)
    existing: dict = {}
    if OUTPUT_JSON.exists():
        existing = json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))

    for category, query in CATEGORY_QUERIES.items():
        print(f"  {category:<15} : '{query}'")
        try:
            photos = search_pexels(query)
            if not photos:
                print("    no results — skipping")
                continue

            photo = photos[0]
            thumb_url = photo["src"]["medium"]

            # Download thumbnail
            img_bytes = requests.get(thumb_url, timeout=20).content
            (LOCAL_DIR / f"{_slug(category)}.jpg").write_bytes(img_bytes)

            # Upload to R2
            r2_key = None
            if r2:
                r2_key = f"images/{_slug(category)}.jpg"
                r2.put_object(
                    Bucket=R2_BUCKET,
                    Key=r2_key,
                    Body=img_bytes,
                    ContentType="image/jpeg",
                    CacheControl="public, max-age=31536000",
                )
                print(f"    OK  R2: {r2_key}")
            else:
                print("    OK  local only (R2 creds not set)")

            existing[category] = {
                "pexels_id": photo["id"],
                "url": thumb_url,
                "alt": photo.get("alt", f"{category} fashion"),
                "photographer": photo["photographer"],
                "pexels_url": photo["url"],
                "r2_key": r2_key,
            }

        except Exception as exc:
            print(f"    ERR {exc}")

    OUTPUT_JSON.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    print(f"\nWrote {len(existing)} entries to {OUTPUT_JSON}")
    print("Visit the Category page on the dashboard to see the thumbnails.")


if __name__ == "__main__":
    run()
