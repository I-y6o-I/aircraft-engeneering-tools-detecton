from typing import List, Optional
from pydantic import BaseModel, Field, conlist
from .common import Detection, Summary, BBox

class PredictRequest(BaseModel):
    image: str = Field(..., description="Image as base64 string")
    threshold: float = Field(0.98, ge=0.0, le=1.0, description="UI threshold for manual verification")

class PredictResponse(BaseModel):
    threshold: float
    classes_catalog: List[str]
    detections: List[Detection]
    not_found: List[str]
    summary: Summary

class Annotation(BaseModel):
    class_: str = Field(..., alias="class")
    # Keep wire format as list[float]; use BBox if you want structured fields:
    box: conlist(float, min_length=4, max_length=4)
    source: Optional[str] = Field(
        default=None, description="Where it came from: model/edited/manual"
    )

    class Config:
        populate_by_name = True

class AdjustRequest(BaseModel):
    # Exactly 11 annotations must be provided (not after predtict, but after adjust from human)!
    annotations: conlist(Annotation, min_length=11, max_length=11)