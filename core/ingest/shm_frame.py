from __future__ import annotations

from multiprocessing.shared_memory import SharedMemory

import numpy as np


class SharedFrameBuffer:
    """跨进程最新帧：共享内存 memcpy，避免把整幅 numpy pickle 进 Queue。"""

    def __init__(
        self,
        width: int,
        height: int,
        *,
        ctx=None,
        shm_name: str | None = None,
        lock=None,
        ts_ms=None,
        seq=None,
    ):
        self.width = int(width)
        self.height = int(height)
        self.nbytes = self.width * self.height * 3
        self._created = shm_name is None
        if self._created:
            if ctx is None:
                raise ValueError("create SharedFrameBuffer requires multiprocessing context")
            self.shm = SharedMemory(create=True, size=self.nbytes)
            self.lock = ctx.Lock()
            self.ts_ms = ctx.Value("q", 0)
            self.seq = ctx.Value("q", 0)
        else:
            self.shm = SharedMemory(name=shm_name)
            self.lock = lock
            self.ts_ms = ts_ms
            self.seq = seq
        self._view = np.ndarray((self.height, self.width, 3), dtype=np.uint8, buffer=self.shm.buf)

    def attach_kwargs(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "shm_name": self.shm.name,
            "lock": self.lock,
            "ts_ms": self.ts_ms,
            "seq": self.seq,
        }

    def write(self, frame_bgr: np.ndarray, ts_ms: int) -> None:
        if frame_bgr.shape[0] != self.height or frame_bgr.shape[1] != self.width:
            import cv2

            frame_bgr = cv2.resize(frame_bgr, (self.width, self.height))
        with self.lock:
            np.copyto(self._view, frame_bgr)
            self.ts_ms.value = int(ts_ms)
            self.seq.value += 1

    def read_copy(self) -> tuple[np.ndarray | None, int, int]:
        with self.lock:
            seq = int(self.seq.value)
            if seq <= 0:
                return None, 0, 0
            return self._view.copy(), int(self.ts_ms.value), seq

    def close(self, unlink: bool | None = None) -> None:
        self.shm.close()
        if unlink is None:
            unlink = self._created
        if unlink:
            try:
                self.shm.unlink()
            except FileNotFoundError:
                pass
