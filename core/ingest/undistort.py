from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from core.calib.view import CalibView, FileCalibView

log = logging.getLogger(__name__)

# (calib_dir, width, height) -> (map1, map2)
_maps: dict[tuple[str, int, int], tuple[np.ndarray, np.ndarray]] = {}


def clear_undistort_maps() -> None:
    _maps.clear()


def undistort_map_cache_size() -> int:
    return len(_maps)


def _maps_for(calib: FileCalibView, width: int, height: int) -> tuple[np.ndarray, np.ndarray]:
    import cv2

    key = (str(Path(calib.dir).resolve()), width, height)
    cached = _maps.get(key)
    if cached is not None:
        return cached
    new_k, _ = cv2.getOptimalNewCameraMatrix(calib.K, calib.dist, (width, height), 0)
    map1, map2 = cv2.initUndistortRectifyMap(
        calib.K,
        calib.dist,
        None,
        new_k,
        (width, height),
        cv2.CV_16SC2,
    )
    _maps[key] = (map1, map2)
    log.info("undistort maps ready dir=%s size=%sx%s", key[0], width, height)
    return map1, map2


def undistort_bgr(frame: np.ndarray, calib: CalibView) -> np.ndarray:
    """按相机缓存 remap 表；禁止每帧 cv2.undistort 重算映射。"""
    if not isinstance(calib, FileCalibView):
        return frame
    import cv2

    h, w = frame.shape[:2]
    map1, map2 = _maps_for(calib, w, h)
    return cv2.remap(frame, map1, map2, interpolation=cv2.INTER_LINEAR)
