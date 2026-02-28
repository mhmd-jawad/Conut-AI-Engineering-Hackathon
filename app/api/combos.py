from fastapi import APIRouter

from app.schemas.combos import ComboRequest
from app.services.combo_service import recommend_combos


router = APIRouter()


@router.post("/combo")
def combo(request: ComboRequest) -> dict:
    return recommend_combos(request.branch, request.top_k)
