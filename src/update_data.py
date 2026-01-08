#!/usr/bin/env python3
"""
Download latest CSV data from Canada Spends API and convert to Parquet.

This script handles raw data ingestion only. For generating dashboard
JSON files, use build_dashboards.py after running this script.

Usage:
    python update_data.py                    # Download and convert to parquet
    python update_data.py --skip-download    # Only convert existing CSVs to parquet
"""

import sys
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

BASE_URL = "https://api.canadasbuilding.com/canada-spends"

TABLES = [
    "aggregated-contracts-under-10k",
    "contracts-over-10k",
    "cihr_grants",
    "global_affairs_grants",
    "nserc_grants",
    "sshrc_grants",
    "transfers",
]


def download_table(table: str, output_dir: Path) -> bool:
    """Download a single table as CSV with streaming export."""
    url = f"{BASE_URL}/{table}.csv?_stream=on&_size=max"
    output_file = output_dir / f"{table}.csv"

    print(f"\nDownloading: {table}")
    print(f"  URL: {url}")

    try:
        with urlopen(url) as response:
            content = response.read()
            output_file.write_bytes(content)

        rows = content.count(b"\n")
        size_mb = len(content) / 1024 / 1024
        print(f"  Success: {rows:,} rows, {size_mb:.1f} MB")
        return True

    except (HTTPError, URLError) as e:
        print(f"  ERROR: {e}")
        return False


def convert_to_parquet(csv_path: Path, parquet_path: Path) -> bool:
    """Convert CSV to Parquet format for faster loading."""
    try:
        import pandas as pd

        print(f"  Converting to Parquet: {parquet_path.name}")

        # Use pandas for robust CSV parsing of large/complex files
        df = pd.read_csv(csv_path, low_memory=False, on_bad_lines='skip')
        df.to_parquet(parquet_path, compression='snappy', index=False)

        size_mb = parquet_path.stat().st_size / 1024 / 1024
        print(f"  Parquet size: {size_mb:.1f} MB")
        return True

    except ImportError:
        print(f"  pandas not installed, skipping")
        return False
    except Exception as e:
        print(f"  Parquet conversion failed: {e}")
        return False


def main():
    skip_download = '--skip-download' in sys.argv

    script_dir = Path(__file__).parent
    project_dir = script_dir.parent  # Go up from src/ to project root
    public_dir = project_dir / "public"
    public_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("Canada Spends Data Updater")
    print("=" * 60)

    # Step 1: Download CSVs
    if not skip_download:
        print("\n[1/2] Downloading CSV data...")
        downloaded = 0
        for table in TABLES:
            if download_table(table, public_dir):
                downloaded += 1
        print(f"\nDownloaded {downloaded}/{len(TABLES)} tables")
    else:
        print("\n[1/2] Skipping download (--skip-download)")

    # Step 2: Convert to Parquet (if pandas available)
    print("\n[2/2] Converting to Parquet...")
    try:
        import pandas
        has_pandas = True
        print("  pandas available, converting files...")
    except ImportError:
        has_pandas = False
        print("  pandas not installed, skipping Parquet conversion")
        print("  Install with: pip install pandas pyarrow")

    converted = 0
    if has_pandas:
        for table in TABLES:
            csv_path = public_dir / f"{table}.csv"
            parquet_path = public_dir / f"{table}.parquet"
            if csv_path.exists():
                if convert_to_parquet(csv_path, parquet_path):
                    converted += 1

        print(f"\nConverted {converted}/{len(TABLES)} files to Parquet")

    # Summary
    print("\n" + "=" * 60)
    print("Complete!")
    print("=" * 60)

    print("\nData files in public/:")
    for ext in ['parquet', 'csv']:
        files = sorted(public_dir.glob(f"*.{ext}"))
        if files:
            print(f"\n  .{ext} files:")
            for f in files:
                size_mb = f.stat().st_size / 1024 / 1024
                print(f"    {f.name}: {size_mb:.1f} MB")

    print("\nNext step: Run 'python build_dashboards.py' to generate dashboard JSON files")

    return 0


if __name__ == "__main__":
    sys.exit(main())
