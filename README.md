<div align="center">

#  Conut  Chief of Operations Agent

**AI-Driven Decision-Support System  AUB AI Engineering Hackathon**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.134-009688?logo=fastapi&logoColor=white)](#api-reference)
[![OpenAI GPT-4o](https://img.shields.io/badge/OpenAI-GPT--4o-412991?logo=openai&logoColor=white)](#architecture)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Live%20Bot-26A5E4?logo=telegram&logoColor=white)](https://t.me/AiEngineering503Nbot)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](#running-with-docker)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green)](#license)

*Prof. Ammar Mohanna · American University of Beirut*

**Team:** Mohammad Jawad · Hassan Fouani · Mohammad Jaafar Farhat

</div>

---

## 🚀 Try It Now

The backend is **deployed and running**. Two ways to interact:

| Interface | Link |
|-----------|------|
| 🌐 **Web Dashboard** | [conut-ai-engineering-hackathon.vercel.app](https://conut-ai-engineering-hackathon.vercel.app) |
| 💬 **Telegram Bot** | [t.me/AiEngineering503Nbot](https://t.me/AiEngineering503Nbot) |

Just open the link and start asking questions:

```
"Forecast demand for Conut Jnah next 3 months"
"Best combos for Conut - Tyre?"
"How many staff for evening shift?"
"Should we expand? Where in Lebanon?"
"How do we grow milkshake sales?"
```

---

## Business Objectives

Addresses all 5 hackathon requirements using real Conut operational data:

| Objective | What it does |
|-----------|-------------|
|  **Combo Optimization** | Market-basket analysis (support / confidence / lift) + cosine similarity to find best product bundles |
|  **Demand Forecasting** | Ensemble of Naive, WMA, and Linear Trend models  up to 6 months ahead per branch |
|  **Staffing Estimation** | Optimal headcount per shift using attendance patterns and sales velocity |
|  **Expansion Feasibility** | 6-KPI branch scorecard + ranked Lebanese candidate cities |
|  **Beverage Growth** | Coffee & milkshake strategy derived from all 7 data sources |

---

## Architecture

```
Telegram / Frontend / OpenClaw
          |
          |  POST /chat  (natural language)
          v
    +--------------+
    |   FastAPI    |  main.py  single gateway, 6 routers
    +--------------+
          |
          v
    +----------------------------------+
    |       Agent Orchestrator         |
    |                                  |
    |  GPT-4o intent classifier        |  <- primary
    |  Regex fallback (50+ patterns)   |  <- zero-API fallback
    |  Entity extractor (branch/shift) |
    +----------------+-----------------+
                     |
       +-------------+-------------+----------+----------+
       v             v             v          v          v
    combo        forecast      staffing   expansion   growth
    service      service       service    service     service
       |
       v
  11 processed CSVs  <-  ETL pipelines  <-  7 raw report exports
```

---

## Running with Docker

Docker is the **recommended way** to run the full stack. A single command starts all 3 services automatically  API, Telegram bot, and frontend:

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- A `.env` file with your OpenAI API key (optional  the agent works via regex fallback without it)

```bash
# Create .env
echo OPENAI_API_KEY=sk-your-key-here > .env
```

### Start Everything

```bash
docker compose up --build -d
```

That's it. All 3 services are now running:

| Service | What runs | URL |
|---------|-----------|-----|
| `api` | FastAPI backend (uvicorn) | http://localhost:8000/docs |
| `telegram-bot` | Telegram bot  auto-starts, auto-restarts |  |
| `frontend` | React dashboard (nginx) | http://localhost:8080 |

> **The Telegram bot requires no manual action.** `restart: always` means it starts with Docker and recovers from crashes automatically.

### Useful Commands

```bash
docker compose ps                     # see all running services
docker compose logs telegram-bot -f   # watch bot logs live
docker compose logs api -f            # watch API logs live
docker compose down                   # stop everything
docker compose up -d                  # start again (no rebuild)
docker compose up --build -d          # rebuild + start (after code changes)
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Natural-language question  AI answer |
| `GET` | `/forecast?branch=Conut` | Demand forecast |
| `GET` | `/combos?branch=Conut+Jnah` | Combo recommendations |
| `GET` | `/staffing?branch=Conut+-+Tyre` | Shift staffing estimate |
| `GET` | `/expansion` | Expansion feasibility + candidate cities |
| `GET` | `/growth` | Beverage growth strategy |
| `GET` | `/branches` | List all valid branches |
| `GET` | `/health` | Health check |

**Example  POST /chat:**
```json
{ "question": "Forecast demand for Tyre next month" }
```
```json
{
  "intent": "forecast",
  "branch": "Conut - Tyre",
  "answer": " Demand Forecast  Conut - Tyre\n...",
  "confidence": 0.95
}
```

---

## OpenClaw Integration

Registered as an OpenClaw skill via [`skills/conut_ops/SKILL.md`](skills/conut_ops/SKILL.md).

OpenClaw connects through:
- `GET /branches`  discover available branches and entities
- `POST /chat`  route any natural-language operational query
- Individual service endpoints for programmatic access

---

## Branches

| Branch | Accepted inputs |
|--------|----------------|
| **Conut** | `conut` |
| **Conut - Tyre** | `tyre`, `conut tyre` |
| **Conut Jnah** | `jnah`, `conut jnah` |
| **Main Street Coffee** | `main street`, `msc` |

Use `all` to aggregate across all branches (where supported).

---

## Project Structure

```
 main.py                  # FastAPI entry point
 telegram_bot.py          # Telegram bot
 Dockerfile               # Backend + bot image (shared)
 docker-compose.yml       # 3 services: api, telegram-bot, frontend
 requirements.txt
 app/
    agent/               # GPT-4o classifier, regex fallback, formatter
    api/                 # REST route handlers
    services/            # Business logic engines
    schemas/             # Pydantic request/response models
 data/
    raw/                 # Original CSV report exports
    processed/           # Cleaned tables (ETL output)
 pipelines/               # ETL cleaning scripts + run_all.py
 skills/conut_ops/        # OpenClaw SKILL.md
 tests/                   # Test suite
```

---

## License

Apache License 2.0  see [LICENSE](LICENSE).
