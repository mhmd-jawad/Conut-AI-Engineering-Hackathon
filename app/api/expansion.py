from fastapi import APIRouter

from app.schemas.expansion import ExpansionRequest
from app.services.expansion_service import evaluate_expansion


router = APIRouter()


@router.post("/expansion")
def expansion(request: ExpansionRequest) -> dict:
    return evaluate_expansion(request.branch)
