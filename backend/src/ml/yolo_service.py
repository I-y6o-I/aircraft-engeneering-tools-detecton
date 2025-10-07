import base64
import io
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from PIL import Image

# Try to import OpenCV and YOLO, fallback if not available
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"OpenCV not available: {e}")
    CV2_AVAILABLE = False

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"YOLO not available: {e}")
    YOLO_AVAILABLE = False

from ..core.settings import settings

logger = logging.getLogger(__name__)

class YOLOInferenceService:
    """Service for running YOLO v11 inference on tool detection."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize YOLO service.
        
        Args:
            model_path: Path to the .pt model file. If None, uses default path.
        """

        self.model = None
        self.model_path = model_path or self._get_default_model_path()
        self.classes_catalog = settings.CLASSES
        
        # Check if required libraries are available
        if not CV2_AVAILABLE:
            raise RuntimeError("OpenCV is not available. Cannot initialize YOLO service.")
        if not YOLO_AVAILABLE:
            raise RuntimeError("YOLO (ultralytics) is not available. Cannot initialize YOLO service.")
            
        self._load_model()
    
    def _get_default_model_path(self) -> str:
        """Get default model path."""

        # Look for .pt files in models directory
        models_dir = Path(__file__).parent.parent.parent / "models"
        pt_files = list(models_dir.glob("*.pt"))
        
        if not pt_files:
            raise FileNotFoundError(
                f"No .pt model files found in {models_dir}. "
                "Please place your YOLO v11 model file there."
            )
        
        if len(pt_files) > 1:
            logger.warning(f"Multiple .pt files found: {pt_files}. Using the first one: {pt_files[0]}")
        
        return str(pt_files[0])
    
    def _load_model(self):
        """Load YOLO model from file."""

        try:
            logger.info(f"Loading YOLO model from: {self.model_path}")
            self.model = YOLO(self.model_path)
            logger.info(f"Model loaded successfully. Classes: {self.model.names}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise RuntimeError(f"Could not load YOLO model from {self.model_path}: {e}")
    
    def _base64_to_image(self, image_b64: str) -> np.ndarray:
        """Convert base64 string to OpenCV image array."""

        try:
            # Remove data URL prefix if present
            if ',' in image_b64:
                image_b64 = image_b64.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_b64)
            
            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Convert to OpenCV format (BGR) if OpenCV is available
            if CV2_AVAILABLE:
                cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                return cv_image
            else:
                # Fallback: return RGB numpy array
                return np.array(pil_image)
            
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {e}")
            raise ValueError(f"Invalid base64 image data: {e}")
    
    def _map_class_names(self, yolo_class_id: int) -> Optional[str]:
        """
        Map YOLO class ID to our standard class names.
        
        Args:
            yolo_class_id: Class ID from YOLO model
            
        Returns:
            Mapped class name or None if not found
        """

        # Get class name from YOLO model
        yolo_class_name = self.model.names.get(yolo_class_id)
        
        if not yolo_class_name:
            return None
        
        # Map YOLO class names to our standard names
        # Based on your model's actual class names
        # class_mapping = {
        #     # Your YOLO model classes -> Our standard classes
        #     '1_screw_driver_minus': 'screwdriver_minus',
        #     '2_screw_driver_plus': 'screwdriver_plus', 
        #     '3_screw_driver_cross': 'offset_cross',  # Cross screwdriver maps to offset_cross
        #     '4_brace': 'brace',
        #     '5_contouring_pliers': 'nippers',  # Contouring pliers maps to nippers
        #     '6_pliers': 'pliers',
        #     '7_slip_joint_pilers': 'lock_pliers',  # Slip joint pliers maps to lock_pliers
        #     '8_wrench': 'wrench_adjustable',  # Wrench maps to adjustable wrench
        #     '9_can_opener': 'oil_can_opener',  # Can opener maps to oil can opener
        #     '10_spanner': 'ring_wrench_3_4',  # Spanner maps to ring wrench
        #     '11_side_cutters': 'shernitsa',  # Side cutters maps to shernitsa
        # }

        # class_mapping = {
        #     # Your YOLO model classes -> Our standard classes
        #     '1_screw_driver_minus': 'screwdriver_minus',
        #     '2_screw_driver_plus': 'offset_cross',
        #     '3_screw_driver_cross': 'screwdriver_plus',  # Cross screwdriver maps to offset_cross ---
        #     '4_brace': 'brace',
        #     '5_contouring_pliers': 'ring_wrench_3_4', # Contouring pliers maps to nippers
        #     '6_pliers': 'nippers',
        #     '7_slip_joint_pilers': 'lock_pliers',  # Slip joint pliers maps to lock_pliers
        #     '8_wrench': 'ring_wrench_3_4',  # Wrench maps to adjustable wrench
        #     '9_can_opener': 'pliers',  # Can opener maps to oil can opener
        #     '10_spanner': 'oil_can_opener',  # Spanner maps to ring wrench
        #     '11_side_cutters': 'shernitsa',  # Side cutters maps to shernitsa
        # }

        class_mapping = {
            "1_screw_driver_minus": "screwdriver_minus",
            "2_screw_driver_plus": "screwdriver_plus",
            "3_screw_driver_cross": "offset_cross",
            "4_brace": "brace",
            "5_contouring_pliers": "lock_pliers",
            "6_pliers": "shernitsa",
            "7_slip_joint_pilers": "wrench_adjustable",
            "8_wrench": "oil_can_opener",
            "9_can_opener": "pliers",
            "10_spanner": "ring_wrench_3_4",
            "11_side_cutters": "nippers"
        }

        
        # Try exact match first
        if yolo_class_name in class_mapping:
            return class_mapping[yolo_class_name]
        
        # Try partial match (case insensitive)
        yolo_lower = yolo_class_name.lower()
        for yolo_name, standard_name in class_mapping.items():
            if yolo_lower in yolo_name.lower() or yolo_name.lower() in yolo_lower:
                return standard_name
        
        logger.warning(f"Unknown class name from YOLO: {yolo_class_name}")
        return None
    
    def _convert_bbox_format(self, bbox: List[float], img_width: int, img_height: int) -> List[float]:
        """
        Convert YOLO bbox format to normalized [x_center, y_center, width, height].
        
        Args:
            bbox: YOLO bbox in format [x1, y1, x2, y2] (absolute coordinates)
            img_width: Image width
            img_height: Image height
            
        Returns:
            Normalized bbox [x_center, y_center, width, height]
        """

        x1, y1, x2, y2 = bbox
        
        # Convert to center format
        x_center = (x1 + x2) / 2
        y_center = (y1 + y2) / 2
        width = x2 - x1
        height = y2 - y1
        
        # Normalize by image dimensions
        x_center_norm = x_center / img_width
        y_center_norm = y_center / img_height
        width_norm = width / img_width
        height_norm = height / img_height
        
        return [x_center_norm, y_center_norm, width_norm, height_norm]
    
    def infer(self, image_b64: str, confidence_threshold: float = 0.5) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Run inference on base64 encoded image.
        
        Args:
            image_b64: Base64 encoded image
            confidence_threshold: Minimum confidence threshold for detections
            
        Returns:
            Tuple of (classes_catalog, detections)
            - classes_catalog: List of all possible class names
            - detections: List of detection dictionaries with keys:
                - class: str
                - confidence: float
                - box: List[float] (normalized [x_center, y_center, width, height])
        """

        if not self.model:
            raise RuntimeError("YOLO model not loaded")
        
        try:
            # Convert base64 to image
            image = self._base64_to_image(image_b64)
            img_height, img_width = image.shape[:2]
            
            logger.info(f"Running inference on image of size: {img_width}x{img_height}")
            
            # Run YOLO inference
            results = self.model(image, conf=confidence_threshold, verbose=False)
            
            detections = []
            
            # Process results
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        # Get class ID and confidence
                        class_id = int(box.cls.item())
                        confidence = float(box.conf.item())
                        
                        # Map class name
                        class_name = self._map_class_names(class_id)
                        if not class_name:
                            continue  # Skip unknown classes
                        
                        # Get bbox coordinates (x1, y1, x2, y2)
                        bbox_xyxy = box.xyxy[0].tolist()
                        
                        # Convert to normalized center format
                        bbox_normalized = self._convert_bbox_format(bbox_xyxy, img_width, img_height)
                        
                        detection = {
                            "class": class_name,
                            "confidence": confidence,
                            "box": bbox_normalized
                        }
                        detections.append(detection)
            
            logger.info(f"Found {len(detections)} detections")
            return self.classes_catalog, detections
            
        except Exception as e:
            logger.error(f"Inference failed: {e}")
            raise RuntimeError(f"YOLO inference failed: {e}")


# Global service instance
_yolo_service: Optional[YOLOInferenceService] = None

def get_yolo_service() -> YOLOInferenceService:
    """Get or create global YOLO service instance."""

    global _yolo_service
    if _yolo_service is None:
        _yolo_service = YOLOInferenceService()
    return _yolo_service

def initialize_yolo_service() -> bool:
    """
    Initialize YOLO service at startup.
    
    Returns:
        True if initialization successful, False otherwise
    """

    try:
        logger.info("Initializing YOLO service at startup...")
        service = get_yolo_service()
        logger.info("YOLO service initialized successfully!")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize YOLO service: {e}")
        return False

def infer_with_yolo(image_b64: str, confidence_threshold: float = 0.5) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Convenience function for YOLO inference.
    
    Args:
        image_b64: Base64 encoded image
        confidence_threshold: Minimum confidence threshold
        
    Returns:
        Tuple of (classes_catalog, detections)
    """

    service = get_yolo_service()
    return service.infer(image_b64, confidence_threshold)