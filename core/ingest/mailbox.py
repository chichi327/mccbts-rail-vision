from __future__ import annotations

import multiprocessing as mp
from queue import Empty, Full
from typing import Any, Optional


class LatestFrameMailbox:
    """深度 1 的邮箱：新对象覆盖旧对象。小结果用 Queue；整帧走 SharedFrameBuffer。"""

    def __init__(self, ctx: mp.context.BaseContext | None = None):
        ctx = ctx or mp.get_context("spawn")
        self._q: mp.Queue = ctx.Queue(maxsize=1)

    def publish(self, packet: Any) -> None:
        try:
            self._q.get_nowait()
        except Empty:
            pass
        try:
            self._q.put_nowait(packet)
        except Full:
            pass

    def take(self, timeout: float = 0.05) -> Optional[Any]:
        try:
            return self._q.get(timeout=timeout)
        except Empty:
            return None

    def take_nowait(self) -> Optional[Any]:
        try:
            return self._q.get_nowait()
        except Empty:
            return None
