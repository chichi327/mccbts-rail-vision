from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np
import yaml


class CalibView(ABC):
    @property
    @abstractmethod
    def valid(self) -> bool: ...

    @abstractmethod
    def undistort_map_size(self) -> tuple[int, int]: ...

    @abstractmethod
    def pixel_to_ground(self, u: float, v: float) -> tuple[float, float]: ...

    @abstractmethod
    def ground_distance_to_nearest_rail(self, x: float, y: float) -> float: ...

    def bbox_foot_to_rail_distance(self, bbox_xyxy: list[float]) -> float:
        x1, _y1, x2, y2 = bbox_xyxy
        u = (x1 + x2) / 2.0
        v = y2
        gx, gy = self.pixel_to_ground(u, v)
        return self.ground_distance_to_nearest_rail(gx, gy)

    @abstractmethod
    def bbox_to_height_m(self, bbox_xyxy: list[float]) -> float: ...


class InvalidCalibView(CalibView):
    def __init__(self, reason: str):
        self.reason = reason

    @property
    def valid(self) -> bool:
        return False

    def undistort_map_size(self) -> tuple[int, int]:
        return (0, 0)

    def pixel_to_ground(self, u: float, v: float) -> tuple[float, float]:
        raise RuntimeError(f"calib invalid: {self.reason}")

    def ground_distance_to_nearest_rail(self, x: float, y: float) -> float:
        raise RuntimeError(f"calib invalid: {self.reason}")

    def bbox_to_height_m(self, bbox_xyxy: list[float]) -> float:
        raise RuntimeError(f"calib invalid: {self.reason}")


class FileCalibView(CalibView):
    def __init__(self, calib_dir: Path):
        self.dir = calib_dir
        cam = np.load(calib_dir / "camera.npz")
        ext = np.load(calib_dir / "extrinsics.npz")
        homo = np.load(calib_dir / "homography.npz")
        with open(calib_dir / "rails.yaml", encoding="utf-8") as f:
            rails = yaml.safe_load(f)
        with open(calib_dir / "meta.yaml", encoding="utf-8") as f:
            self.meta: dict[str, Any] = yaml.safe_load(f) or {}

        self.K = cam["K"].astype(np.float64)
        self.dist = cam["dist"].astype(np.float64)
        self.H = homo["H"].astype(np.float64)
        self.R = ext["R"].astype(np.float64) if "R" in ext.files else np.eye(3)
        self.t = ext["t"].astype(np.float64) if "t" in ext.files else np.zeros(3)
        self.camera_height_m = float(ext["height_m"]) if "height_m" in ext.files else float(np.linalg.norm(self.t))
        self.rails = rails
        self.width = int(self.meta.get("width", 1920))
        self.height = int(self.meta.get("height", 1080))

    @property
    def valid(self) -> bool:
        return bool(self.meta.get("undistorted", False))

    def undistort_map_size(self) -> tuple[int, int]:
        return self.width, self.height

    def pixel_to_ground(self, u: float, v: float) -> tuple[float, float]:
        vec = self.H @ np.array([u, v, 1.0], dtype=np.float64)
        if abs(vec[2]) < 1e-9:
            return (float("nan"), float("nan"))
        return float(vec[0] / vec[2]), float(vec[1] / vec[2])

    def ground_distance_to_nearest_rail(self, x: float, y: float) -> float:
        rails = self.rails.get("rails") or []
        best = float("inf")
        for rail in rails:
            best = min(best, _point_to_segment_dist(x, y, rail["p0"], rail["p1"]))
        return best

    def bbox_to_height_m(self, bbox_xyxy: list[float]) -> float:
        """单目粗估：底边脚点到地面，顶边反投影高度差。无外参时退回相机高度比例。"""
        x1, y1, x2, y2 = bbox_xyxy
        foot_u = (x1 + x2) / 2.0
        fy = float(self.K[1, 1]) if self.K.shape == (3, 3) else 1000.0
        box_h_px = max(y2 - y1, 1.0)
        if self.camera_height_m <= 0:
            return 0.0
        gx, gy = self.pixel_to_ground(foot_u, y2)
        ground_dist = float(np.hypot(gx, gy))
        if ground_dist < 0.1:
            ground_dist = 0.1
        return float(box_h_px / fy * ground_dist)


def _point_to_segment_dist(x: float, y: float, p0: list[float], p1: list[float]) -> float:
    ax, ay = p0
    bx, by = p1
    vx, vy = bx - ax, by - ay
    wx, wy = x - ax, y - ay
    denom = vx * vx + vy * vy
    if denom < 1e-12:
        return float(np.hypot(wx, wy))
    t = max(0.0, min(1.0, (wx * vx + wy * vy) / denom))
    px, py = ax + t * vx, ay + t * vy
    return float(np.hypot(x - px, y - py))
