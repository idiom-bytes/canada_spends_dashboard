# /plan-dashboard

When the user invokes this command, spawn an **Explore agent** to autonomously investigate the data and formulate a dashboard plan.

## How to Execute

Use the Task tool with `subagent_type: "Explore"` and pass the user's query along with context about the data sources.

### Agent Prompt Template

```
You are a data exploration expert for the Canada Spends Dashboard. Your task is to explore government spending data and create a dashboard plan.

## User's Request
{user_request}

## Your Mission
1. Read `data_schemas.json` to understand available data sources and their columns
2. Read `dashboard_configs.json` to see existing dashboards and dataSourceDefaults
3. Query the relevant parquet file(s) in `public/` using Python to explore the data
4. Find patterns, totals, and insights relevant to the user's request
5. Formulate a concrete dashboard configuration plan

## Data Exploration (use Python)
```python
import pandas as pd
df = pd.read_parquet('public/{data_source}.parquet')
# Search, filter, aggregate as needed
```

## Available Data Sources
- contracts-over-10k: Federal contracts >$10K with vendor_name, contract_value, owner_org_title
- aggregated-contracts-under-10k: Small contracts aggregated by dept/year
- transfers: Transfer payments (FSCL_YR, MINE, TOT_CY_XPND_AMT, PROVTER_EN)
- cihr_grants: Health research (competition_year, program_type, award_amount)
- nserc_grants: Science/engineering grants (fiscal_year, program, award_amount)
- sshrc_grants: Social sciences grants (fiscal_year, program, amount)
- global_affairs_grants: International development (start, status, maximumContribution)

## Output Format
Return a summary with:
1. **Findings**: What you discovered (counts, totals, patterns)
2. **Dashboard Plan**: JSON configuration ready for /create-dashboard:
```json
{
  "id": "unique-dashboard-id",
  "title": "Dashboard Title",
  "subtitle": "Current $ (not inflation-adjusted)",
  "note": "Brief context",
  "description": "What this dashboard shows",
  "dataFiles": ["data-source-name"],
  "groupBy": "field_for_x_axis",
  "seriesBy": "field_for_stacked_series",
  "valueField": "numeric_field_to_sum",
  "extractYear": true,
  "maxSeries": 10,
  "filter": {"field": "...", "contains": ["..."]}  // optional
}
```
3. **Next Steps**: Tell user to run `/create-dashboard` with the plan
```

## Example Invocation

User: `/plan-dashboard Find all contracts with Brookfield`

You should spawn:
```
Task(
  subagent_type="Explore",
  prompt="[Agent prompt with user request: 'Find all contracts with Brookfield']",
  description="Explore Brookfield contracts"
)
```

The agent will autonomously explore and return findings + a dashboard plan.

$ARGUMENTS
