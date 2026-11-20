"""Model inference boundary.

The current implementation lives in ``weed_detector.py``. This module is a
stable seam for a trained segmentation model to be added in Milestone 3.
"""

from app.services.weed_detector import DetectionResult, WeedDetector

__all__ = ["DetectionResult", "WeedDetector"]
