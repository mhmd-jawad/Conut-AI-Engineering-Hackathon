# Implementation Roadmap (Execution Order)

## Phase 0 — Foundation (30–45 min)

1. Set up Python environment and dependencies.
2. Confirm all raw datasets exist in `data/raw/`.
3. Add `main.py` FastAPI app shell and health endpoint.
4. Add folder skeleton under `app/` and `skills/conut_ops/`.

## Phase 1 — Data Pipeline (2.5–3.5 hours)

1. Implement cleaners for all source reports:
   - monthly sales
   - category-channel sales
   - item sales
   - customer orders
   - baskets
   - attendance
2. Build `pipelines/run_all.py` orchestrator.
3. Write schema assertions after every output table.
4. Generate `branch_kpis.csv` from processed tables.

## Phase 2 — Analytics Services (2–3 hours)

1. Combo engine:
   - basket reconstruction
   - pair metrics (support/confidence/lift)
2. Forecast engine:
   - moving average + trend classification
3. Staffing engine:
   - shift bucketing + demand-adjusted recommendation
4. Expansion engine:
   - weighted scorecard + archetype recommendation
5. Growth engine:
   - beverage penetration + branch playbook generation

## Phase 3 — API Layer (1.5–2 hours)

1. Add schemas in `app/schemas/`.
2. Add service modules in `app/services/`.
3. Add route modules in `app/api/`.
4. Wire endpoints in `main.py`.
5. Validate with `/docs` and sample payloads.

## Phase 4 — OpenClaw Integration (1 hour)

1. Implement `skills/conut_ops/SKILL.md` intent routing.
2. Validate all five objective prompts.
3. Add robust fallback/error messages.

## Phase 5 — Validation + Packaging (1–1.5 hours)

1. Add tests for:
   - cleaning rules
   - endpoint responses
   - critical business logic
2. Produce final insights section in README.
3. Create executive brief PDF (max 2 pages).
4. Capture demo screenshots/video.

## Definition of Done

- End-to-end pipeline executes from raw to processed successfully.
- FastAPI endpoints operational for all five objectives.
- OpenClaw successfully invokes backend for representative prompts.
- Reproducible setup instructions verified from a clean environment.
