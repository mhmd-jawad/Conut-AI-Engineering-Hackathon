def recommend_combos(branch: str, top_k: int) -> dict:
    return {
        "branch": branch,
        "top_k": top_k,
        "recommendations": [],
        "explanation": "Combo engine scaffold ready; connect to basket_lines processing.",
    }
