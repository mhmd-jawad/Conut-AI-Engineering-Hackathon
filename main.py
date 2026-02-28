from fastapi import FastAPI

from app.api.combos import router as combos_router
from app.api.expansion import router as expansion_router
from app.api.forecast import router as forecast_router
from app.api.growth import router as growth_router
from app.api.staffing import router as staffing_router


app = FastAPI(title="Conut Chief of Operations Agent", version="0.1.0")

app.include_router(combos_router, tags=["combos"])
app.include_router(forecast_router, tags=["forecast"])
app.include_router(staffing_router, tags=["staffing"])
app.include_router(expansion_router, tags=["expansion"])
app.include_router(growth_router, tags=["growth"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "conut-chief-ops-agent"}
