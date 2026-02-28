from pydantic import BaseModel, Field


class ComboRequest(BaseModel):
    branch: str = Field(..., min_length=1, description="Branch name or 'all' for global analysis")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of top combo pairs to return")
    include_modifiers: bool = Field(
        default=False,
        description="Include zero-price modifiers/toppings (e.g. WHIPPED CREAM) in combo analysis",
    )
    min_support: float = Field(default=0.02, ge=0.0, le=1.0, description="Minimum support threshold")
    min_confidence: float = Field(default=0.15, ge=0.0, le=1.0, description="Minimum confidence threshold")
    min_lift: float = Field(default=1.0, ge=0.0, description="Minimum lift threshold")


class ComboCompareRequest(BaseModel):
    branch: str = Field(..., min_length=1, description="Branch name or 'all' for global analysis")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of top combo pairs to return")
    include_modifiers: bool = Field(
        default=False,
        description="Include zero-price modifiers/toppings (e.g. WHIPPED CREAM) in combo analysis",
    )
    min_support: float = Field(default=0.02, ge=0.0, le=1.0, description="Minimum support threshold")
    min_confidence: float = Field(default=0.15, ge=0.0, le=1.0, description="Minimum confidence threshold")
    min_lift: float = Field(default=1.0, ge=0.0, description="Minimum lift threshold")


class ComboPair(BaseModel):
    item_a: str
    item_b: str
    support: float = Field(description="Fraction of baskets containing both items")
    confidence_a_to_b: float = Field(description="P(B | A) confidence that A leads to B")
    confidence_b_to_a: float = Field(description="P(A | B) confidence that B leads to A")
    lift: float = Field(description="Lift >1 means positive association")
    basket_count: int = Field(description="Number of baskets containing both items")
    avg_combo_revenue: float = Field(description="Average combined revenue when both items are in a basket")
    price_a: float = Field(description="Average unit price of item A")
    price_b: float = Field(description="Average unit price of item B")
    individual_total: float = Field(description="Sum of individual prices (price_a + price_b)")
    suggested_combo_price: float = Field(description="Suggested bundle price (12% discount)")
    savings: float = Field(description="Customer savings vs buying individually")


class ComboMLPair(BaseModel):
    item_a: str
    item_b: str
    similarity_score: float = Field(description="Cosine similarity score learned from the basket-item matrix")
    support_train: float = Field(description="Pair support in training baskets")
    basket_count_train: int = Field(description="Pair count in training baskets")
    price_a: float = Field(description="Average unit price of item A")
    price_b: float = Field(description="Average unit price of item B")
    individual_total: float = Field(description="Sum of individual prices (price_a + price_b)")
    suggested_combo_price: float = Field(description="Suggested bundle price (12% discount)")
    savings: float = Field(description="Customer savings vs buying individually")


class ComboResponse(BaseModel):
    branch: str
    total_baskets: int
    include_modifiers: bool
    recommendations: list[ComboPair]
    explanation: str


class ComboCompareResponse(BaseModel):
    branch: str
    model_name: str
    non_ai_answer_line: str
    ml_answer_line: str
    ml_precision_at_k: float | None
    non_ai_recommendations: list[ComboPair]
    ml_recommendations: list[ComboMLPair]
    evaluation_note: str
    explanation: str
