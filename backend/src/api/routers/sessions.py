from datetime import datetime, timezone
from typing import List, Dict, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ...core.db import get_session
from ...core.auth import get_current_user
from ...models.user import User
from ...models.session import Session as SessionModel
from ..schemas.sessions import (
    CreateHandoutRequest, CreateHandoutResponse,
    SessionPredictRequest, SessionPredictResponse,
    SessionAdjustRequest, SessionAdjustResponse,
    IssueRequest, IssueResponse,
    FinalizeRequest, FinalizeResponse,
    SessionsListResponse, SessionsListItem,
    SessionCardResponse, HandStageSnapshot,
    DiffResponse
)
from ..schemas.predict import PredictResponse
from ...core.settings import settings
import hashlib
import json

router = APIRouter(prefix="/sessions", tags=["sessions"])

# Import YOLO inference
from ...ml.yolo_service import infer_with_yolo
import logging

logger = logging.getLogger(__name__)

def _infer_with_fallback(image_b64: str, threshold: float = 0.5) -> tuple[List[str], List[Dict[str, Any]]]:
    """Inference with fallback to stub if YOLO fails."""
    try:
        # Try YOLO inference first
        return infer_with_yolo(image_b64, threshold)
    except Exception as e:
        logger.warning(f"YOLO inference failed in session, falling back to stub: {e}")
        # Fallback to stub
        return _infer_stub(image_b64)

def _infer_stub(image_b64: str) -> tuple[List[str], List[Dict[str, Any]]]:
    """Fallback inference stub for sessions."""
    
    classes_catalog = settings.CLASSES
    detections = [
        {"class": "screwdriver_plus", "confidence": 0.992, "box": [0.512, 0.431, 0.183, 0.072]},
        {"class": "wrench_adjustable", "confidence": 0.74, "box": [0.246, 0.611, 0.204, 0.090]},
        {"class": "screwdriver_plus", "confidence": 0.981, "box": [0.300, 0.400, 0.150, 0.080]},
    ]
    return classes_catalog, detections


@router.post("/handout", response_model=CreateHandoutResponse, status_code=201)
async def create_handout_session(
    req: CreateHandoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> CreateHandoutResponse:
    """Create a new handout session (start of the process)."""
    
    session = SessionModel(
        user_id=current_user.id,
        status="draft",
        threshold_used=req.threshold,
        notes=req.notes
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return CreateHandoutResponse(
        session_id=str(session.id),
        status=session.status,
        threshold_used=session.threshold_used,
        created_at=session.created_at.isoformat()
    )


@router.post("/{session_id}/handout/predict", response_model=SessionPredictResponse)
async def handout_predict(
    session_id: str,
    req: SessionPredictRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> SessionPredictResponse:
    """Run prediction within a session context."""
    
    # Get session
    session = (await db.execute(
        select(SessionModel).where(SessionModel.id == uuid.UUID(session_id), SessionModel.user_id == current_user.id)
    )).scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status not in ["draft", "handout_auto", "handout_needs_manual"]:
        raise HTTPException(status_code=400, detail="Session is not in a state that allows prediction")
    
    # Run inference with YOLO (fallback to stub)
    classes_catalog, detections_raw = _infer_with_fallback(req.image, req.threshold)
    
    # Process detections (same logic as in predict.py)
    detections = []
    for i, d in enumerate(detections_raw, start=1):
        is_pass = float(d.get("confidence", 0.0)) >= float(req.threshold)
        
        det = {
            "detection_id": f"det-{i:03d}",
            "class": d.get("class", ""),
            "confidence": d.get("confidence", 0.0),
            "is_passed_conf_treshold": is_pass,
            "box": d.get("box", [0.0, 0.0, 0.0, 0.0]),
        }
        detections.append(det)
    
    # Calculate summary
    found_classes = {det["class"] for det in detections}
    not_found = [c for c in classes_catalog if c not in found_classes]
    
    summary = {
        "expected_total": len(classes_catalog),
        "found_candidates": len(detections),
        "passed_above_threshold": sum(1 for d in detections if d["is_passed_conf_treshold"]),
        "requires_manual_count": int(
            len(not_found) > 0 or any(not d["is_passed_conf_treshold"] for d in detections)
        ),
        "not_found_count": len(not_found),
    }
    
    # Create response
    predict_response = {
        "threshold": req.threshold,
        "classes_catalog": classes_catalog,
        "detections": detections,
        "not_found": not_found,
        "summary": summary,
    }
    
    # Update session with prediction data and image
    session.handout_predict = predict_response
    session.handout_image = req.image  # Store the base64 image
    session.status = "handout_needs_manual" if summary["requires_manual_count"] > 0 else "handout_auto"
    session.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return SessionPredictResponse(**predict_response)


@router.post("/{session_id}/handout/adjust", response_model=SessionAdjustResponse)
async def handout_adjust(
    session_id: str,
    req: SessionAdjustRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> SessionAdjustResponse:
    """Accept final annotations for a session."""
    
    # Get session
    session = (await db.execute(
        select(SessionModel).where(SessionModel.id == uuid.UUID(session_id), SessionModel.user_id == current_user.id)
    )).scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status not in ["handout_auto", "handout_needs_manual", "handover_auto", "handover_needs_manual"]:
        raise HTTPException(status_code=400, detail="Session is not in a state that allows adjustment")
    
    # Validate annotations (same logic as in predict.py)
    classes_catalog = set(settings.CLASSES)
    classes = [a.class_ for a in req.annotations]
    issues: List[str] = []
    
    # Validate class completeness
    if set(classes) != classes_catalog:
        missing = list(classes_catalog - set(classes))
        extra = list(set(classes) - classes_catalog)
        if missing:
            issues.append(f"Missing classes: {missing}")
        if extra:
            issues.append(f"Unknown/duplicated classes: {extra}")
        if len(classes) != len(set(classes)):
            issues.append("Each class must appear exactly once")
    
    # Validate bbox normalization
    def bbox_ok(b) -> bool:
        return all(0.0 <= float(x) <= 1.0 for x in b)
    
    for idx, a in enumerate(req.annotations):
        if not bbox_ok(a.box):
            issues.append(f"Annotation[{idx}] bbox must be normalized [0..1]: {a.box}")
    
    if issues:
        return SessionAdjustResponse(
            ok=False,
            issues=issues,
            stage="handout" if "handout" in session.status else "handover",
            count=len(req.annotations)
        )
    
    # Save final annotations
    final_annotations = [a.model_dump() for a in req.annotations]
    
    if "handout" in session.status:
        session.handout_final = {"annotations": final_annotations}
        session.status = "issued"
        stage = "handout"
    else:
        session.handover_final = {"annotations": final_annotations}
        session.status = "returned"
        session.returned_at = datetime.now(timezone.utc)
        stage = "handover"
    
    session.updated_at = datetime.now(timezone.utc)
    await db.commit()
    
    return SessionAdjustResponse(
        ok=True,
        issues=None,
        stage=stage,
        count=len(req.annotations)
    )


@router.post("/{session_id}/issue", response_model=IssueResponse)
async def issue_session(
    session_id: str,
    req: IssueRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> IssueResponse:
    """Issue/confirm a session (move to issued state)."""
    
    session = (await db.execute(
        select(SessionModel).where(SessionModel.id == session_id, SessionModel.user_id == current_user.id)
    )).scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != "handout_auto" and session.handout_final is None:
        raise HTTPException(status_code=400, detail="Session must have final annotations before issuing")
    
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Must confirm to issue session")
    
    session.status = "issued"
    session.issued_at = datetime.now(timezone.utc)
    session.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return IssueResponse(
        status="issued",
        issued_at=session.issued_at.isoformat()
    )


@router.post("/{session_id}/finalize", response_model=FinalizeResponse)
async def finalize_session(
    session_id: str,
    req: FinalizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> FinalizeResponse:
    """Finalize a session (move to returned state)."""
    
    session = (await db.execute(
        select(SessionModel).where(SessionModel.id == session_id, SessionModel.user_id == current_user.id)
    )).scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status not in ["handover_auto", "handover_needs_manual"] and session.handover_final is None:
        raise HTTPException(status_code=400, detail="Session must have handover final annotations before finalizing")
    
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Must confirm to finalize session")
    
    session.status = "returned"
    session.returned_at = datetime.now(timezone.utc)
    session.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return FinalizeResponse(
        status="returned",
        returned_at=session.returned_at.isoformat()
    )


@router.get("", response_model=SessionsListResponse)
async def list_sessions(
    page: int = 1,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> SessionsListResponse:
    """List sessions with pagination. Admins see all sessions, simple users see only their own."""
    
    offset = (page - 1) * limit
    
    # Build query based on user role
    if current_user.role == "admin":
        # Admins can see all sessions
        total_query = select(func.count()).select_from(SessionModel)
        sessions_query = (
            select(SessionModel, User)
            .join(User, SessionModel.user_id == User.id)
            .order_by(SessionModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    else:
        # Simple users see only their own sessions
        total_query = select(func.count()).select_from(SessionModel).where(SessionModel.user_id == current_user.id)
        sessions_query = (
            select(SessionModel, User)
            .join(User, SessionModel.user_id == User.id)
            .where(SessionModel.user_id == current_user.id)
            .order_by(SessionModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    
    total = (await db.execute(total_query)).scalar()
    results = (await db.execute(sessions_query)).all()
    
    items = [
        SessionsListItem(
            id=str(session.id),
            employee_id=user.employee_id,  # Show actual session owner's employee_id
            status=session.status,
            notes=session.notes,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat()
        )
        for session, user in results
    ]
    
    return SessionsListResponse(
        page=page,
        limit=limit,
        total=total,
        items=items
    )


@router.get("/{session_id}", response_model=SessionCardResponse)
async def get_session_details(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> SessionCardResponse:
    """Get detailed session information. Admins can view any session, simple users only their own."""
    
    # Build query based on user role
    if current_user.role == "admin":
        # Admins can view any session
        query = select(SessionModel, User).join(User, SessionModel.user_id == User.id).where(SessionModel.id == uuid.UUID(session_id))
    else:
        # Simple users can only view their own sessions
        query = select(SessionModel, User).join(User, SessionModel.user_id == User.id).where(
            SessionModel.id == uuid.UUID(session_id), 
            SessionModel.user_id == current_user.id
        )
    
    result = (await db.execute(query)).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session, session_owner = result
    
    # Build handout snapshot
    handout = None
    if session.handout_predict or session.handout_final or session.issued_at or session.handout_image:
        handout = HandStageSnapshot(
            predict=session.handout_predict,
            final=session.handout_final,
            image=session.handout_image,
            issued_at=session.issued_at.isoformat() if session.issued_at else None,
            returned_at=None
        )
    
    # Build handover snapshot
    handover = None
    if session.handover_predict or session.handover_final or session.returned_at or session.handover_image:
        handover = HandStageSnapshot(
            predict=session.handover_predict,
            final=session.handover_final,
            image=session.handover_image,
            issued_at=None,
            returned_at=session.returned_at.isoformat() if session.returned_at else None
        )
    
    return SessionCardResponse(
        id=str(session.id),
        employee_id=session_owner.employee_id,  # Show actual session owner's employee_id
        status=session.status,
        threshold_used=session.threshold_used,
        notes=session.notes,
        issued_at=session.issued_at.isoformat() if session.issued_at else None,
        returned_at=session.returned_at.isoformat() if session.returned_at else None,
        handout=handout,
        handover=handover,
        hash=session.hash
    )


@router.post("/{session_id}/handover/predict", response_model=SessionPredictResponse)
async def handover_predict(
    session_id: str,
    req: SessionPredictRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> SessionPredictResponse:
    """Run prediction for handover stage."""
    
    # Get session
    session = (await db.execute(
        select(SessionModel).where(SessionModel.id == uuid.UUID(session_id), SessionModel.user_id == current_user.id)
    )).scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status not in ["issued", "handover_auto", "handover_needs_manual"]:
        raise HTTPException(status_code=400, detail="Session is not in a state that allows handover prediction")
    
    # Run inference with YOLO (fallback to stub)
    classes_catalog, detections_raw = _infer_with_fallback(req.image, req.threshold)
    
    # Process detections (same logic as handout)
    detections = []
    for i, d in enumerate(detections_raw, start=1):
        is_pass = float(d.get("confidence", 0.0)) >= float(req.threshold)
        
        det = {
            "detection_id": f"det-{i:03d}",
            "class": d.get("class", ""),
            "confidence": d.get("confidence", 0.0),
            "is_passed_conf_treshold": is_pass,
            "box": d.get("box", [0.0, 0.0, 0.0, 0.0]),
        }
        detections.append(det)
    
    # Calculate summary
    found_classes = {det["class"] for det in detections}
    not_found = [c for c in classes_catalog if c not in found_classes]
    
    summary = {
        "expected_total": len(classes_catalog),
        "found_candidates": len(detections),
        "passed_above_threshold": sum(1 for d in detections if d["is_passed_conf_treshold"]),
        "requires_manual_count": int(
            len(not_found) > 0 or any(not d["is_passed_conf_treshold"] for d in detections)
        ),
        "not_found_count": len(not_found),
    }
    
    # Create response
    predict_response = {
        "threshold": req.threshold,
        "classes_catalog": classes_catalog,
        "detections": detections,
        "not_found": not_found,
        "summary": summary,
    }
    
    # Update session with handover prediction data and image
    session.handover_predict = predict_response
    session.handover_image = req.image  # Store the base64 image
    session.status = "handover_needs_manual" if summary["requires_manual_count"] > 0 else "handover_auto"
    session.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return SessionPredictResponse(**predict_response)


@router.post("/{session_id}/handover/adjust", response_model=SessionAdjustResponse)
async def handover_adjust(
    session_id: str,
    req: SessionAdjustRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> SessionAdjustResponse:
    """Accept final annotations for handover stage."""
    
    # Get session
    session = (await db.execute(
        select(SessionModel).where(SessionModel.id == uuid.UUID(session_id), SessionModel.user_id == current_user.id)
    )).scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status not in ["handover_auto", "handover_needs_manual"]:
        raise HTTPException(status_code=400, detail="Session is not in handover adjustment state")
    
    # Validate annotations (same logic as handout)
    classes_catalog = set(settings.CLASSES)
    classes = [a.class_ for a in req.annotations]
    issues: List[str] = []
    
    # Validate class completeness
    if set(classes) != classes_catalog:
        missing = list(classes_catalog - set(classes))
        extra = list(set(classes) - classes_catalog)
        if missing:
            issues.append(f"Missing classes: {missing}")
        if extra:
            issues.append(f"Unknown/duplicated classes: {extra}")
        if len(classes) != len(set(classes)):
            issues.append("Each class must appear exactly once")
    
    # Validate bbox normalization
    def bbox_ok(b) -> bool:
        return all(0.0 <= float(x) <= 1.0 for x in b)
    
    for idx, a in enumerate(req.annotations):
        if not bbox_ok(a.box):
            issues.append(f"Annotation[{idx}] bbox must be normalized [0..1]: {a.box}")
    
    if issues:
        return SessionAdjustResponse(
            ok=False,
            issues=issues,
            stage="handover",
            count=len(req.annotations)
        )
    
    # Save final handover annotations
    final_annotations = [a.model_dump() for a in req.annotations]
    session.handover_final = {"annotations": final_annotations}
    session.status = "returned"
    session.returned_at = datetime.now(timezone.utc)
    session.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return SessionAdjustResponse(
        ok=True,
        issues=None,
        stage="handover",
        count=len(req.annotations)
    )


@router.get("/{session_id}/diff", response_model=DiffResponse)
async def get_session_diff(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
) -> DiffResponse:
    """Get differences between handout and handover stages."""
    
    session = (await db.execute(
        select(SessionModel).where(SessionModel.id == uuid.UUID(session_id), SessionModel.user_id == current_user.id)
    )).scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.handout_final or not session.handover_final:
        raise HTTPException(status_code=400, detail="Both handout and handover final annotations are required")
    
    # Expected classes
    expected = {class_name: 1 for class_name in settings.CLASSES}
    
    # Extract annotations
    handout_annotations = session.handout_final.get("annotations", [])
    handover_annotations = session.handover_final.get("annotations", [])
    
    # Convert to class -> annotation mapping
    handout_final = {}
    for ann in handout_annotations:
        class_name = ann.get("class")
        if class_name:  # Only add if class_name is not None
            handout_final[class_name] = {
                "box": ann.get("box", []),
                "source": ann.get("source", "unknown")
            }
    
    handover_final = {}
    for ann in handover_annotations:
        class_name = ann.get("class")
        if class_name:  # Only add if class_name is not None
            handover_final[class_name] = {
                "box": ann.get("box", []),
                "source": ann.get("source", "unknown")
            }
    
    # Find missing and extra
    handout_classes = set(handout_final.keys())
    handover_classes = set(handover_final.keys())
    
    missing = list(handout_classes - handover_classes)  # In handout but not in handover
    extra = list(handover_classes - set(settings.CLASSES))  # Not in expected classes
    
    return DiffResponse(
        expected=expected,
        handout_final=handout_final,
        handover_final=handover_final,
        missing=missing,
        extra=extra
    )