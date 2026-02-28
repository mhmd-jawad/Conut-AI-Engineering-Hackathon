from fastapi import APIRouter

from app.schemas.expansion import ExpansionRequest, ExpansionResponse
from app.services.expansion_service import evaluate_expansion


router = APIRouter()


@router.post("/expansion", response_model=ExpansionResponse)
def expansion(request: ExpansionRequest) -> ExpansionResponse:
    """Evaluate expansion feasibility and recommend candidate locations."""
    result = evaluate_expansion(request.branch)

    # If the service returned an error dict (unknown branch), raise 404
    if "error" in result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=result)

    return result
