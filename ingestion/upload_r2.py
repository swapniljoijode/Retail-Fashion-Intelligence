"""Upload Parquet output to Cloudflare R2 using the S3-compatible API.

Cloudflare R2 is API-compatible with S3, so boto3 works unchanged — only the
endpoint_url and credential env vars differ from AWS.

Required environment variables (set in .env):
    R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_RAW_BUCKET

CLI:
    python -m ingestion.upload_r2
    python -m ingestion.upload_r2 --input-dir data_generation/output --prefix raw
    python -m ingestion.upload_r2 --dry-run
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

load_dotenv()


def _r2_client():
    """Build a boto3 S3 client pointed at the Cloudflare R2 endpoint."""
    account_id = os.environ["R2_ACCOUNT_ID"]
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def upload_parquet(
    input_dir: Path,
    bucket: str,
    prefix: str = "raw",
    dry_run: bool = False,
) -> list[dict]:
    """Upload all Parquet files under input_dir to R2, preserving the sub-directory
    structure as the S3 key path.

    Returns a manifest — one dict per file with local_path, s3_key, size_bytes.
    Raises FileNotFoundError if no Parquet files are found.
    """
    parquet_files = sorted(input_dir.rglob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No Parquet files found under {input_dir}")

    client = None if dry_run else _r2_client()
    manifest: list[dict] = []

    for local_path in parquet_files:
        relative = local_path.relative_to(input_dir)
        # Always use forward slashes for S3 keys
        s3_key = "/".join([prefix] + list(relative.parts)) if prefix else "/".join(relative.parts)
        size_bytes = local_path.stat().st_size

        if not dry_run:
            client.upload_file(str(local_path), bucket, s3_key)

        manifest.append(
            {"local_path": str(local_path), "s3_key": s3_key, "size_bytes": size_bytes}
        )
        tag = "DRY-RUN " if dry_run else "UPLOADED"
        print(f"[{tag}] {relative}  →  s3://{bucket}/{s3_key}  ({size_bytes:,} bytes)")

    total_bytes = sum(r["size_bytes"] for r in manifest)
    destination = f"s3://{bucket}/{prefix}/" if prefix else f"s3://{bucket}/"
    print(
        f"\n{'Dry-run: would upload' if dry_run else 'Uploaded'} "
        f"{len(manifest)} files ({total_bytes / 1_048_576:.1f} MB) to {destination}"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload Parquet output to Cloudflare R2",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data_generation/output"),
        help="Root directory containing Parquet output",
    )
    parser.add_argument(
        "--bucket",
        default=os.getenv("R2_RAW_BUCKET", "fashion-retail-raw"),
        help="R2 bucket name (overrides R2_RAW_BUCKET env var)",
    )
    parser.add_argument(
        "--prefix",
        default="raw",
        help="S3 key prefix — all files are uploaded under this path",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be uploaded without actually uploading",
    )
    args = parser.parse_args()

    try:
        upload_parquet(args.input_dir, args.bucket, args.prefix, args.dry_run)
    except (BotoCoreError, ClientError) as exc:
        raise SystemExit(f"R2 upload failed: {exc}") from exc


if __name__ == "__main__":
    main()
