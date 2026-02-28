import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.core.config  # noqa: F401 – load .env early

from app.api.chat import router as chat_router
from app.api.combos import router as combos_router
from app.api.expansion import router as expansion_router
from app.api.forecast import router as forecast_router
from app.api.growth import router as growth_router
from app.api.staffing import router as staffing_router


app = FastAPI(title="Conut Chief of Operations Agent", version="0.1.0")
# ── CORS – allow the React dev-server and any deployed front-end ────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Unified agent endpoint (Operational AI Component) ───────────────────
app.include_router(chat_router, tags=["chat"])

# ── Individual objective endpoints ──────────────────────────────────────
app.include_router(combos_router, tags=["combos"])
app.include_router(forecast_router, tags=["forecast"])
app.include_router(staffing_router, tags=["staffing"])
app.include_router(expansion_router, tags=["expansion"])
app.include_router(growth_router, tags=["growth"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "conut-chief-ops-agent"}


@app.get("/branches")
def branches() -> dict:
    """Discovery endpoint – returns valid entity values for OpenClaw."""
    return {
        "branches": ["Conut", "Conut - Tyre", "Conut Jnah", "Main Street Coffee"],
        "shifts": ["morning", "midday", "evening"],
        "default_horizon_months": 3,
        "default_top_k": 5,
    }


if __name__ == "__main__":
    import uvicorn

    # Render injects PORT dynamically; fall back to 8000 for local dev.
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
