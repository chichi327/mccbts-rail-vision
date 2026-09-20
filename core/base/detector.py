from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from core.base.types import Detection


class BaseDetector(ABC):
    def load(self, config: dict) -> None:
        self.config = config

    @abstractmethod
    def infer(self, frame_bgr: np.ndarray, camera_id: str) -> list[Detection]:
        """输入已去畸变 BGR 帧，只返回框与类别。"""

    def release(self) -> None:
        return None
