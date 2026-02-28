from fastapi import APIRouter

from app.schemas.forecast import ForecastRequest
from app.services.forecast_service import forecast_branch_demand


router = APIRouter()


@router.post("/forecast")
def forecast(request: ForecastRequest) -> dict:
    return forecast_branch_demand(request.branch, request.horizon_months)
