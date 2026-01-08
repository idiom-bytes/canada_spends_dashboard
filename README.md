# Canada Spends Dashboard

A single-page dashboard for exploring Canadian government spending data. Built to run on GitHub Pages and be easy to iterate on with Claude Code.

## Features

- **Dashboards Tab**: Pre-configured visualizations with instant loading
- **Explore Tab**: Interactive data exploration with customizable groupings and filters
- **7 Data Sources**: Contracts, transfers, and research grants from federal government
- **Claude Skills**: AI-assisted dashboard creation with `/plan-dashboard` and `/create-dashboard`

## Running Locally

### Option 1: Simple HTTP Server (Python)

```bash
# No dependencies needed for basic viewing
python -m http.server 8000
```

Open http://localhost:8000

### Option 2: With Python Dependencies (for data processing)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
python -m http.server 8000
```

### Option 3: Using uv (faster)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create environment and install
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Run server
python -m http.server 8000
```

### Updating Data

To refresh data from Canada Spends:

```bash
source .venv/bin/activate
python src/update_data.py
```

### Building Pre-aggregated Dashboards

To regenerate pre-aggregated JSON for faster dashboard loading:

```bash
source .venv/bin/activate
python src/build_dashboards.py
```

## Deploying to GitHub Pages

### Initial Setup

1. **Push your code to GitHub**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/canada_spends_dashboard.git
   git push -u origin main
   ```

2. **Enable GitHub Pages**:
   - Go to your repository on GitHub
   - Navigate to **Settings** > **Pages**
   - Under "Source", select **Deploy from a branch**
   - Select **main** branch and **/ (root)** folder
   - Click **Save**

3. **Wait for deployment** (usually 1-2 minutes)
   - Your site will be available at: `https://YOUR_USERNAME.github.io/canada_spends_dashboard/`

### Updating the Deployed Site

Simply push changes to the main branch:

```bash
git add .
git commit -m "Update dashboard"
git push
```

GitHub Pages will automatically rebuild and deploy.

### Custom Domain (Optional)

1. Go to **Settings** > **Pages**
2. Under "Custom domain", enter your domain
3. Add a `CNAME` file to your repo root with your domain name
4. Configure DNS with your domain provider

## Using Claude Skills

This project includes Claude Code skills for AI-assisted dashboard creation. These skills help you explore data and create new dashboards without manually writing configuration.

### Available Skills

| Skill | Purpose |
|-------|---------|
| `/plan-dashboard` | Explore data, find specific companies/topics, formulate a dashboard plan |
| `/create-dashboard` | Build dashboards from a plan, including pre-aggregation and configuration |

### Workflow

#### Step 1: Plan Your Dashboard

```
/plan-dashboard Find all contracts with Brookfield and show spending by department over time
```

The skill will:
- Query the data to find relevant records
- Analyze patterns (total spending, top departments, etc.)
- Output a JSON plan for the dashboard

#### Step 2: Create the Dashboard

```
/create-dashboard [paste the plan from step 1]
```

The skill will:
- Create pre-aggregated JSON in `public/dashboards/`
- Add configuration to `dashboard_configs.json`
- The dashboard appears immediately in the Dashboards dropdown

### Example Session

```
User: /plan-dashboard I want to see CIHR cancer research funding trends

Claude: [Explores cihr_grants data, searches for cancer-related keywords]
        Found 2,847 grants with cancer-related research totaling $1.2B from 2007-2024.

        Here's the plan:
        {
          "id": "cihr-cancer-research",
          "title": "CIHR Cancer Research Funding",
          "dataSource": "cihr_grants",
          "groupBy": "competition_year",
          "seriesBy": "program_type",
          "valueField": "award_amount",
          "filter": {"field": "keywords", "contains": ["cancer", "oncology", "tumor"]}
        }

User: /create-dashboard [pastes plan]

Claude: [Creates pre-aggregated data and config]
        Dashboard "cihr-cancer-research" created!
        It now appears in the Dashboards dropdown.
```

### Data Exploration Examples

The `/plan-dashboard` skill can help you:

- **Find specific vendors**: "Find all contracts with Deloitte"
- **Analyze by region**: "Show transfer payments by province"
- **Compare institutions**: "Compare NSERC funding across top 10 universities"
- **Track trends**: "Show how defense contracts changed over time"
- **Search keywords**: "Find all health research related to diabetes"

### Files Used by Skills

| File | Purpose |
|------|---------|
| `data_schemas.json` | Complete schema documentation for all data sources |
| `dashboard_configs.json` | Dashboard configurations (skills add entries here) |
| `public/dashboards/*.json` | Pre-aggregated dashboard data |
| `.claude/commands/*.md` | Skill definitions |

## Project Structure

```
canada_spends_dashboard/
├── index.html              # Main application (single-page app)
├── dashboard_configs.json  # Dashboard configurations
├── data_schemas.json       # Data source documentation
├── requirements.txt        # Python dependencies
├── public/
│   ├── global.css          # Styles
│   ├── *.parquet           # Data files (Parquet format)
│   └── dashboards/         # Pre-aggregated dashboard JSON
├── src/
│   ├── update_data.py      # Download fresh data from Canada Spends
│   └── build_dashboards.py # Generate pre-aggregated dashboard JSON
├── .claude/
│   └── commands/           # Claude Code skills
│       ├── plan-dashboard.md
│       └── create-dashboard.md
└── mappings/               # Reusable filter configurations
```

## Data Sources

| Source | Description | Records |
|--------|-------------|---------|
| `contracts-over-10k` | Federal contracts >$10K with vendor details | ~230K |
| `aggregated-contracts-under-10k` | Small contracts aggregated by dept/year | ~500 |
| `transfers` | Transfer payments to provinces/orgs | ~335K |
| `cihr_grants` | Health research grants (CIHR) | ~133K |
| `nserc_grants` | Science/engineering grants (NSERC) | ~218K |
| `sshrc_grants` | Social sciences grants (SSHRC) | ~213K |
| `global_affairs_grants` | International development projects | ~2.4K |

## Adding Dashboards Manually

If you prefer to add dashboards without Claude skills:

1. Edit `dashboard_configs.json`
2. Add a new entry to the `dashboards` array:

```json
{
  "id": "my-dashboard",
  "title": "My Dashboard Title",
  "subtitle": "Current $ (not inflation-adjusted)",
  "note": "Brief description",
  "description": "Longer explanation",
  "dataFiles": ["contracts-over-10k"],
  "groupBy": "reporting_period",
  "seriesBy": "owner_org_title",
  "valueField": "contract_value",
  "extractYear": true,
  "maxSeries": 10
}
```

3. Optionally create pre-aggregated data in `public/dashboards/my-dashboard.json`

See `README_CREATE_DASHBOARD.md` for detailed configuration options.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally with `python -m http.server 8000`
5. Submit a pull request

## License

MIT License - See LICENSE file for details.

## Credits

- Data source: [Canada Spends](https://canadaspends.com/)
- Built by [@idiom_bytes](https://x.com/idiom_bytes)
