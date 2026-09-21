from __future__ import annotations

import logging
from pathlib import Path
from typing import cast

import numpy as np

from core.base.detector import BaseDetector
from core.base.types import Detection, ObjectType

log = logging.getLogger(__name__)

_ALLOWED: frozenset[str] = frozenset({"person", "car", "truck"})


class PersonVehicleDetector(BaseDetector):
    """YOLO 人车检测。当前配置只开 person，接流水线；车类稍后加 class_names。"""

    def load(self, config: dict) -> None:
        self.config = config
        self.model = None
        self.conf = float(config.get("conf_threshold", 0.5))
        raw = config.get("class_names") or {0: "person"}
        self.class_names = {int(k): str(v) for k, v in raw.items()}
        self.class_ids = [
            i for i, name in self.class_names.items() if name in _ALLOWED
        ]
        path = Path(str(config.get("model_path", "")))
        if not self.class_ids:
            log.warning("person_vehicle_detect: no allowed class_names")
            return
        if not path.is_file():
            log.warning("person_vehicle_detect: model not found path=%s", path)
            return
        from ultralytics import YOLO

        self.model = YOLO(str(path))
        log.info(
            "person_vehicle_detect: loaded %s classes=%s conf=%s",
            path,
            self.class_ids,
            self.conf,
        )

    def infer(self, frame_bgr: np.ndarray, camera_id: str) -> list[Detection]:
        if self.model is None:
            return []
        results = self.model(
            frame_bgr,
            classes=self.class_ids,
            verbose=False,
            conf=self.conf,
        )
        boxes = results[0].boxes
        if boxes is None:
            return []
        out: list[Detection] = []
        for box in boxes:
            cls_id = int(box.cls[0])
            name = self.class_names.get(cls_id)
            if name not in _ALLOWED:
                continue
            conf = float(box.conf[0])
            x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].tolist())
            out.append(
                Detection(
                    type=cast(ObjectType, name),
                    confidence=conf,
                    bbox_xyxy=[x1, y1, x2, y2],
                )
            )
        return out

    def release(self) -> None:
        self.model = None
