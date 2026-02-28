def recommend_staffing(branch: str, shift: str) -> dict:
    return {
        "branch": branch,
        "shift": shift,
        "recommended_staff": None,
        "explanation": "Staffing engine scaffold ready; connect attendance and demand inputs.",
    }
