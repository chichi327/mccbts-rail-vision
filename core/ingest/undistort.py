from __future__ import annotations

import numpy as np

from core.calib.view import CalibView, FileCalibView


def undistort_bgr(frame: np.ndarray, calib: CalibView) -> np.ndarray:
    if not isinstance(calib, FileCalibView):
        return frame
    import cv2

    h, w = frame.shape[:2]
    new_k, _ = cv2.getOptimalNewCameraMatrix(calib.K, calib.dist, (w, h), 0)
    return cv2.undistort(frame, calib.K, calib.dist, None, new_k)
