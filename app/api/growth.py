from fastapi import APIRouter

from app.schemas.growth import GrowthRequest, GrowthResponse
from app.services.growth_service import growth_strategy


router = APIRouter()


@router.post("/growth-strategy", response_model=GrowthResponse)
def growth(request: GrowthRequest) -> GrowthResponse:
    return growth_strategy(request.branch)
