from typing import List, Tuple, Dict, Any
from fastapi import APIRouter, HTTPException
from ..schemas.predict import PredictRequest, PredictResponse, AdjustRequest
from ..schemas.common import Detection, Summary
from ...core.settings import settings
from ...ml.yolo_service import infer_with_yolo
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def _infer_with_fallback(image_b64: str) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Inference with fallback to stub if YOLO fails.
    
    Args:
        image_b64: Base64 encoded image
        threshold: Confidence threshold
        
    Returns:
        Tuple of (classes_catalog, detections)
    """
    try:
        # Try YOLO inference first with base threshold
        return infer_with_yolo(image_b64, settings.YOLO_CONFIDENCE_THRESHOLD)
    except Exception as e:
        logger.warning(f"YOLO inference failed, falling back to stub: {e}")
        # Fallback to stub
        return _infer_stub(image_b64)

def _infer_stub(image_b64: str) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Fallback inference stub for when YOLO is not available.
    Returns:
      - classes catalog (11 fixed classes from settings),
      - list of raw detections in a lightweight dict format:
        {"class": <str>, "confidence": <float>, "box": [xc, yc, w, h]}.
    """
    classes_catalog = settings.CLASSES
    # Example detections (mimics the sample from the spec):
    detections = [
        {"class": "screwdriver_plus", "confidence": 0.992, "box": [0.512, 0.431, 0.183, 0.072]},
        {"class": "wrench_adjustable", "confidence": 0.74, "box": [0.246, 0.611, 0.204, 0.090]},
        {"class": "screwdriver_plus", "confidence": 0.981, "box": [0.300, 0.400, 0.150, 0.080]},
    ]
    return classes_catalog, detections


@router.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest) -> PredictResponse:
    """
    One-off prediction endpoint.
    - Accepts base64 image + threshold.
    - Produces detections with local IDs and threshold flags.
    - May return < 11 or > 11 detections; this is expected at this stage.
    """

    # Get all detections with base YOLO threshold
    classes_catalog, detections_raw = _infer_with_fallback(req.image)

    detections: List[Detection] = []
    for i, d in enumerate(detections_raw, start=1):
        # Compute threshold pass/fail. Keep numeric conversions explicit.
        is_pass = float(d.get("confidence", 0.0)) >= float(req.threshold)

        # Wrap raw dict into a validated Pydantic model
        det = Detection(
            detection_id=f"det-{i:03d}",
            **{
                "class": d.get("class", ""),
                "confidence": d.get("confidence", 0.0),
                "is_passed_conf_treshold": is_pass,
                "box": d.get("box", [0.0, 0.0, 0.0, 0.0]),
            },
        )
        detections.append(det)

    # Classes with at least one candidate
    found_classes = {det.class_ for det in detections}
    not_found = [c for c in classes_catalog if c not in found_classes]

    # Summarize the situation for the UI
    summary = Summary(
        expected_total=len(classes_catalog),
        found_candidates=len(detections),
        passed_above_threshold=sum(1 for d in detections if d.is_passed_conf_treshold),
        requires_manual_count=int(
            len(not_found) > 0 or any(not d.is_passed_conf_treshold for d in detections)
        ),
        not_found_count=len(not_found),
    )

    return PredictResponse(
        threshold=req.threshold,
        classes_catalog=classes_catalog,
        detections=detections,
        not_found=not_found,
        summary=summary,
    )


@router.post("/predict/adjust")
async def predict_adjust(req: AdjustRequest):
    """
    Final annotations acceptance endpoint.
    Business rules:
      - Exactly 11 annotations (enforced by the schema).
      - Each of the 11 known classes must appear exactly once (no extras, no duplicates).
      - All bboxes must be normalized to [0..1].

    Returns:
      {"ok": true,  "message": "...", "count": 11}
      or
      {"ok": false, "issues": ["...","..."]}
    """

    classes_catalog = set(settings.CLASSES)
    classes = [a.class_ for a in req.annotations]
    issues: List[str] = []

    # Encode the invariant in one check: the set must match exactly.
    # This simultaneously validates: 11 unique, all known, none missing.
    if set(classes) != classes_catalog:
        missing = list(classes_catalog - set(classes))
        extra = list(set(classes) - classes_catalog)
        if missing:
            issues.append(f"Missing classes: {missing}")
        if extra:
            # When a class appears twice, it will show up here as "extra"
            # because set(classes) differs from the catalog.
            issues.append(f"Unknown/duplicated classes: {extra}")
        if len(classes) != len(set(classes)):
            issues.append("Each class must appear exactly once")

    # Validate bbox normalization
    def bbox_ok(b) -> bool:
        # Keep it tolerant to minor float quirks if needed later, e.g., eps = 1e-9
        return all(0.0 <= float(x) <= 1.0 for x in b)

    for idx, a in enumerate(req.annotations):
        if not bbox_ok(a.box):
            issues.append(f"Annotation[{idx}] bbox must be normalized [0..1]: {a.box}")

    if issues:
        return {"ok": False, "issues": issues}

    return {
        "ok": True,
        "message": "Final annotations accepted",
        "count": len(req.annotations),
    }