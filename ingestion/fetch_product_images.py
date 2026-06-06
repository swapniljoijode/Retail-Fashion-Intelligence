"""
Phase 9 — Product Image Pipeline

Fetches one representative image per fashion category from the Pexels API,
uploads 300×300 thumbnails to Cloudflare R2 (images/ prefix), and writes
dashboard/public/data/images.json so the dashboard can render thumbnails.

Usage (from project root):
    uv run python -m ingestion.fetch_product_images

Environment variables (.env):
    PEXELS_API_KEY          Free key from https://www.pexels.com/api/
    R2_ACCOUNT_ID           Cloudflare account ID
    R2_ACCESS_KEY_ID        R2 S3-compatible access key
    R2_SECRET_ACCESS_KEY    R2 S3-compatible secret
    R2_SERVED_BUCKET        Bucket name (default: fashion-retail-served)

Free tier: 200 requests/hour, 20 000/month — well within our needs (6 categories).
Images are licensed under the Pexels License (free for commercial and non-commercial use;
no attribution required, though credited in the metadata we store).
"""

import io
import json
import os
import re
from pathlib import Path

import boto3
import requests
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()

PEXELS_API_KEY    = os.environ.get("PEXELS_API_KEY", "")
R2_ACCOUNT_ID     = os.environ.get("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID  = os.environ.get("R2_ACCESS_KEY_ID", "")
R2_SECRET         = os.environ.get("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET         = os.environ.get("R2_SERVED_BUCKET", "fashion-retail-served")

OUTPUT_JSON = Path("dashboard/public/data/images.json")
LOCAL_DIR   = Path("data/product_images")

# Map each category to a focused Pexels search query
CATEGORY_QUERIES: dict[str, str] = {
    "Tops":       "women fashion top clothing",
    "Bottoms":    "women jeans trousers fashion",
    "Dresses":    "women dress fashion elegant",
    "Outerwear":  "women jacket coat fashion",
    "Footwear":   "fashion shoes heels sneakers",
    "Accessories":"fashion handbag accessories",
}


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _r2_client():
    if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET]):
        return None
    return boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def search_pexels(query: str, per_page: int = 3) -> list[dict]:
    """Return top Pexels photo results for a query."""
    r = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": PEXELS_API_KEY},
        params={"query": query, "per_page": per_page, "size": "medium", "orientation": "square"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("photos", [])


def download_thumbnail(url: str) -> bytes:
    """Download an image from URL, resize hint via query params."""
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.content


def upload_to_r2(client, data: bytes, key: str) -> str:
    """Upload bytes to R2; return the public-facing key."""
    client.put_object(
        Bucket=R2_BUCKET,
        Key=key,
        Body=data,
        ContentType="image/jpeg",
        CacheControl="public, max-age=31536000",
    )
    return key


def run() -> None:
    if not PEXELS_API_KEY:
        print("ERROR: PEXELS_API_KEY not set in .env")
        print("  Get a free key at https://www.pexels.com/api/ (takes 60 seconds)")
        return

    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    r2 = _r2_client()

    results: dict[str, dict] = {}

    for category, query in CATEGORY_QUERIES.items():
        print(f"  {category:<15} searching: '{query}' ...")
        try:
            photos = search_pexels(query)
            if not photos:
                print(f"    no results — skipping")
                continue

            photo   = photos[0]
            thumb_url = photo["src"]["medium"]   # ~350px wide
            img_bytes = download_thumbnail(thumb_url)

            # Save locally
            local_path = LOCAL_DIR / f"{_slug(category)}.jpg"
            local_path.write_bytes(img_bytes)

            # Upload to R2 (if credentials available)
            r2_key = None
            if r2:
                r2_key = f"images/{_slug(category)}.jpg"
                upload_to_r2(r2, img_bytes, r2_key)
                print(f"    OK  uploaded to R2: {r2_key}")
            else:
                print(f"    OK  saved locally (R2 credentials not set)")

            results[category] = {
                "pexels_id":    photo["id"],
                "url":          thumb_url,
                "alt":          photo.get("alt", f"{category} fashion"),
                "photographer": photo["photographer"],
                "pexels_url":   photo["url"],
                "r2_key":       r2_key,
            }

        except Exception as exc:
            print(f"    ERR {exc}")

    if results:
        OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\nWrote {len(results)} entries → {OUTPUT_JSON}")
    else:
        print("\nNo images fetched — images.json unchanged.")


if __name__ == "__main__":
    run()
