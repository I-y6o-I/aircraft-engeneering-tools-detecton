from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, conint, conlist
from .predict import PredictResponse, Annotation
from .common import SessionStatus, Stage

class CreateHandoutRequest(BaseModel):
    threshold: float = Field(0.98, ge=0.0, le=1.0)
    notes: Optional[str] = None

class CreateHandoutResponse(BaseModel):
    session_id: str
    status: SessionStatus
    threshold_used: float
    created_at: str  # ISO8601

class SessionPredictRequest(BaseModel):
    image: str
    threshold: float = Field(0.98, ge=0.0, le=1.0)

# Reuse PredictResponse for body; server updates internal status accordingly.
SessionPredictResponse = PredictResponse

class SessionAdjustRequest(BaseModel):
    # Exactly 11 annotations
    annotations: conlist(Annotation, min_length=11, max_length=11)

class SessionAdjustResponse(BaseModel):
    ok: bool
    issues: Optional[List[str]] = None
    stage: Stage
    count: conint(ge=0)  # number of accepted annotations

class IssueRequest(BaseModel):
    confirm: bool = True

class IssueResponse(BaseModel):
    status: Literal["issued"]
    issued_at: str

class FinalizeRequest(BaseModel):
    confirm: bool = True

class FinalizeResponse(BaseModel):
    status: Literal["returned"]
    returned_at: str

class SessionsListItem(BaseModel):
    id: str
    employee_id: Optional[str] = None
    status: SessionStatus
    notes: Optional[str] = None
    created_at: str
    updated_at: str

class SessionsListResponse(BaseModel):
    page: int
    limit: int
    total: int
    items: List[SessionsListItem]

class HandStageSnapshot(BaseModel):
    predict: Optional[PredictResponse] = None
    final: Optional[Dict] = None  # use your final annotations structure
    image: Optional[str] = None  # base64 encoded image
    issued_at: Optional[str] = None
    returned_at: Optional[str] = None

class SessionCardResponse(BaseModel):
    id: str
    employee_id: Optional[str] = None
    status: SessionStatus
    threshold_used: float
    notes: Optional[str] = None
    issued_at: Optional[str] = None  # when tools were issued
    returned_at: Optional[str] = None  # when tools were returned
    handout: Optional[HandStageSnapshot] = None
    handover: Optional[HandStageSnapshot] = None
    hash: Optional[str] = None  # sha256:...

class DiffResponse(BaseModel):
    expected: Dict[str, int]
    handout_final: Dict[str, Dict]
    handover_final: Dict[str, Dict]
    missing: List[str]  # present in handout, absent in handover
    extra: List[str]    # found but not expected (usually empty in this task)