from __future__ import annotations

import numpy as np

from core.base.estimator import BaseEstimator
from core.base.types import Detection
from core.calib.view import CalibView


class TrackDistanceEstimator(BaseEstimator):
    def estimate(
        self,
        frame_bgr: np.ndarray,
        camera_id: str,
        detections: list[Detection],
        calib: CalibView,
    ) -> list[Detection]:
        for det in detections:
            if det.type in ("person", "car", "truck"):
                det.distance_to_track_m = calib.bbox_foot_to_rail_distance(det.bbox_xyxy)
        return detections
