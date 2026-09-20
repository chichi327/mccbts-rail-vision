from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class FramePacket:
    camera_id: str
    capture_ts_ms: int
    frame_bgr: np.ndarray
    undistorted: bool
