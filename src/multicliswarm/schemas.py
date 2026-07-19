from pydantic import BaseModel, Field

class ArchitectResponse(BaseModel):
    specification: str = Field(description="A detailed markdown description of the components, function signatures, error handling, and expected behaviors.")
    test_code: str = Field(description="Complete, fully working unit test code designed to verify the correct behavior of the implementation.")
    filename: str = Field(description="The recommended filename where the implementation should be saved.")

class Pricing(BaseModel):
    input_price_per_1m: float
    output_price_per_1m: float

# Approximate pricing per 1M tokens (USD)
MODEL_PRICING = {
    "gemini": Pricing(input_price_per_1m=0.075, output_price_per_1m=0.30),
    "codex": Pricing(input_price_per_1m=5.00, output_price_per_1m=15.00),
    "claude": Pricing(input_price_per_1m=3.00, output_price_per_1m=15.00),
    "mock": Pricing(input_price_per_1m=0.0, output_price_per_1m=0.0),
    "default": Pricing(input_price_per_1m=1.00, output_price_per_1m=3.00)
}

def estimate_cost(engine_name: str, input_tokens: int, output_tokens: int) -> float:
    name_clean = engine_name.lower().strip()
    pricing = MODEL_PRICING.get(name_clean, MODEL_PRICING["default"])
    cost = (input_tokens / 1_000_000) * pricing.input_price_per_1m + (output_tokens / 1_000_000) * pricing.output_price_per_1m
    return cost
