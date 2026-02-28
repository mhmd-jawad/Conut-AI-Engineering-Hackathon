<div align="center">

# 🍩 Conut — Chief of Operations Agent

**AI-Driven Decision-Support System for a Bakery & Café Chain**

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue?logo=python&logoColor=white)](#prerequisites)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.134-009688?logo=fastapi&logoColor=white)](#tech-stack)
[![OpenAI GPT-4o](https://img.shields.io/badge/OpenAI-GPT--4o-412991?logo=openai&logoColor=white)](#llm-intent-classification)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)](#telegram-bot)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green)](#license)

*Built for the AUB AI Engineering Hackathon*

</div>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Telegram Bot](#telegram-bot)
- [LLM Intent Classification](#llm-intent-classification)
- [OpenClaw Integration](#openclaw-integration)
- [Data Pipeline](#data-pipeline)
- [Testing](#testing)
- [Configuration](#configuration)
- [License](#license)

---

## Overview

**Conut Chief of Operations Agent** is an end-to-end operational AI system built for **Conut**, a bakery & café chain with **4 branches** across Lebanon. It answers natural-language business questions by routing them through an intelligent agent pipeline backed by 5 analytics services — all powered by real transactional data.

Ask the agent a question in plain English (or via Telegram), and it will classify your intent, extract entities, run the analysis, and return a beautifully formatted answer.

> *"What are the best combos for Conut Jnah?"*
> *"Forecast demand for the next 3 months"*
> *"How many staff do we need for the evening shift?"*
> *"Should we expand to a new area?"*
> *"How can we grow milkshake sales?"*

---

## Key Features

| # | Objective | What It Does |
|---|-----------|--------------|
| 🍩 | **Combo Optimization** | Market-basket analysis (support / confidence / lift) + ML cosine-similarity to find the best product bundles, with suggested combo pricing |
| 📈 | **Demand Forecasting** | Ensemble of Naive, Weighted Moving Average, and Linear Trend models to project branch-level revenue up to 6 months ahead |
| 👥 | **Staffing Estimation** | Calculates optimal headcount per shift per branch using attendance patterns, sales velocity, and efficiency metrics |
| 🌍 | **Expansion Feasibility** | Scores existing branches on 6 KPI dimensions, identifies the best archetype, and ranks candidate Lebanese cities for replication |
| ☕ | **Beverage Growth Strategy** | Analyses coffee & milkshake performance across all 7 data sources — hero products, channel gaps, dessert-beverage bundles, revenue momentum, and customer metrics |
| 💬 | **Conversational AI** | Natural chitchat and greetings handled gracefully via GPT-4o, so users get a friendly experience even outside business queries |

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Telegram / API Client                  │
└────────────────────────┬─────────────────────────────────┘
                         │  POST /chat
                         ▼
┌──────────────────────────────────────────────────────────┐
│                    FastAPI Gateway                        │
│                    (main.py)                              │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│               🤖 Agent Orchestrator                       │
│                  (agent.py)                               │
│                                                          │
│   question ──► smart_classify() ──► dispatch() ──► format│
│                     │                    │                │
│            ┌────────┴────────┐     ┌─────┴──────┐        │
│            │  GPT-4o LLM    │     │  5 Service  │        │
│            │  (primary)     │     │  Engines    │        │
│            │                │     │             │        │
│            │  Regex         │     │  combo      │        │
│            │  (fallback)    │     │  forecast   │        │
│            └────────────────┘     │  staffing   │        │
│                                   │  expansion  │        │
│                                   │  growth     │        │
│                                   └─────────────┘        │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│              📊 Data Layer (11 processed CSVs)            │
│              from 7+ raw report exports                   │
└──────────────────────────────────────────────────────────┘
```

**4 layers:**

1. **Data Layer** — ETL pipelines clean raw CSV exports into 11 canonical processed tables
2. **Analytics Layer** — 5 service engines compute recommendations using pandas, scikit-learn, and statistical models
3. **Agent Layer** — GPT-4o intent classifier + regex fallback + entity extraction + response formatting
4. **Interface Layer** — FastAPI REST API + Telegram Bot + OpenClaw skill

For detailed architecture docs, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Tech Stack

| Category | Technologies |
|----------|-------------|
| **API Framework** | FastAPI 0.134, Uvicorn |
| **Data & ML** | pandas, NumPy, scikit-learn, SciPy |
| **LLM** | OpenAI GPT-4o (intent classification + chitchat) |
| **Bot** | python-telegram-bot 22.6 |
| **Validation** | Pydantic v2 |
| **Agent Platform** | OpenClaw (SKILL.md) |
| **Language** | Python 3.12+ |

---

## Project Structure

```text
Conut-AI-Engineering-Hackathon/
│
├── main.py                          # FastAPI app entry point
├── telegram_bot.py                  # Telegram bot (forwards to /chat)
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variable template
│
├── app/
│   ├── agent/                       # 🤖 AI Agent layer
│   │   ├── agent.py                 #    Orchestrator: classify → dispatch → format
│   │   ├── llm_intent.py            #    GPT-4o intent classifier (primary)
│   │   ├── intent.py                #    Regex intent classifier (fallback)
│   │   ├── tools.py                 #    Service dispatcher
│   │   └── formatter.py             #    Telegram-friendly output formatting
│   │
│   ├── api/                         # 🌐 REST endpoints
│   │   ├── chat.py                  #    POST /chat — unified agent endpoint
│   │   ├── combos.py                #    GET  /combos
│   │   ├── forecast.py              #    GET  /forecast
│   │   ├── staffing.py              #    GET  /staffing
│   │   ├── expansion.py             #    GET  /expansion
│   │   └── growth.py                #    GET  /growth
│   │
│   ├── services/                    # ⚙️ Business logic engines
│   │   ├── combo_service.py         #    Basket analysis + cosine similarity
│   │   ├── forecast_service.py      #    Ensemble demand forecasting
│   │   ├── staffing_service.py      #    Shift-based headcount estimation
│   │   ├── expansion_service.py     #    6-KPI scorecard + city ranking
│   │   └── growth_service.py        #    Beverage strategy (7 data sources)
│   │
│   ├── schemas/                     # 📋 Pydantic request/response models
│   └── core/                        # 🔧 Config & shared utilities
│
├── data/
│   ├── raw/                         # Original report exports
│   ├── processed/                   # Cleaned CSVs (pipeline output)
│   └── external/                    # Curated external data (documented)
│
├── pipelines/                       # 🔄 ETL cleaning scripts
│   ├── clean_*.py                   #    Per-report cleaning logic
│   └── run_all.py                   #    Run all pipelines in sequence
│
├── skills/
│   └── conut_ops/
│       └── SKILL.md                 # 🧠 OpenClaw skill definition (288 lines)
│
├── tests/                           # ✅ Test suite
│   ├── test_agent.py
│   ├── test_combo_compare.py
│   ├── test_expansion.py
│   ├── test_forecast.py
│   ├── test_staffing.py
│   └── test_openclaw.py             #    20 OpenClaw integration tests
│
└── docs/                            # 📖 Documentation
    ├── ARCHITECTURE.md
    ├── OPENCLAW_INTEGRATION.md
    └── IMPLEMENTATION_ROADMAP.md
```

---

## Quick Start

### Prerequisites

- **Python 3.12+**
- An **OpenAI API key** *(optional — the agent works without one via regex fallback)*

### 1. Clone & Install

```bash
git clone https://github.com/your-org/Conut-AI-Engineering-Hackathon.git
cd Conut-AI-Engineering-Hackathon

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key (optional)
```

### 3. Run the Data Pipeline

```bash
python pipelines/run_all.py
```

### 4. Start the API Server

```bash
python main.py
# or: uvicorn main:app --host 127.0.0.1 --port 8000
```

### 5. Open the Docs

Visit **http://127.0.0.1:8000/docs** for the interactive Swagger UI.

### 6. Start the Telegram Bot *(optional)*

```bash
python telegram_bot.py
```

---

## API Reference

### Primary Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Ask the agent any business question in natural language |

**Request:**
```json
{
  "question": "What are the best combos for Conut Jnah?"
}
```

**Response:**
```json
{
  "intent": "combo",
  "branch": "Conut Jnah",
  "answer": "🍩 Combo Recommendations — Conut Jnah\n...",
  "confidence": 0.90,
  "elapsed_ms": 312.4,
  "data": { "..." : "..." },
  "error": null
}
```

### Service Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/combos` | Product combo recommendations |
| `GET` | `/forecast` | Demand forecasts by branch |
| `GET` | `/staffing` | Shift staffing estimates |
| `GET` | `/expansion` | Expansion feasibility scorecards |
| `GET` | `/growth` | Coffee & milkshake growth strategies |

### Utility Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health check |
| `GET` | `/branches` | List valid branches, shifts, and defaults |

---

## Telegram Bot

The agent is deployed as a **Telegram Bot** for easy demo access. It forwards every message to `POST /chat` and renders the response with emoji-rich formatting.

**Commands:**
| Command | Description |
|---------|-------------|
| `/start` | Welcome message with feature overview |
| `/branches` | List all branches |
| `/health` | Check API health |
| *Any text* | Routed to the AI agent |

**Response footer includes:**
- 🔎 Detected intent
- 🏪 Branch (if applicable)
- 🎯 Confidence score
- ⏱ Response time

---

## LLM Intent Classification

The agent uses a **two-tier classifier**:

```
User Question
     │
     ▼
┌─────────────┐    success    ┌───────────────┐
│  GPT-4o     │──────────────►│ Intent Object │
│  (primary)  │               └───────────────┘
└──────┬──────┘
       │ failure / no API key
       ▼
┌─────────────┐    always     ┌───────────────┐
│  Regex      │──────────────►│ Intent Object │
│  (fallback) │               └───────────────┘
└─────────────┘
```

- **GPT-4o** — A single API call (~100-200 tokens) classifies the question into one of 7 intents with a confidence score. Also handles entity extraction (branch, shift, horizon).
- **Regex fallback** — 50+ keyword patterns across all intents ensure the agent works with zero API calls and instant response time.
- **Supported intents:** `combo` · `forecast` · `staffing` · `expansion` · `growth` · `chitchat` · `unknown`

---

## OpenClaw Integration

The agent is registered as an **OpenClaw skill** via [`skills/conut_ops/SKILL.md`](skills/conut_ops/SKILL.md) (288 lines).

OpenClaw can:
- Discover available entities via `GET /branches`
- Route any natural-language question through `POST /chat`
- Access individual service endpoints for programmatic use

See [`docs/OPENCLAW_INTEGRATION.md`](docs/OPENCLAW_INTEGRATION.md) for full integration details.

---

## Data Pipeline

Raw report exports are cleaned into 11 processed CSVs by the scripts in `pipelines/`.

| Processed File | Source | Used By |
|----------------|--------|---------|
| `monthly_sales_by_branch.csv` | Branch revenue reports | Forecast, Expansion, Growth |
| `basket_lines.csv` | Transaction-level basket data | Combo, Growth |
| `attendance.csv` | Time & attendance records | Staffing, Growth |
| `avg_sales_by_menu_channel.csv` | Channel-level averages | Expansion, Growth |
| `customer_orders_delivery.csv` | Delivery order history | Expansion, Growth |
| `Sales by items and groups.csv` | Item-level sales | Expansion, Growth |
| `Summary by division-menu channel.csv` | Division breakdowns | Expansion, Growth |
| `tax_summary_by_branch.csv` | Tax reports | Pipeline |

Run all pipelines:

```bash
python pipelines/run_all.py
```

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test suites
python -m pytest tests/test_agent.py -v         # Agent pipeline
python -m pytest tests/test_openclaw.py -v       # OpenClaw integration (20 tests)
python -m pytest tests/test_forecast.py -v       # Forecast math
python -m pytest tests/test_combo_compare.py -v  # Combo algorithms
python -m pytest tests/test_expansion.py -v      # Expansion scorecards
python -m pytest tests/test_staffing.py -v       # Staffing estimation
```

---

## Configuration

All configuration is via environment variables (`.env` file). Copy the template to get started:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *(none)* | OpenAI API key for GPT-4o *(optional)* |
| `OPENAI_MODEL` | `gpt-4o` | Model for intent classification |
| `APP_HOST` | `127.0.0.1` | Server bind address |
| `APP_PORT` | `8000` | Server port |
| `DATA_DIR` | `./data/processed` | Path to processed data |
| `MIN_SUPPORT` | `0.05` | Minimum support threshold for combo analysis |
| `MIN_CONFIDENCE` | `0.2` | Minimum confidence threshold for combo analysis |

---

## Branches

The system supports **4 Conut branches**:

| Branch | Aliases |
|--------|---------|
| **Conut** | `conut` |
| **Conut - Tyre** | `tyre`, `conut-tyre`, `conut tyre` |
| **Conut Jnah** | `jnah`, `conut jnah` |
| **Main Street Coffee** | `main street`, `msc` |

---

## License

This project is licensed under the **Apache License 2.0** — see [LICENSE](LICENSE) for details.
