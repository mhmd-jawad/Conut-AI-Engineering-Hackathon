# Conut Chief of Operations Agent

An AI-driven decision-support system for **Conut**, designed to turn messy operational exports into practical business recommendations for:

- **Combo Optimization**
- **Demand Forecasting by Branch**
- **Expansion Feasibility**
- **Shift Staffing Estimation**
- **Coffee and Milkshake Growth Strategy**

The system includes an end-to-end pipeline for **data ingestion, cleaning, feature engineering, analytics/modeling, inference/reporting**, and exposes these capabilities through a **FastAPI backend** integrated with **OpenClaw** for operational querying.

---

## 1. Business Problem

Conut is a growing sweets and beverages business with multiple branches and operational complexity across:

- branch-level demand
- staffing decisions
- product mix performance
- combo and upsell opportunities
- branch expansion decisions
- beverage growth strategy

The available data is exported from operational/POS reports, but it is **messy, report-style CSV data**, not clean analytical tables.  
The core challenge is not just prediction, but building a **reliable operational AI system** that can transform these raw files into business decisions Conut can actually use.

This project treats the task like a **real consulting and AI systems engagement** rather than a notebook-only assignment.

---

## 2. Objectives

This system addresses all required hackathon objectives:

### 1) Combo Optimization
Identify high-value product combinations based on customer purchasing patterns.

### 2) Demand Forecasting by Branch
Forecast branch-level demand to support inventory and supply-chain planning.

### 3) Expansion Feasibility
Evaluate whether expansion is feasible and recommend the **best branch profile / expansion archetype**, with optional support for candidate location scoring if documented external data is added.

### 4) Shift Staffing Estimation
Estimate the number of employees needed per shift using attendance history and demand indicators.

### 5) Coffee and Milkshake Growth Strategy
Develop branch-specific data-driven growth recommendations to improve coffee and milkshake sales.

### 6) OpenClaw Integration
Allow OpenClaw to interact with the system and execute operational queries such as:
- demand prediction
- staffing recommendation
- combo suggestions
- growth strategy prompts
- expansion feasibility summaries

---

## 3. Dataset Overview

The dataset is provided as a package of report-style CSV exports.

### Raw Files Used

- `REP_S_00136_SMRY.csv` — summary by division/menu channel
- `REP_S_00194_SMRY.csv` — tax summary by branch
- `REP_S_00461.csv` — time and attendance logs
- `REP_S_00502.csv` — sales by customer in detail (delivery, line-item style)
- `rep_s_00150.csv` — customer orders with first/last order timestamps, totals, order counts
- `rep_s_00191_SMRY.csv` — sales by items and groups
- `rep_s_00334_1_SMRY.csv` — monthly sales by branch
- `rep_s_00435_SMRY.csv` — average sales by menu/channel
- `rep_s_00435_SMRY (1).csv` — duplicate version of the same report

---

## 4. Important Data Notes

This dataset has several constraints that shape the system design:

- numeric values are intentionally **scaled/transformed**
- conclusions should focus on **patterns, trends, ratios, and relative comparisons**
- the exports are **report-style CSVs**, not analytics-ready tables
- files contain:
  - repeated headers
  - page markers
  - total/subtotal rows
  - branch separators
  - inconsistent formatting
- customer and employee names are anonymized
- some fields, such as customer address, are sparse or partially unusable

Because of this, the first critical stage of the system is a **robust ingestion and cleaning pipeline**.

---

## 5. What Each Dataset Supports

### `REP_S_00502.csv`
**Purpose:** detailed basket / order-line data  
**Used for:** combo optimization, basket analysis, upsell opportunities

### `rep_s_00334_1_SMRY.csv`
**Purpose:** monthly sales by branch  
**Used for:** demand forecasting by branch

### `REP_S_00461.csv`
**Purpose:** attendance and work duration logs  
**Used for:** shift staffing estimation

### `rep_s_00191_SMRY.csv`
**Purpose:** item-level and category-level sales performance  
**Used for:** beverage strategy, top-product analysis, branch assortment insights

### `REP_S_00136_SMRY.csv`
**Purpose:** category sales by channel (delivery/table/take away)  
**Used for:** category-channel analysis, branch strategy, growth strategy

### `rep_s_00435_SMRY.csv`
**Purpose:** customer count, sales, and average sales by menu/channel  
**Used for:** channel strategy, average ticket analysis, expansion signal support

### `rep_s_00150.csv`
**Purpose:** customer order history summary  
**Used for:** repeat-customer analysis, recency/frequency/value features

### `REP_S_00194_SMRY.csv`
**Purpose:** branch tax summary  
**Used for:** validation/sanity checks on branch totals

---

## 6. System Architecture

The system is organized into four layers:

### A. Data Layer
Handles:
- raw CSV ingestion
- cleaning and parsing
- transformation into structured processed tables

### B. Analytics Layer
Handles:
- combo mining
- demand forecasting
- staffing estimation
- branch KPI generation
- beverage growth recommendations
- expansion feasibility scoring

### C. Service Layer
A **FastAPI backend** exposes the operational capabilities via endpoints.

### D. Agent Layer
**OpenClaw** acts as the operational interface and can invoke the system using a workspace skill.

---

## 7. Project Structure

```text
conut-chief-ops-agent/
│
├── README.md
├── requirements.txt
├── .env.example
├── Makefile
├── main.py
│
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
│
├── pipelines/
│   ├── 01_clean_monthly_sales.py
│   ├── 02_clean_category_channel_sales.py
│   ├── 03_clean_item_sales.py
│   ├── 04_clean_customer_orders.py
│   ├── 05_clean_baskets.py
│   ├── 06_clean_attendance.py
│   ├── 07_build_kpis.py
│   └── run_all.py
│
├── app/
│   ├── api/
│   │   ├── forecast.py
│   │   ├── combos.py
│   │   ├── staffing.py
│   │   ├── expansion.py
│   │   └── growth.py
│   │
│   ├── services/
│   │   ├── forecast_service.py
│   │   ├── combo_service.py
│   │   ├── staffing_service.py
│   │   ├── expansion_service.py
│   │   └── growth_service.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── loaders.py
│   │   └── utils.py
│   │
│   └── schemas/
│       ├── forecast.py
│       ├── combos.py
│       ├── staffing.py
│       ├── expansion.py
│       └── growth.py
│
├── tests/
│   ├── test_cleaning.py
│   ├── test_endpoints.py
│   └── test_business_logic.py
│
├── docs/
│   ├── architecture.png
│   ├── executive_brief.pdf
│   └── demo_screenshots/
│
└── skills/
    └── conut_ops/
        └── SKILL.md
```

---

## 8. Pipeline Overview

The project follows an end-to-end pipeline:

### Stage 1 — Ingestion
Load the raw report-style CSV files from `data/raw/`.

### Stage 2 — Cleaning and Parsing
Transform each report into clean structured tables by:
- removing repeated page headers
- removing footer lines and totals
- normalizing branch names
- parsing dates/times
- converting numeric fields
- removing duplicate report copies
- handling cancellations / negative rows where appropriate

### Stage 3 — Processed Tables
The cleaned outputs are stored in `data/processed/` as canonical datasets, such as:

- `branch_monthly_sales.csv`
- `category_channel_sales.csv`
- `item_sales.csv`
- `customer_orders.csv`
- `basket_lines.csv`
- `attendance.csv`
- `menu_channel_summary.csv`
- `branch_kpis.csv`

### Stage 4 — Analytics / Modeling
Use the processed tables to generate operational insights.

### Stage 5 — API Inference Layer
Expose decision-support functions through FastAPI endpoints.

### Stage 6 — OpenClaw Interaction
OpenClaw invokes the system and returns operational responses.

---

## 9. Methods Used

The project intentionally favors **robust, explainable, and lightweight methods** over unnecessary model complexity.

### Combo Optimization
Uses basket analysis on order-level data:
- item frequency
- pair frequency
- support
- confidence
- lift

### Demand Forecasting by Branch
Uses lightweight forecasting because branch sales history is short:
- naive baseline
- weighted moving average
- simple trend regression

### Shift Staffing Estimation
Uses:
- historical attendance by branch
- shift bucketing by punch-in time
- branch/shift median staff estimates
- demand-adjusted staffing recommendations

### Expansion Feasibility
Uses a weighted scorecard based on:
- recent demand trend
- branch strength
- average ticket/channel health
- repeat customer signal
- product mix
- beverage attachment strength

### Coffee and Milkshake Growth Strategy
Uses:
- item/category sales analysis
- channel mix
- cross-branch comparison
- combo opportunities
- rule-based recommendation generation

---

## 10. Why We Did Not Use Heavy Deep Learning

The available data is:
- messy
- relatively short in time horizon
- partly aggregated
- intentionally scaled

For this reason, using very heavy forecasting architectures or training deep models from scratch would not be the most defensible choice.

Instead, this project emphasizes:
- strong data engineering
- explainable analytics
- business realism
- reproducibility
- operational usability

This is more aligned with the actual hackathon objective: **a reliable AI system Conut could realistically use**.

---

## 11. Core Processed Tables

### `branch_monthly_sales.csv`
Used for branch-level trend and demand forecasting.

### `category_channel_sales.csv`
Used for category-channel strategy and beverage growth insights.

### `item_sales.csv`
Used for item-level performance, hero products, and branch assortment analysis.

### `customer_orders.csv`
Used for repeat-customer analysis and customer-value signals.

### `basket_lines.csv`
Used for combo and co-purchase mining.

### `attendance.csv`
Used for staffing estimation by branch and shift.

### `menu_channel_summary.csv`
Used for average ticket and menu-channel insights.

### `branch_kpis.csv`
Master branch-level KPI table used in scoring and executive reporting.

---

## 12. Business Objectives and How They Are Solved

## 12.1 Combo Optimization

**Goal:** identify optimal product combinations based on purchasing patterns.

**Data used:**
- `basket_lines.csv`
- `item_sales.csv`

**Approach:**
- reconstruct baskets from line-item sales
- remove cancellations and non-informative rows
- compute co-purchase patterns
- rank branch-specific combos
- identify dessert + drink opportunities
- identify add-on upsell opportunities

**Output examples:**
- top bundles by branch
- recommended upsell pairs
- evidence-backed combo rationale

---

## 12.2 Demand Forecasting by Branch

**Goal:** estimate branch demand for next-month planning.

**Data used:**
- `branch_monthly_sales.csv`

**Approach:**
- compute branch demand history
- apply moving average and trend-based forecasting
- generate relative demand index
- label branches as:
  - growing
  - stable
  - declining

**Output examples:**
- next-month branch forecast
- trend commentary
- confidence note

---

## 12.3 Expansion Feasibility

**Goal:** evaluate whether opening a new branch is feasible.

**Data used:**
- `branch_monthly_sales.csv`
- `menu_channel_summary.csv`
- `customer_orders.csv`
- `item_sales.csv`

**Approach:**
- build a branch feasibility scorecard
- identify the best-performing branch archetype
- infer which branch profile is most suitable for replication

**Important limitation:**
The internal data does **not** contain enough reliable geographic information to fully justify real location recommendation at street/neighborhood level.  
Therefore, this project primarily recommends the **best expansion profile** and feasibility direction.  
If documented external data is added, candidate areas can also be scored.

---

## 12.4 Shift Staffing Estimation

**Goal:** estimate required employees per shift.

**Data used:**
- `attendance.csv`
- demand forecast outputs

**Approach:**
- parse punch-in / punch-out logs
- bucket shifts into morning / midday / evening
- compute historical staffing patterns by branch and shift
- adjust recommended staffing using demand conditions

**Output examples:**
- recommended staff count for each branch and shift
- low/base/high scenario recommendations

---

## 12.5 Coffee and Milkshake Growth Strategy

**Goal:** increase coffee and milkshake sales.

**Data used:**
- `item_sales.csv`
- `category_channel_sales.csv`
- `basket_lines.csv`
- `menu_channel_summary.csv`

**Approach:**
- measure branch-level coffee and milkshake performance
- identify strong and weak beverage branches
- compare beverage penetration across branches
- identify dessert-beverage bundles
- generate operational sales recommendations

**Output examples:**
- hero beverage products to push
- weak branches needing beverage support
- branch-specific combo recommendations
- promotion and upsell recommendations

---

## 13. API Design

The system exposes a FastAPI backend.

### Health Check
- `GET /health`

Returns:
- service status
- dataset load confirmation

### Combo Suggestions
- `POST /combo`

Returns:
- top recommended combos for a branch
- support/evidence
- explanation

### Demand Forecast
- `POST /forecast`

Returns:
- demand forecast for a branch
- trend classification
- confidence note

### Staffing Recommendation
- `POST /staffing`

Returns:
- recommended staffing for branch/shift
- explanation

### Expansion Feasibility
- `POST /expansion`

Returns:
- feasibility summary
- best branch archetype to replicate
- risks and assumptions

### Beverage Growth Strategy
- `POST /growth-strategy`

Returns:
- coffee and milkshake strategy for a branch
- products to push
- bundle ideas
- explanation

### Optional Summary Endpoint
- `GET /summary`

Returns:
- company-wide top operational highlights

---

## 14. OpenClaw Integration

The final system is designed to be invoked by **OpenClaw**.

### Integration Approach

OpenClaw acts as the interface layer, while this project provides the business intelligence backend.

OpenClaw can invoke the backend through a workspace skill that maps operational prompts to API calls.

### Example Queries OpenClaw Can Handle

- “Forecast next month demand for Conut Jnah.”
- “What combos should we promote in Main Street Coffee?”
- “How many staff should Conut - Tyre schedule for evening shift?”
- “Give me a coffee and milkshake growth strategy for the weakest branch.”
- “Is expansion feasible, and what type of branch should Conut open next?”

### Skill Folder
The OpenClaw skill is expected inside:

```text
skills/conut_ops/SKILL.md
```

### Expected Skill Behavior
The skill should route user requests to:
- `/combo`
- `/forecast`
- `/staffing`
- `/expansion`
- `/growth-strategy`

---

## 15. Reproducibility

This project is designed to be executable from scratch.

### Requirements
- Python 3.10+
- pip / virtual environment
- FastAPI + Uvicorn
- processed raw CSV files in `data/raw/`

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Run the Pipeline

```bash
python pipelines/run_all.py
```

This should:
- clean all raw datasets
- generate processed tables
- build branch KPIs
- prepare data for the API layer

### Run the API

```bash
uvicorn main:app --reload
```

Default local API:
```text
http://127.0.0.1:8000
```

### Example API Endpoints
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

---

## 16. Suggested OpenClaw Demo Flow

1. Run the data pipeline
2. Start the FastAPI backend
3. Start or connect OpenClaw locally
4. Load the `conut_ops` skill
5. Ask operational questions from OpenClaw
6. Capture screenshots or screen recording as demo evidence

### Demo Evidence Should Show
- OpenClaw invoking the system
- responses for at least 3–5 business queries
- visible recommendations/results
- backend or terminal logs if possible

---

## 17. Expected Outputs

The system is expected to produce outputs such as:

### Combo Optimization
- top co-purchased item pairs by branch
- dessert + beverage bundles
- upsell suggestions

### Demand Forecasting
- branch forecast index
- growth/stability/decline tag
- branch ranking by expected demand

### Staffing
- recommended staff counts by branch and shift
- base and peak staffing estimates

### Expansion
- branch archetype replication recommendation
- feasibility score summary
- documented limitations

### Beverage Growth
- branch-specific coffee growth ideas
- milkshake growth opportunities
- hero SKUs to promote
- bundle and upsell actions

---

## 18. Key Assumptions

- numeric values are scaled, so we focus on **relative business insight**
- short historical windows require **lightweight forecasting**
- attendance logs approximate staffing supply, not performance
- sparse address data weakens true geospatial branch expansion analysis
- branch-level strategic recommendations are still valid even when exact geographic targeting is limited

---

## 19. Risks and Limitations

### Data Limitations
- report-style CSV formatting
- duplicate and repeated headers
- sparse geographic information
- scaled values rather than exact business figures
- limited forecasting horizon

### Modeling Limitations
- forecasting is based on limited monthly history
- staffing estimation is inferential, not optimized from demand timestamps
- expansion location recommendation is limited without external location intelligence

### Operational Limitation
- results are only as reliable as the cleaned report data and assumptions applied

---

## 20. Future Work

Possible improvements beyond the hackathon:

- add external demographic / rent / footfall data for true location scoring
- integrate inventory and supplier lead-time signals
- build daily or hourly demand forecasting if finer-grained sales timestamps become available
- add branch-level recommendation dashboards
- add alerting for low-performing categories
- incorporate automated promotion simulation / what-if analysis

---

## 21. Team Workflow Suggestion

### If team of 3
**Member 1:** data cleaning and processed tables  
**Member 2:** analytics/modeling  
**Member 3:** API, OpenClaw integration, README, executive brief, demo evidence

### If team of 2
**Member 1:** data cleaning + forecasting + combos + staffing  
**Member 2:** growth strategy + expansion + API + OpenClaw + documentation

### If solo
Recommended build order:
1. data cleaning
2. combo engine
3. demand forecast
4. staffing estimator
5. beverage growth strategy
6. expansion scorecard
7. API
8. OpenClaw integration
9. README + brief + demo

---

## 22. Deliverables

This repository is intended to contain:

- full source code
- reproducible pipeline
- processed outputs
- documentation
- OpenClaw integration skill
- executive brief PDF
- demo evidence

### Required Submission Artifacts
- public GitHub repository
- `README.md`
- executive brief (max 2 pages PDF)
- demo screenshots or short video
- OpenClaw invoking the system

---

## 23. Executive Summary

This project delivers a practical **Chief of Operations Agent** for Conut by transforming messy operational data into a reproducible decision-support system.

Instead of building a toy model or a notebook-only prototype, the project focuses on:

- robust data engineering
- explainable analytics
- business-oriented insight generation
- operational API access
- OpenClaw integration for real usage

The result is a system that can support real operational questions around:
- demand
- staffing
- bundling
- beverages
- branch expansion

---

## 24. Placeholder for Final Results

> Replace this section with your actual final outputs before submission.

### Example Highlights
- **Best combo opportunities:** `[TO FILL]`
- **Strongest branch trend:** `[TO FILL]`
- **Weakest branch beverage performance:** `[TO FILL]`
- **Recommended expansion profile:** `[TO FILL]`
- **Highest staffing pressure branch:** `[TO FILL]`

---

## 25. How to Cite This Work

If needed in your report/presentation, refer to it as:

**Conut Chief of Operations Agent — AI Engineering Hackathon Submission**  
American University of Beirut

---

## 26. Contact / Team

**Team Members**
- `[Name 1]`
- `[Name 2]`
- `[Name 3]`

**Course**
AI Engineering — American University of Beirut

**Hackathon**
Conut AI Engineering Hackathon  
12-Hour Chief of Operations Agent Challenge