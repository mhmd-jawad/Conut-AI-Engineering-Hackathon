from fastapi import APIRouter

from app.schemas.staffing import StaffingRequest
from app.services.staffing_service import recommend_staffing


router = APIRouter()


@router.post("/staffing")
def staffing(request: StaffingRequest) -> dict:
    return recommend_staffing(request.branch, request.shift)
