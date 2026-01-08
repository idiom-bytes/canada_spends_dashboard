# /create-dashboard

When the user invokes this command, spawn a **general-purpose agent** to autonomously create the dashboard including pre-aggregation and configuration.

## How to Execute

Use the Task tool with `subagent_type: "general-purpose"` and pass the dashboard plan.

### Agent Prompt Template

```
You are a dashboard builder for the Canada Spends Dashboard. Your task is to create a new dashboard from the provided plan.

## Dashboard Plan
{dashboard_plan}

## Your Mission
1. Read `dashboard_configs.json` to understand the current structure
2. Create pre-aggregated data JSON for fast loading (if the dashboard has filters or uses a large dataset)
3. Add the dashboard configuration to `dashboard_configs.json`
4. Verify the JSON is valid

## Step 1: Create Pre-aggregated Data (if needed)

Run Python to create `public/dashboards/{id}.json`:

```python
import pandas as pd
import json
from pathlib import Path

# Load data
df = pd.read_parquet('public/{dataFile}.parquet')

# Apply filters if specified in plan
# df = df[df['field'].str.contains('value', case=False, na=False)]

# Extract year if needed
df['_group'] = df['{groupBy}'].astype(str).str.extract(r'(\d{4})')[0]
df = df[df['_group'].notna()]

# Get top series
series_totals = df.groupby('{seriesBy}')['{valueField}'].sum()
top_series = series_totals.nlargest({maxSeries}).index.tolist()
df_filtered = df[df['{seriesBy}'].isin(top_series)]

# Build aggregated data
groups = sorted(df_filtered['_group'].unique())
data = []
for group in groups:
    group_df = df_filtered[df_filtered['_group'] == group]
    series_values = {s: float(group_df[group_df['{seriesBy}'] == s]['{valueField}'].sum()) for s in top_series}
    data.append({'group': group, 'series': series_values})

output = {
    'title': '{title}',
    'subtitle': '{subtitle}',
    'note': '{note}',
    'description': '{description}',
    'aggregated': {
        'groups': groups,
        'series': top_series,
        'data': data
    }
}

Path('public/dashboards').mkdir(exist_ok=True)
with open('public/dashboards/{id}.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"Created public/dashboards/{id}.json")
```

## Step 2: Add to dashboard_configs.json

Use the Edit tool to add the new dashboard to the `dashboards` array in `dashboard_configs.json`.

## Step 3: Verify

Check that:
- The pre-aggregated JSON file exists and is valid
- The dashboard_configs.json is valid JSON
- Report success to the user with the dashboard ID

## Output Format

Return:
1. **Status**: Success or failure
2. **Dashboard ID**: The id that was created
3. **Files Modified**: List of files created/modified
4. **Next Steps**: Tell user to refresh the app to see the new dashboard in the Dashboards dropdown
```

## Example Invocation

User: `/create-dashboard {"id": "brookfield-contracts", "title": "Brookfield Contracts", ...}`

You should spawn:
```
Task(
  subagent_type="general-purpose",
  prompt="[Agent prompt with the dashboard plan JSON]",
  description="Create brookfield-contracts dashboard"
)
```

The agent will autonomously create the pre-aggregated data, update the config, and report success.

$ARGUMENTS
