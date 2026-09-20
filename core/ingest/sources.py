from __future__ import annotations

from abc import ABC, abstractmethod
from time import time

import numpy as np

from core.ingest.packet import FramePacket


class FrameSource(ABC):
    @abstractmethod
    def read(self) -> FramePacket | None: ...

    @abstractmethod
    def release(self) -> None: ...


class SyntheticSource(FrameSource):
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
        # 一条浅色「轨」便于预览
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
    """低缓冲 OpenCV 拉流。生产 GPU NVDEC 可替换本类，接口保持 read()。"""

    def __init__(self, camera_id: str, url: str, width: int, height: int):
        import cv2

        self.camera_id = camera_id
        self.cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.width = width
        self.height = height

    def read(self) -> FramePacket | None:
        import cv2

        ok, frame = self.cap.read()
        if not ok or frame is None:
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
        self.cap.release()


class OpenCVDeviceSource(FrameSource):
    """本机 USB / 内置摄像头，仅用于架构通路验证。"""

    def __init__(self, camera_id: str, device_index: int, width: int, height: int, fps: int = 10):
        import cv2

        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.interval = 1.0 / max(fps, 1)
        self._last = 0.0
        self.cap = cv2.VideoCapture(device_index)
        if not self.cap.isOpened():
            raise RuntimeError(
                f"打不开摄像头 device_index={device_index}。"
                "macOS 请在系统设置 → 隐私与安全 → 相机 允许终端/IDE。"
            )
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def read(self) -> FramePacket | None:
        import cv2

        if not self.cap.grab():
            return None
        now = time()
        if now - self._last < self.interval:
            return None
        ok, frame = self.cap.retrieve()
        if not ok or frame is None:
            return None
        self._last = now
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height))
        return FramePacket(
            camera_id=self.camera_id,
            capture_ts_ms=int(time() * 1000),
            frame_bgr=frame,
            undistorted=False,
        )

    def release(self) -> None:
        self.cap.release()


def open_source(cam: dict) -> FrameSource:
    source = cam.get("source", "synthetic")
    if source == "rtsp":
        return OpenCVRTSPSource(cam["id"], cam["rtsp_main"], cam["width"], cam["height"])
    if source == "webcam":
        return OpenCVDeviceSource(
            cam["id"],
            int(cam.get("device_index", 0)),
            cam["width"],
            cam["height"],
            int(cam.get("target_fps", 10)),
        )
    return SyntheticSource(cam["id"], cam["width"], cam["height"], int(cam.get("target_fps", 10)))
