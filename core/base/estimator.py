from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np

from core.base.types import Detection

if TYPE_CHECKING:
    from core.calib.view import CalibView


class BaseEstimator(ABC):
    def load(self, config: dict) -> None:
        self.config = config

    @abstractmethod
    def estimate(
        self,
        frame_bgr: np.ndarray,
        camera_id: str,
        detections: list[Detection],
        calib: CalibView,
    ) -> list[Detection]:
        """补齐物理量，不得丢弃上游目标、不得另起主 bbox。"""

    def release(self) -> None:
        return None
