from __future__ import annotations

from typing import Any

from core.base.types import Detection
from core.ingest.mailbox import LatestFrameMailbox
from core.ingest.shm_frame import SharedFrameBuffer


def snapshot_live(
    buffers: dict[str, SharedFrameBuffer],
    det_boxes: dict[str, dict[str, LatestFrameMailbox]],
    det_cache: dict[tuple[str, str], list[Detection]],
    camera_id: str,
) -> tuple[Any, list[Detection]]:
    buf = buffers.get(camera_id)
    if buf is None:
        return None, []
    frame, _ts, seq = buf.read_copy()
    if frame is None or seq <= 0:
        return None, []
    for pipe_id, per_cam in det_boxes.items():
        box = per_cam.get(camera_id)
        if box is None:
            continue
        got = box.take_nowait()
        if got is not None:
            det_cache[(camera_id, pipe_id)] = got
    merged: list[Detection] = []
    for pipe_id in det_boxes:
        merged.extend(det_cache.get((camera_id, pipe_id)) or [])
    return frame, merged
