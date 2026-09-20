from __future__ import annotations

import numpy as np

from core.base.estimator import BaseEstimator
from core.base.types import Detection
from core.calib.view import CalibView


class ObstacleHeightEstimator(BaseEstimator):
    def estimate(
        self,
        frame_bgr: np.ndarray,
        camera_id: str,
        detections: list[Detection],
        calib: CalibView,
    ) -> list[Detection]:
        for det in detections:
            if det.type == "obstacle":
                det.height_m = calib.bbox_to_height_m(det.bbox_xyxy)
        return detections
