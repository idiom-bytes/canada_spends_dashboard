#!/usr/bin/env python3
"""
Download latest CSV data from Canada Spends API and build optimized dashboard data.

Usage:
    python update_data.py           # Download CSVs and build dashboard data
    python update_data.py --skip-download  # Only rebuild dashboard data from existing CSVs
"""

import csv
import json
import os
import sys
from collections import defaultdict
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


def extract_year(value: str) -> str:
    """Extract 4-digit year from a value like '202312' or '2023-2024'."""
    if not value:
        return "Unknown"
    # Try to find a 4-digit year
    import re
    match = re.search(r'(\d{4})', str(value))
    return match.group(1) if match else str(value).strip()


def to_number(value) -> float:
    """Convert a value to a number, handling currency formatting."""
    if isinstance(value, (int, float)):
        return float(value)
    if not value:
        return 0.0
    cleaned = str(value).replace('$', '').replace(',', '').replace(' ', '')
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def load_mapping(mapping_path: Path) -> dict | None:
    """Load a mapping JSON file."""
    if not mapping_path or not mapping_path.exists():
        return None
    try:
        return json.loads(mapping_path.read_text())
    except Exception as e:
        print(f"  Warning: Could not load mapping {mapping_path}: {e}")
        return None


def row_matches_mapping(row: dict, mapping: dict | None) -> bool:
    """Check if a row matches the mapping filter."""
    if not mapping:
        return True

    field = mapping.get('field', '')
    value = row.get(field, '') or ''

    # Check exact include
    if 'include' in mapping:
        if value not in mapping['include']:
            return False

    # Check includeContains
    if 'includeContains' in mapping:
        matched = any(
            item.lower() in value.lower()
            for item in mapping['includeContains']
        )
        if not matched:
            return False

    return True


def aggregate_data(rows: list[dict], config: dict, mapping: dict | None) -> dict:
    """Aggregate rows according to dashboard config."""
    group_by = config.get('groupBy', '')
    series_by = config.get('seriesBy', '')
    value_field = config.get('valueField', '')
    extract_year_flag = config.get('extractYear', False)
    min_series_total = config.get('minSeriesTotal', 0)
    max_series = config.get('maxSeries', 10)
    top_series_per_group = config.get('topSeriesPerGroup', False)

    totals = defaultdict(lambda: defaultdict(float))
    series_totals = defaultdict(float)
    groups_set = set()
    series_set = set()

    for row in rows:
        if not row_matches_mapping(row, mapping):
            continue

        group_value = row.get(group_by, '')
        if extract_year_flag:
            group_value = extract_year(group_value)

        series_value = row.get(series_by, 'Total') if series_by else 'Total'
        value = to_number(row.get(value_field, 0))

        if not group_value:
            continue

        groups_set.add(group_value)
        series_set.add(series_value)
        totals[group_value][series_value] += value
        series_totals[series_value] += value

    # Determine which series to include
    if top_series_per_group and max_series:
        # Get top N series per group
        top_series = set()
        for group_map in totals.values():
            ranked = sorted(group_map.items(), key=lambda x: -x[1])[:max_series]
            for series_key, _ in ranked:
                top_series.add(series_key)
        series_list = sorted(top_series, key=lambda s: -series_totals[s])
    else:
        # Filter by min total and take top N overall
        series_list = [s for s in series_set if series_totals[s] >= min_series_total]
        series_list = sorted(series_list, key=lambda s: -series_totals[s])[:max_series]

    # Sort groups (numeric if possible)
    try:
        groups = sorted(groups_set, key=lambda x: int(x))
    except ValueError:
        groups = sorted(groups_set)

    # Build output data
    data = []
    for group in groups:
        series_data = {s: totals[group].get(s, 0) for s in series_list}
        data.append({'group': group, 'series': series_data})

    return {
        'groups': groups,
        'series': series_list,
        'data': data
    }


def build_dashboard_data(config: dict, dashboards_dir: Path, script_dir: Path) -> bool:
    """Build pre-aggregated data for a single dashboard."""
    dashboard_id = config.get('id', 'unknown')
    print(f"\nBuilding dashboard: {dashboard_id}")

    csv_files = config.get('csvs', [])
    if not csv_files:
        print(f"  No CSV files configured")
        return False

    # Load CSV data
    all_rows = []
    for csv_file in csv_files:
        csv_path = script_dir / csv_file
        if not csv_path.exists():
            print(f"  CSV not found: {csv_path}")
            continue

        print(f"  Loading: {csv_file}")
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            all_rows.extend(rows)
        print(f"  Loaded {len(rows):,} rows")

    if not all_rows:
        print(f"  No data loaded")
        return False

    # Load mapping if specified
    mapping = None
    if config.get('mapping'):
        mapping_path = script_dir / config['mapping']
        mapping = load_mapping(mapping_path)

    # Aggregate data
    aggregated = aggregate_data(all_rows, config, mapping)

    print(f"  Aggregated: {len(aggregated['groups'])} groups, {len(aggregated['series'])} series")

    # Save pre-aggregated JSON to dashboards folder
    dashboards_dir.mkdir(exist_ok=True)
    output_file = dashboards_dir / f"{dashboard_id}.json"
    output_data = {
        'id': dashboard_id,
        'title': config.get('title', ''),
        'subtitle': config.get('subtitle', ''),
        'note': config.get('note', ''),
        'description': config.get('description', ''),
        'aggregated': aggregated
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f)

    size_kb = output_file.stat().st_size / 1024
    print(f"  Saved: dashboards/{output_file.name} ({size_kb:.1f} KB)")

    return True


def main():
    skip_download = '--skip-download' in sys.argv

    script_dir = Path(__file__).parent
    public_dir = script_dir / "public"
    public_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("Canada Spends Data Updater")
    print("=" * 60)

    # Step 1: Download CSVs
    if not skip_download:
        print("\n[1/3] Downloading CSV data...")
        for table in TABLES:
            download_table(table, public_dir)
    else:
        print("\n[1/3] Skipping download (--skip-download)")

    # Step 2: Convert to Parquet (if pandas available)
    print("\n[2/3] Converting to Parquet...")
    try:
        import pandas
        has_pandas = True
        print("  pandas available, converting files...")
    except ImportError:
        has_pandas = False
        print("  pandas not installed, skipping Parquet conversion")
        print("  Install with: pip install pandas pyarrow")

    if has_pandas:
        for table in TABLES:
            csv_path = public_dir / f"{table}.csv"
            parquet_path = public_dir / f"{table}.parquet"
            if csv_path.exists():
                convert_to_parquet(csv_path, parquet_path)

    # Step 3: Build dashboard data
    print("\n[3/3] Building dashboard data...")
    configs_path = script_dir / "dashboard_configs.json"
    dashboards_dir = public_dir / "dashboards"

    if not configs_path.exists():
        print(f"  Config file not found: {configs_path}")
        return 1

    configs = json.loads(configs_path.read_text())
    dashboards = configs.get('dashboards', [])

    for config in dashboards:
        build_dashboard_data(config, dashboards_dir, script_dir)

    # Summary
    print("\n" + "=" * 60)
    print("Complete!")
    print("=" * 60)

    print("\nGenerated dashboard files:")
    for f in sorted(dashboards_dir.glob("*.json")):
        size_kb = f.stat().st_size / 1024
        print(f"  dashboards/{f.name}: {size_kb:.1f} KB")

    return 0


if __name__ == "__main__":
    sys.exit(main())
