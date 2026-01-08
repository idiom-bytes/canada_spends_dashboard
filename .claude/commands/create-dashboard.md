# CREATE_DASHBOARD Skill

Create a new dashboard from a plan or from scratch, including configuration and pre-aggregation.

## Your Role

You are a dashboard builder for the Canada Spends Dashboard. Your job is to:
1. Accept a plan from `/plan-dashboard` OR help create one from scratch
2. Build the dashboard configuration
3. Create pre-aggregated data for fast loading
4. Register the dashboard so it appears in the Dashboards tab

## Input Formats

### Option 1: Plan from `/plan-dashboard`

If the user provides a plan JSON from `/plan-dashboard`, parse it and proceed directly to implementation.

### Option 2: From Scratch

If no plan is provided, ask:
- What data source? (see `data_schemas.json`)
- What grouping? (usually time-based field)
- What series? (categories for stacked bars)
- Any filters needed?

## Implementation Steps

### Step 1: Read Current Configuration

```bash
# Read current dashboard configs
cat dashboard_configs.json
```

### Step 2: Create Pre-Aggregated Data (if needed)

For large datasets or filtered views, create pre-aggregated JSON:

```python
import pandas as pd
import json
from pathlib import Path

# Load data
df = pd.read_parquet('public/contracts-over-10k.parquet')

# Apply filters if needed
# Example: Filter for specific vendor
df = df[df['vendor_name'].str.contains('Brookfield', case=False, na=False)]

# Configure aggregation
config = {
    'groupBy': 'reporting_period',
    'seriesBy': 'owner_org_title',
    'valueField': 'contract_value',
    'extractYear': True,
    'maxSeries': 10,
    'minSeriesTotal': 0
}

# Extract year if needed
if config['extractYear']:
    df['_group'] = df[config['groupBy']].astype(str).str.extract(r'(\d{4})')[0]
else:
    df['_group'] = df[config['groupBy']].astype(str)

# Filter valid groups
df = df[df['_group'].notna()]

# Aggregate
series_field = config['seriesBy']
value_field = config['valueField']

# Calculate series totals for ranking
series_totals = df.groupby(series_field)[value_field].sum()
if config['minSeriesTotal']:
    series_totals = series_totals[series_totals >= config['minSeriesTotal']]
top_series = series_totals.nlargest(config['maxSeries']).index.tolist()

# Filter to top series
df_filtered = df[df[series_field].isin(top_series)]

# Build aggregated structure
groups = sorted(df_filtered['_group'].unique())
data = []
for group in groups:
    group_df = df_filtered[df_filtered['_group'] == group]
    series_values = {}
    for series in top_series:
        val = group_df[group_df[series_field] == series][value_field].sum()
        series_values[series] = float(val)
    data.append({'group': group, 'series': series_values})

# Build output
output = {
    'title': 'Dashboard Title',
    'subtitle': 'Current $ (not inflation-adjusted)',
    'note': 'Note about the data',
    'description': 'Description of what this shows',
    'aggregated': {
        'groups': groups,
        'series': top_series,
        'data': data
    }
}

# Save
Path('public/dashboards').mkdir(exist_ok=True)
with open('public/dashboards/my-dashboard-id.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"Created pre-aggregated data with {len(groups)} groups and {len(top_series)} series")
```

### Step 3: Add to Dashboard Config

Edit `dashboard_configs.json` to add the new dashboard:

```json
{
  "id": "brookfield-contracts",
  "title": "Brookfield Contracts by Year",
  "subtitle": "Current $ (not inflation-adjusted)",
  "note": "All federal contracts with Brookfield companies",
  "description": "Government contracts with Brookfield-related vendors, grouped by year and department.",
  "dataFiles": ["contracts-over-10k"],
  "groupBy": "reporting_period",
  "seriesBy": "owner_org_title",
  "valueField": "contract_value",
  "extractYear": true,
  "minSeriesTotal": 0,
  "maxSeries": 10
}
```

### Step 4: Verify

1. Check the JSON files are valid
2. Open the dashboard in a browser
3. Verify the new dashboard appears in the dropdown

## Dashboard Configuration Reference

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier (lowercase, hyphenated) |
| `title` | Yes | Display title in the UI |
| `subtitle` | No | Subtitle (usually "Current $ (not inflation-adjusted)") |
| `note` | No | Brief contextual note |
| `description` | No | Longer description |
| `dataFiles` | Yes | Array of data source names |
| `groupBy` | Yes | Field for X-axis grouping |
| `seriesBy` | Yes | Field for stacked series |
| `valueField` | Yes | Numeric field to aggregate |
| `extractYear` | No | Extract 4-digit year from groupBy field |
| `minSeriesTotal` | No | Minimum total for a series to appear |
| `maxSeries` | No | Maximum number of series to show |
| `topSeriesPerGroup` | No | If true, show top N series per group instead of overall |
| `filter` | No | Filter object: `{field, contains: [...]}` or `{field, include: [...]}` |

## Filter Examples

### Text Contains Filter
```json
{
  "filter": {
    "field": "vendor_name",
    "contains": ["Brookfield", "Deloitte"]
  }
}
```

### Exact Match Filter
```json
{
  "filter": {
    "field": "theme",
    "include": ["Biomedical", "Clinical"]
  }
}
```

## Complete Example: Creating "Brookfield Contracts" Dashboard

### 1. Pre-aggregate the data

```python
import pandas as pd
import json
from pathlib import Path

df = pd.read_parquet('public/contracts-over-10k.parquet')
df = df[df['vendor_name'].str.contains('Brookfield', case=False, na=False)]

df['year'] = df['reporting_period'].str[:4]
df = df[df['year'].notna()]

series_totals = df.groupby('owner_org_title')['contract_value'].sum()
top_series = series_totals.nlargest(10).index.tolist()
df_filtered = df[df['owner_org_title'].isin(top_series)]

groups = sorted(df_filtered['year'].unique())
data = []
for group in groups:
    group_df = df_filtered[df_filtered['year'] == group]
    series_values = {s: float(group_df[group_df['owner_org_title'] == s]['contract_value'].sum()) for s in top_series}
    data.append({'group': group, 'series': series_values})

output = {
    'title': 'Brookfield Contracts by Year',
    'subtitle': 'Current $ (not inflation-adjusted)',
    'note': 'Federal contracts with Brookfield-related vendors',
    'description': 'All government contracts where vendor name contains "Brookfield", grouped by year and buying department.',
    'aggregated': {
        'groups': groups,
        'series': top_series,
        'data': data
    }
}

Path('public/dashboards').mkdir(exist_ok=True)
with open('public/dashboards/brookfield-contracts.json', 'w') as f:
    json.dump(output, f, indent=2)
```

### 2. Add to dashboard_configs.json

```json
{
  "id": "brookfield-contracts",
  "title": "Brookfield Contracts by Year",
  "subtitle": "Current $ (not inflation-adjusted)",
  "note": "Federal contracts with Brookfield-related vendors",
  "description": "All government contracts where vendor name contains Brookfield.",
  "dataFiles": ["contracts-over-10k"],
  "groupBy": "reporting_period",
  "seriesBy": "owner_org_title",
  "valueField": "contract_value",
  "extractYear": true,
  "maxSeries": 10
}
```

### 3. Done!

The dashboard now appears in the Dashboards dropdown and loads instantly from pre-aggregated data.

## Files Modified

When creating a dashboard, you will modify:
- `dashboard_configs.json` - Add dashboard configuration
- `public/dashboards/{id}.json` - Pre-aggregated data (optional but recommended for filtered/large data)

## Workflow Summary

1. **Receive plan** from `/plan-dashboard` or create from scratch
2. **Create pre-aggregated JSON** if the dashboard has filters or uses a large dataset
3. **Add configuration** to `dashboard_configs.json`
4. **Test** by loading the app and selecting the new dashboard
5. **Report** the dashboard URL/ID to the user

$ARGUMENTS
