from __future__ import annotations

import numpy as np

from core.base.detector import BaseDetector
from core.base.types import Detection


class ObstacleDetector(BaseDetector):
    def infer(self, frame_bgr: np.ndarray, camera_id: str) -> list[Detection]:
        h, w = frame_bgr.shape[:2]
        x1, x2 = int(w * 0.55), int(w * 0.62)
        y1, y2 = int(h * 0.62), int(h * 0.78)
        return [
            Detection(
                type="obstacle",
                confidence=0.8,
                bbox_xyxy=[float(x1), float(y1), float(x2), float(y2)],
            )
        ]
