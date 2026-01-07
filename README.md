# Canada Spends Dashboard (Codex-friendly)

This repo is built to run as a single-page dashboard on GitHub Pages and to be easy to iterate on inside Codex.

## Quick start (Codex / local)

```bash
python -m http.server 8000
```

Open http://localhost:8000/index.html.

## One-line screenshot capture (stable Playwright flags)

The script below starts a local server, renders the page, and captures a screenshot using flags that prevent
Playwright crashes inside containers:

```bash
bash scripts/serve_and_capture.sh
```

Screenshot output: `artifacts/dashboard.png`.

You can override defaults:

```bash
PORT=8000 OUTPUT=artifacts/dashboard.png bash scripts/serve_and_capture.sh
```

## Configure Narrow dashboards

Edit `dashboard_configs.json` to add or change preconfigured Narrow dashboards. Reusable filters can be stored in
`mappings/labels/departments/` and referenced from each dashboard configuration.
