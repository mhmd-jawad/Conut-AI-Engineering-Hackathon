# Conut Chief of Operations Agent

AI-driven decision-support system for Conut’s operations, covering:
- Combo Optimization
- Demand Forecasting by Branch
- Expansion Feasibility
- Shift Staffing Estimation
- Coffee and Milkshake Growth Strategy

This repository is structured as an end-to-end analytics + API system with OpenClaw integration.

## Architecture at a Glance

The system has 4 layers:
1. **Data Layer**: ingest and clean report-style CSV exports into canonical processed tables.
2. **Analytics Layer**: compute forecasts, combos, staffing recommendations, expansion scorecards, and beverage growth actions.
3. **Service Layer**: FastAPI endpoints exposing all operational capabilities.
4. **Agent Layer**: OpenClaw skill that routes natural-language operations requests to backend endpoints.

For the full architecture and data contracts, see:
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/OPENCLAW_INTEGRATION.md](docs/OPENCLAW_INTEGRATION.md)
- [docs/IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md)

## Proposed Project Structure

```text
Conut-AI-Engineering-Hackathon/
├── README.md
├── requirements.txt
├── .env.example
├── main.py
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── pipelines/
│   ├── clean_00194.py
│   ├── 01_clean_monthly_sales.py
│   ├── 02_clean_category_channel_sales.py
│   ├── 03_clean_item_sales.py
│   ├── 04_clean_customer_orders.py
│   ├── 05_clean_baskets.py
│   ├── 06_clean_attendance.py
│   ├── 07_build_kpis.py
│   └── run_all.py
├── app/
│   ├── api/
│   ├── services/
│   ├── schemas/
│   └── core/
├── skills/
│   └── conut_ops/
│       └── SKILL.md
└── docs/
    ├── ARCHITECTURE.md
    ├── OPENCLAW_INTEGRATION.md
    └── IMPLEMENTATION_ROADMAP.md
```

## Quick Start (Target)

1. Create env and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Run pipeline:

```bash
python pipelines/run_all.py
```

3. Run API:

```bash
uvicorn main:app --reload
```

4. Open API docs:
- `http://127.0.0.1:8000/docs`

## Current Status

- Raw data is present under `data/raw/`
- Tax-cleaning script exists: `pipelines/clean_00194.py`
- Architecture package and implementation roadmap now included in `docs/`
