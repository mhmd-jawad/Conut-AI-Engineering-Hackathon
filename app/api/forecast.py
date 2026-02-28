from fastapi import APIRouter, HTTPException

from app.schemas.forecast import ForecastRequest, ForecastResponse
from app.services.forecast_service import forecast_branch_demand


router = APIRouter()


@router.post("/forecast", response_model=ForecastResponse)
def forecast(request: ForecastRequest):
    result = forecast_branch_demand(request.branch, request.horizon_months)
    if "error" in result and result["error"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
