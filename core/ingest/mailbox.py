from __future__ import annotations

import multiprocessing as mp
from queue import Empty, Full
from typing import Optional

from core.ingest.packet import FramePacket


class LatestFrameMailbox:
    """深度 1 的邮箱：新帧覆盖旧帧，读端永远拿最新。跨进程 Queue 实现（骨架）。"""

    def __init__(self, ctx: mp.context.BaseContext | None = None):
        ctx = ctx or mp.get_context("spawn")
        self._q: mp.Queue = ctx.Queue(maxsize=1)

    def publish(self, packet: FramePacket) -> None:
        try:
            self._q.get_nowait()
        except Empty:
            pass
        try:
            self._q.put_nowait(packet)
        except Full:
            pass

    def take(self, timeout: float = 0.05) -> Optional[FramePacket]:
        try:
            return self._q.get(timeout=timeout)
        except Empty:
            return None
