from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from time import time

import numpy as np

from core.ingest.packet import FramePacket

log = logging.getLogger(__name__)

os.environ.setdefault(
    "OPENCV_FFMPEG_CAPTURE_OPTIONS",
    "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay|max_delay;500000",
)


def redact_rtsp(url: str) -> str:
    if "://" not in url or "@" not in url:
        return url
    scheme, rest = url.split("://", 1)
    _creds, host = rest.split("@", 1)
    return f"{scheme}://***@{host}"


class FrameSource(ABC):
    @abstractmethod
    def read(self) -> FramePacket | None: ...

    @abstractmethod
    def release(self) -> None: ...


class SyntheticSource(FrameSource):
    """无硬件单测用，不是第二种摄像头接入。"""

    def __init__(self, camera_id: str, width: int, height: int, fps: int):
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.interval = 1.0 / max(fps, 1)
        self._last = 0.0

    def read(self) -> FramePacket | None:
        now = time()
        if now - self._last < self.interval:
            return None
        self._last = now
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = (40, 40, 40)
        y = int(self.height * 0.75)
        frame[y : y + 4, :, :] = (180, 180, 180)
        return FramePacket(
            camera_id=self.camera_id,
            capture_ts_ms=int(now * 1000),
            frame_bgr=frame,
            undistorted=False,
        )

    def release(self) -> None:
        return None


class OpenCVRTSPSource(FrameSource):
    """唯一真实视频入口：拉 MediaMTX（本机 8554）。连续失败则重建连接。"""

    def __init__(self, camera_id: str, url: str, width: int, height: int, fail_before_reconnect: int = 8):
        self.camera_id = camera_id
        self.url = url
        self.width = width
        self.height = height
        self.fail_before_reconnect = fail_before_reconnect
        self.cap = None
        self._fail = 0
        self._retries = 0
        self._last_try = 0.0
        self._open()

    def _open(self) -> None:
        import cv2

        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self._fail = 0
            self._retries = 0
            log.info("rtsp opened camera=%s %s", self.camera_id, redact_rtsp(self.url))
        else:
            log.warning("rtsp open failed camera=%s %s", self.camera_id, redact_rtsp(self.url))

    def _reconnect(self) -> None:
        now = time()
        wait = min(8.0, 0.5 * (2 ** min(self._retries, 4)))
        if now - self._last_try < wait:
            return
        self._last_try = now
        self._retries += 1
        log.warning(
            "rtsp reconnect camera=%s attempt=%s next_min_interval=%.1fs",
            self.camera_id,
            self._retries,
            wait,
        )
        self._open()

    def read(self) -> FramePacket | None:
        import cv2

        if self.cap is None or not self.cap.isOpened():
            self._reconnect()
            return None
        ok, frame = self.cap.read()
        if not ok or frame is None:
            self._fail += 1
            if self._fail >= self.fail_before_reconnect:
                self._reconnect()
            return None
        self._fail = 0
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height))
        return FramePacket(
            camera_id=self.camera_id,
            capture_ts_ms=int(time() * 1000),
            frame_bgr=frame,
            undistorted=False,
        )

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None


def open_source(cam: dict) -> FrameSource:
    source = cam.get("source", "rtsp")
    if source == "webcam":
        raise ValueError(
            "已取消 source=webcam。本机 USB 请 bash scripts/start.sh --webcam "
            "（FFmpeg → MediaMTX → ingest 只拉 rtsp://127.0.0.1:8554/...），与现场同一条链路。"
        )
    if source == "synthetic":
        return SyntheticSource(
            cam["id"], cam["width"], cam["height"], int(cam.get("target_fps", 10))
        )
    url = cam.get("rtsp_main") or cam.get("rtsp_camera")
    if not url:
        raise ValueError(f"camera {cam.get('id')} missing rtsp_main")
    return OpenCVRTSPSource(cam["id"], url, cam["width"], cam["height"])
