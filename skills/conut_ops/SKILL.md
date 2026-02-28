# conut_ops Skill

## Purpose

Operational skill for Conut Chief of Operations backend.

## Backend Base URL

`http://127.0.0.1:8000`

## Intent Routing

- Combo recommendation -> `POST /combo`
- Demand forecasting -> `POST /forecast`
- Staffing recommendation -> `POST /staffing`
- Expansion feasibility -> `POST /expansion`
- Coffee/milkshake strategy -> `POST /growth-strategy`
- Service health -> `GET /health`

## Input Entity Extraction

Extract when possible:
- `branch`
- `shift`
- `horizon_months`
- `top_k`

## Fallback Behavior

- If branch is missing, ask for branch name.
- If API call fails, return concise fallback and suggest retry.
- Always include recommendation rationale in response.
