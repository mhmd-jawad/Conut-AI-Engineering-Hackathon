# conut_ops — Conut Chief of Operations Skill

## Purpose

This skill connects OpenClaw to the **Conut Chief of Operations Agent**, an
AI-driven decision-support system for a bakery & café chain with 4 branches.
It answers operational questions about combos, demand forecasts, staffing,
expansion feasibility, and coffee/milkshake growth strategy.

---

## Backend Base URL

```
http://127.0.0.1:8000
```

---

## Primary Endpoint — Natural Language Chat

> **Use this endpoint for ALL user questions.**
> It handles intent classification, entity extraction, service dispatch, and
> response formatting internally.

### `POST /chat`

**Request:**
```json
{
  "question": "<user's natural-language question>"
}
```

**Response:**
```json
{
  "intent": "combo | forecast | staffing | expansion | growth | unknown",
  "branch": "Conut Jnah",
  "answer": "## 🍩 Combo Recommendations — Conut Jnah\n...",
  "confidence": 0.85,
  "elapsed_ms": 312.4,
  "data": { },
  "error": null
}
```

- `answer` — ready-to-display Markdown text (include this in your reply)
- `data` — raw JSON from the underlying service (for programmatic access)
- `confidence` — 0-1 score for how confident the intent classifier is
- `error` — non-null only when something failed

### Example Prompts → Payloads

| User says | Payload |
|-----------|---------|
| "What are the top combos for Conut Jnah?" | `{"question": "What are the top combos for Conut Jnah?"}` |
| "Forecast demand for Conut - Tyre next 4 months" | `{"question": "Forecast demand for Conut - Tyre next 4 months"}` |
| "How many staff for the evening shift at Conut?" | `{"question": "How many staff for the evening shift at Conut?"}` |
| "Should we expand? Where should we open next?" | `{"question": "Should we expand? Where should we open next?"}` |
| "Give me a coffee growth strategy for Main Street Coffee" | `{"question": "Give me a coffee growth strategy for Main Street Coffee"}` |
| "Show me all branch forecasts" | `{"question": "Show me all branch forecasts"}` |

---

## Discovery Endpoint

### `GET /branches`

Returns valid branch names and shift values for entity validation.

```json
{
  "branches": ["Conut", "Conut - Tyre", "Conut Jnah", "Main Street Coffee"],
  "shifts": ["morning", "midday", "evening"],
  "default_horizon_months": 3,
  "default_top_k": 5
}
```

### `GET /health`

```json
{ "status": "ok", "service": "conut-chief-ops-agent" }
```

---

## Direct Objective Endpoints (Advanced)

These can be called directly if you need fine-grained control instead of
natural-language input.

### 1. `POST /combo` — Product Combo Optimization

```json
// Request
{ "branch": "Conut Jnah", "top_k": 5 }

// Response
{
  "branch": "Conut Jnah",
  "total_baskets": 1842,
  "combos": [
    {
      "item_a": "Mini Donut",
      "item_b": "Iced Latte",
      "support": 0.12,
      "confidence_a_to_b": 0.38,
      "lift": 2.14,
      "revenue_impact": 4520.0,
      "suggested_bundle_price": 85.0
    }
  ]
}
```

### 2. `POST /forecast` — Demand Forecasting by Branch

```json
// Request
{ "branch": "Conut - Tyre", "horizon_months": 4 }

// Response
{
  "branch": "Conut - Tyre",
  "history": [ {"label": "2025-07", "value": 1200.5}, ... ],
  "forecasts": [
    {
      "label": "2026-03",
      "naive": 1100.0,
      "wma": 1150.3,
      "trend_regression": 1180.0,
      "ensemble": 1143.4
    }
  ],
  "trend_classification": "growing",
  "mom_growth_pct": 3.2,
  "confidence_interval": { "lower": 1050.0, "upper": 1250.0 },
  "anomalies": []
}
```

### 3. `POST /staffing` — Shift Staffing Estimation

```json
// Request
{ "branch": "Conut", "shift": "evening" }

// Response
{
  "branch": "Conut",
  "shift": "evening",
  "scenarios": {
    "conservative": { "headcount": 3 },
    "recommended":  { "headcount": 4 },
    "peak":         { "headcount": 5 }
  },
  "rationale": "Based on attendance patterns and demand for evening shift."
}
```

### 4. `POST /expansion` — Expansion Feasibility

```json
// Request
{ "branch": "" }

// Response
{
  "verdict": "Cautiously Positive",
  "best_archetype": { "branch": "Conut Jnah", "total_score": 78.5 },
  "branch_scorecards": [ ... ],
  "candidate_locations": [
    { "area": "Hamra", "location_score": 82.3 }
  ]
}
```

### 5. `POST /growth-strategy` — Coffee & Milkshake Growth

```json
// Request
{ "branch": "Main Street Coffee" }

// Response
{
  "branch": "Main Street Coffee",
  "branches": [
    {
      "branch": "Main Street Coffee",
      "beverage_penetration_pct": 18.4,
      "coffee_revenue": 12500.0,
      "milkshake_revenue": 4300.0,
      "hero_coffee_items": [ {"description": "Iced Latte", "total_amount": 5200.0} ],
      "hero_milkshake_items": [ {"description": "Oreo Shake", "total_amount": 2100.0} ],
      "underperforming_items": [ {"description": "Hot Mocha", "gap_pct": 62.0} ],
      "actions": [ {"recommendation": "Bundle Iced Latte with top-selling donut"} ]
    }
  ]
}
```

---

## Entity Reference

### Branch Names (exact values)

| User might say | Canonical value |
|----------------|-----------------|
| "Conut", "main branch" | `Conut` |
| "Tyre", "Conut Tyre", "Conut - Tyre" | `Conut - Tyre` |
| "Jnah", "Conut Jnah" | `Conut Jnah` |
| "Main Street", "MSC", "Main Street Coffee" | `Main Street Coffee` |
| "all branches", "every branch" | queries all 4 automatically |

### Shifts

`morning` · `midday` · `evening`

### Numeric Parameters

| Parameter | Default | Range | Used by |
|-----------|---------|-------|---------|
| `horizon_months` | 3 | 1–12 | forecast |
| `top_k` | 5 | 1–20 | combo |

---

## Response Handling

1. **Always display the `answer` field** from `/chat` — it is pre-formatted
   Markdown ready for the user.
2. Use `data` for follow-up computations or structured extraction.
3. If `error` is not null, show a friendly message and suggest rephrasing.
4. If `intent` is `"unknown"`, the answer field contains a help menu listing
   what the agent can do — display it to guide the user.

---

## Error & Fallback Behavior

| Scenario | Action |
|----------|--------|
| API timeout (>10 s) | Retry once, then say: "The analytics service is momentarily busy. Please try again." |
| HTTP 422 (validation) | Extract the missing field from the error detail and ask the user for it. |
| HTTP 500 | Say: "Something went wrong on our end. Please try again shortly." |
| `intent` = `unknown` | Display the help text returned in `answer`. |
| `confidence` < 0.3 | Append: "I'm not fully sure I understood — did you mean one of these?" and list the 5 capabilities. |
| Branch not recognized | Call `GET /branches` and suggest the closest match: "Did you mean Conut - Tyre?" |

---

## Quick-Start Checklist

1. Ensure the FastAPI server is running: `uvicorn main:app --host 127.0.0.1 --port 8000`
2. Verify: `GET http://127.0.0.1:8000/health` → `{"status": "ok"}`
3. Load this skill in OpenClaw.
4. Ask any of the example prompts above.
5. The `/chat` endpoint handles everything — no manual routing needed.
