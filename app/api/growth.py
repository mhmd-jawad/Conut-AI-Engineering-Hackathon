from fastapi import APIRouter

from app.schemas.growth import GrowthRequest
from app.services.growth_service import growth_strategy


router = APIRouter()


@router.post("/growth-strategy")
def growth(request: GrowthRequest) -> dict:
    return growth_strategy(request.branch)
