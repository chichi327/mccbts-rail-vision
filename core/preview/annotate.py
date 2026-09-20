from __future__ import annotations

import cv2
import numpy as np

from core.base.types import Detection

_COLORS = {
    "person": (0, 220, 0),
    "car": (255, 180, 0),
    "truck": (255, 180, 0),
    "obstacle": (0, 165, 255),
}


def annotate_frame(frame_bgr: np.ndarray, detections: list[Detection]) -> np.ndarray:
    out = frame_bgr.copy()
    for det in detections:
        x1, y1, x2, y2 = [int(v) for v in det.bbox_xyxy]
        color = _COLORS.get(det.type, (0, 255, 0))
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        parts = [det.type]
        if det.distance_to_track_m is not None:
            parts.append(f"{det.distance_to_track_m:.2f}m")
        if det.height_m is not None:
            parts.append(f"h={det.height_m:.2f}m")
        cv2.putText(out, " ".join(parts), (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.putText(out, "preview (not in 300ms path)", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    return out
