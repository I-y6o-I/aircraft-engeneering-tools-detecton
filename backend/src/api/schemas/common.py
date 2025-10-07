from typing import List, Literal
from pydantic import BaseModel, Field, field_validator, conlist

class BBox(BaseModel):
    """Normalized bounding box in [0..1] for (x_center, y_center, width, height)."""
    
    x_center: float = Field(..., ge=0.0, le=1.0)
    y_center: float = Field(..., ge=0.0, le=1.0)
    width: float = Field(..., ge=0.0, le=1.0)
    height: float = Field(..., ge=0.0, le=1.0)

    @field_validator("width", "height")
    @classmethod
    def non_zero(cls, v: float) -> float:
        # Allow zero but it's unusual; adjust if needed
        return v

class Detection(BaseModel):
    detection_id: str = Field(..., description="Local candidate id, e.g. det-001")
    class_: str = Field(..., alias="class")
    confidence: float
    is_passed_conf_treshold: bool
    # Keep wire format as list[float] for compatibility with /predict response
    box: conlist(float, min_length=4, max_length=4)
    model_config = {"populate_by_name": True}

class Annotation(BaseModel):
    class_: str = Field(..., alias="class")
    # Keep wire format as list[float] for compatibility with /predict/adjust request
    box: conlist(float, min_length=4, max_length=4)
    source: Literal["model", "manual", "edited"] = "model"

    model_config = {"populate_by_name": True}

class Summary(BaseModel):
    expected_total: int
    found_candidates: int
    passed_above_threshold: int
    requires_manual_count: int
    not_found_count: int

Stage = Literal["handout", "handover"]
SessionStatus = Literal[
    "draft",
    "handout_auto",
    "handout_needs_manual",
    "issued",
    "handover_auto",
    "handover_needs_manual",
    "returned",
]