#!/usr/bin/env python3
"""
Build pre-aggregated dashboard JSON files from parquet/CSV data.

This script reads the raw data files and generates optimized dashboard
JSON files based on configurations in dashboard_configs.json.

Usage:
    python build_dashboards.py              # Build all dashboards
    python build_dashboards.py --dashboard healthcare-top-10  # Build specific dashboard
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path


def extract_year(value: str) -> str | None:
    """
    Extract 4-digit year from a value like '202312' or '2023-2024'.

    Returns None for invalid/unparseable values to allow filtering.
    """
    if not value:
        return None

    value_str = str(value).strip()

    # Try to find a 4-digit year (1900-2099 range for sanity)
    match = re.search(r'(19\d{2}|20\d{2})', value_str)
    if match:
        return match.group(1)

    # Invalid year format
    return None


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


def row_matches_filter(row: dict, filter_config: dict | None) -> bool:
    """Check if a row matches the filter criteria."""
    if not filter_config:
        return True

    field = filter_config.get('field', '')
    value = row.get(field, '') or ''

    # Check exact include
    if 'include' in filter_config:
        if value not in filter_config['include']:
            return False

    # Check contains (substring match)
    if 'contains' in filter_config:
        matched = any(
            item.lower() in str(value).lower()
            for item in filter_config['contains']
        )
        if not matched:
            return False

    return True


def aggregate_data(rows: list[dict], config: dict) -> dict:
    """Aggregate rows according to dashboard config."""
    group_by = config.get('groupBy', '')
    series_by = config.get('seriesBy', '')
    value_field = config.get('valueField', '')
    extract_year_flag = config.get('extractYear', False)
    min_series_total = config.get('minSeriesTotal', 0)
    max_series = config.get('maxSeries', 10)
    top_series_per_group = config.get('topSeriesPerGroup', False)
    filter_config = config.get('filter')

    totals = defaultdict(lambda: defaultdict(float))
    series_totals = defaultdict(float)
    groups_set = set()
    series_set = set()

    skipped_rows = 0

    for row in rows:
        if not row_matches_filter(row, filter_config):
            continue

        group_value = row.get(group_by, '')

        if extract_year_flag:
            group_value = extract_year(group_value)
            # Skip rows with invalid year values
            if group_value is None:
                skipped_rows += 1
                continue

        series_value = row.get(series_by, 'Total') if series_by else 'Total'
        value = to_number(row.get(value_field, 0))

        if not group_value:
            continue

        groups_set.add(group_value)
        series_set.add(series_value)
        totals[group_value][series_value] += value
        series_totals[series_value] += value

    if skipped_rows > 0:
        print(f"  Skipped {skipped_rows:,} rows with invalid year values")

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


def load_data_file(file_path: Path) -> list[dict]:
    """Load data from parquet or CSV file."""
    rows = []

    if file_path.suffix == '.parquet':
        try:
            import pyarrow.parquet as pq
            table = pq.read_table(file_path)
            # Convert to list of dicts
            columns = table.column_names
            for i in range(table.num_rows):
                row = {col: table.column(col)[i].as_py() for col in columns}
                rows.append(row)
            return rows
        except ImportError:
            print(f"  pyarrow not installed, trying CSV fallback")
            # Try CSV fallback
            csv_path = file_path.with_suffix('.csv')
            if csv_path.exists():
                file_path = csv_path
            else:
                return []

    if file_path.suffix == '.csv':
        import csv
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

    return rows


def build_dashboard(config: dict, dashboards_dir: Path, project_dir: Path) -> bool:
    """Build pre-aggregated data for a single dashboard."""
    dashboard_id = config.get('id', 'unknown')
    print(f"\nBuilding dashboard: {dashboard_id}")

    # Support both 'csvs' (legacy) and 'dataFiles' config keys
    data_files = config.get('dataFiles', config.get('csvs', []))
    if not data_files:
        print(f"  No data files configured")
        return False

    # Load data
    all_rows = []
    public_dir = project_dir / "public"

    for data_file in data_files:
        # Try parquet first, then CSV
        base_name = data_file.replace('.csv', '').replace('.parquet', '')
        parquet_path = public_dir / f"{base_name}.parquet"
        csv_path = public_dir / f"{base_name}.csv"

        if parquet_path.exists():
            file_path = parquet_path
        elif csv_path.exists():
            file_path = csv_path
        else:
            # Try as-is (might be full path)
            file_path = project_dir / data_file
            if not file_path.exists():
                print(f"  Data file not found: {data_file}")
                continue

        print(f"  Loading: {file_path.name}")
        rows = load_data_file(file_path)
        all_rows.extend(rows)
        print(f"  Loaded {len(rows):,} rows")

    if not all_rows:
        print(f"  No data loaded")
        return False

    # Aggregate data
    aggregated = aggregate_data(all_rows, config)

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
    print(f"  Saved: {output_file.name} ({size_kb:.1f} KB)")

    return True


def main():
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent  # Go up from src/ to project root
    public_dir = project_dir / "public"
    dashboards_dir = public_dir / "dashboards"
    configs_path = project_dir / "dashboard_configs.json"

    # Parse arguments
    specific_dashboard = None
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == '--dashboard' and i < len(sys.argv):
            specific_dashboard = sys.argv[i + 1]
            break

    print("=" * 60)
    print("Dashboard Builder")
    print("=" * 60)

    if not configs_path.exists():
        print(f"Config file not found: {configs_path}")
        return 1

    configs = json.loads(configs_path.read_text())
    dashboards = configs.get('dashboards', [])

    if specific_dashboard:
        dashboards = [d for d in dashboards if d.get('id') == specific_dashboard]
        if not dashboards:
            print(f"Dashboard not found: {specific_dashboard}")
            return 1

    built = 0
    for config in dashboards:
        if build_dashboard(config, dashboards_dir, project_dir):
            built += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"Complete! Built {built}/{len(dashboards)} dashboards")
    print("=" * 60)

    print("\nGenerated files:")
    for f in sorted(dashboards_dir.glob("*.json")):
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name}: {size_kb:.1f} KB")

    return 0


if __name__ == "__main__":
    sys.exit(main())
