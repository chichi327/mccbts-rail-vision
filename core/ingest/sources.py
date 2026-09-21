from __future__ import annotations

import logging
import os
import threading
from abc import ABC, abstractmethod
from time import time

import numpy as np

from core.ingest.packet import FramePacket

log = logging.getLogger(__name__)

# 必须在 import cv2 之前生效。max_delay 500ms 会把转动画面拖成「卡住」。
FFMPEG_CAPTURE_OPTIONS = (
    "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay|"
    "max_delay;0|probesize;32|analyzeduration;0"
)
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = FFMPEG_CAPTURE_OPTIONS


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


class OpenCVRTSPSource(FrameSource):
    """唯一真实视频入口：拉 MediaMTX（本机 8554）。连续失败则重建连接。

    FFmpeg/OpenCV 会在内部排队。后台只把最新一帧放进槽里，ingest 不再按队列顺序播。
    """

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
        self._lock = threading.Lock()
        self._latest: np.ndarray | None = None
        self._seq = 0
        self._emitted_seq = -1
        self._reader_stop = threading.Event()
        self._reader: threading.Thread | None = None
        self._open()

    def _stop_reader(self) -> None:
        self._reader_stop.set()
        cap = self.cap
        if cap is not None:
            cap.release()
            self.cap = None
        if self._reader is not None:
            self._reader.join(timeout=2.0)
            self._reader = None

    def _open(self) -> None:
        import cv2

        self._stop_reader()
        self._reader_stop.clear()
        self.cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self._fail = 0
            self._retries = 0
            with self._lock:
                self._latest = None
                self._seq = 0
                self._emitted_seq = -1
            self._reader = threading.Thread(
                target=self._pump,
                name=f"rtsp-pump-{self.camera_id}",
                daemon=True,
            )
            self._reader.start()
            log.info("rtsp opened camera=%s %s", self.camera_id, redact_rtsp(self.url))
        else:
            log.warning("rtsp open failed camera=%s %s", self.camera_id, redact_rtsp(self.url))

    def _pump(self) -> None:
        while not self._reader_stop.is_set():
            cap = self.cap
            if cap is None:
                break
            ok, frame = cap.read()
            if not ok or frame is None:
                with self._lock:
                    self._fail += 1
                if not self._reader_stop.wait(0.02):
                    continue
                break
            with self._lock:
                self._latest = frame
                self._seq += 1
                self._fail = 0

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
        with self._lock:
            if self._fail >= self.fail_before_reconnect:
                need_reconnect = True
                frame = None
            elif self._latest is None or self._seq == self._emitted_seq:
                return None
            else:
                need_reconnect = False
                self._emitted_seq = self._seq
                frame = self._latest.copy()
        if need_reconnect:
            self._reconnect()
            return None
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height))
        return FramePacket(
            camera_id=self.camera_id,
            capture_ts_ms=int(time() * 1000),
            frame_bgr=frame,
            undistorted=False,
        )

    def release(self) -> None:
        self._stop_reader()


def open_source(cam: dict) -> FrameSource:
    source = cam.get("source", "rtsp")
    if source != "rtsp":
        raise ValueError(
            f"camera {cam.get('id')} 只支持 source=rtsp（本机 MediaMTX），不支持 {source!r}"
        )
    url = cam.get("rtsp_main") or cam.get("rtsp_camera")
    if not url:
        raise ValueError(f"camera {cam.get('id')} missing rtsp_main")
    return OpenCVRTSPSource(cam["id"], url, cam["width"], cam["height"])
