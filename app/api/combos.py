from fastapi import APIRouter

from app.schemas.combos import ComboRequest, ComboResponse
from app.services.combo_service import recommend_combos


router = APIRouter()


@router.post("/combo", response_model=ComboResponse)
def combo(request: ComboRequest) -> ComboResponse:
    """Return top-K co-purchased item pairs for a branch (basket analysis)."""
    return recommend_combos(
        branch=request.branch,
        top_k=request.top_k,
        include_modifiers=request.include_modifiers,
        min_support=request.min_support,
        min_confidence=request.min_confidence,
        min_lift=request.min_lift,
    )
