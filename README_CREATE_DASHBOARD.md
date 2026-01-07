# Create a Narrow Dashboard (How-to)

Use this guide when you want a new Narrow dashboard entry in `dashboard_configs.json`.

## What a Narrow dashboard is

A Narrow dashboard is a preconfigured view in `dashboard_configs.json` that:
- chooses one or more CSVs from `public/`
- aggregates by a **groupBy** field (x-axis)
- optionally splits by a **seriesBy** field (stacked bars)
- sums a **valueField**
- applies optional filters or reusable mappings

## How to add a new dashboard

1. Open `dashboard_configs.json`.
2. Add a new object to the `dashboards` array.
3. Fill in the fields below (example provided).

### Required fields

- **id**: unique slug for the dashboard (used in the dropdown)
- **title**: headline shown above the chart
- **subtitle**: secondary title (e.g., currency note)
- **note**: short highlight (e.g., “Top 10 programs per year”)
- **description**: longer explanation shown under the note
- **csvs**: array of CSV paths (start with one file, e.g., `public/cihr_grants.txt`)
- **groupBy**: column used for the x-axis (e.g., year)
- **seriesBy**: column used for the stacked series (e.g., program)
- **valueField**: numeric column to sum (e.g., award_amount)

### Optional fields

- **extractYear**: `true` to extract a 4-digit year from the groupBy value
- **minSeriesTotal**: hide series with totals below this value
- **maxSeries**: limit number of series shown
- **topSeriesPerGroup**: `true` to pick top-N series within each group (uses `maxSeries`)
- **mapping**: path to a mapping JSON file in `mappings/labels/departments/`

## Example dashboard entry

```json
{
  "id": "healthcare-top-10",
  "title": "Top 10 Healthcare Expenditures by Year",
  "subtitle": "Current $ (not inflation-adjusted)",
  "note": "Top 10 healthcare programs per year based on total award amount.",
  "description": "CIHR grants grouped by year and program, filtered to core healthcare themes.",
  "csvs": ["public/cihr_grants.txt"],
  "groupBy": "competition_year",
  "seriesBy": "program",
  "valueField": "award_amount",
  "extractYear": false,
  "minSeriesTotal": 0,
  "maxSeries": 10,
  "topSeriesPerGroup": true,
  "mapping": "mappings/labels/departments/healthcare.json"
}
```

## How mappings work (filters you can reuse)

Mappings are simple JSON files stored in `mappings/labels/departments/`.
They let you reuse a filter across dashboards without repeating the criteria.

Example mapping (`mappings/labels/departments/healthcare.json`):

```json
{
  "id": "healthcare-themes",
  "label": "Healthcare research themes (CIHR)",
  "description": "Filter CIHR grants to core healthcare themes for dashboard reuse.",
  "field": "theme",
  "include": [
    "Biomedical",
    "Clinical",
    "Health Systems and Services",
    "Population and Public Health"
  ]
}
```

### Mapping fields

- **field**: CSV column to filter on
- **include**: list of exact values to include
- **includeContains** (optional): list of substrings to include if the field contains them

## How to describe a new dashboard in a prompt

When you want a new dashboard, provide:
- Title + description
- CSV to use
- groupBy field
- seriesBy field
- valueField
- filters (direct or via mapping)
- whether you want top-N per group or overall top series

Example prompt to generate a new dashboard entry:

> "Create a Narrow dashboard called ‘Municipal Grants by Province’ using public/transfers.txt, group by FSCL_YR, series by PROVTER_EN, sum TOT_CY_XPND_AMT, extractYear true, show top 8 series per year, and add a short description." 

This is enough information to add a new entry to `dashboard_configs.json` and (if needed) add a mapping file.
