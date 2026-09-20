from __future__ import annotations

import numpy as np

from core.base.detector import BaseDetector
from core.base.types import Detection


class PersonVehicleDetector(BaseDetector):
    """骨架：固定位置假框，便于联调测距与事件。替换为 YOLO 时只改本文件。"""

    def infer(self, frame_bgr: np.ndarray, camera_id: str) -> list[Detection]:
        h, w = frame_bgr.shape[:2]
        # 底边中心约 u=704,v=0.83h，配合示例标定约 1.6m
        x1 = int(w * 0.32)
        x2 = int(w * 0.41)
        y1 = int(h * 0.55)
        y2 = int(h * 0.83)
        return [
            Detection(
                type="person",
                confidence=0.9,
                bbox_xyxy=[float(x1), float(y1), float(x2), float(y2)],
            )
        ]
