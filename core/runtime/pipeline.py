from __future__ import annotations

import logging
import time
from multiprocessing import Queue
from typing import Any

from core.base.detector import BaseDetector
from core.base.estimator import BaseEstimator
from core.base.types import Detection
from core.calib.store import CalibStore
from core.event.eventer import Eventer
from core.ingest.mailbox import LatestFrameMailbox
from core.runtime.loader import load_pipeline_steps
from core.track.iou_tracker import IoUTracker

log = logging.getLogger(__name__)


def now_ms() -> int:
    return int(time.time() * 1000)


def run_pipeline(
    pipeline_id: str,
    step_names: list[str],
    algorithms: dict[str, Any],
    cameras: list[dict[str, Any]],
    mailboxes: dict[str, LatestFrameMailbox],
    event_queue: Queue,
    system: dict[str, Any],
    stop_event,
) -> None:
    steps = load_pipeline_steps(step_names, algorithms)
    store = CalibStore()
    for cam in cameras:
        store.load_camera(cam["id"], cam["calib_dir"])
    trackers = {cam["id"]: IoUTracker(prefix=f"{cam['id']}-{pipeline_id}") for cam in cameras}
    eventer = Eventer(
        warning_m=float(system.get("warning_distance_m", 2.0)),
        danger_m=float(system.get("danger_distance_m", 1.0)),
    )
    drop_age = int(system.get("drop_if_frame_age_ms", 200))
    dropped = 0
    log.info("pipeline start id=%s steps=%s", pipeline_id, step_names)
    try:
        while not stop_event.is_set():
            for cam in cameras:
                packet = mailboxes[cam["id"]].take(timeout=0.02)
                if packet is None:
                    continue
                age = now_ms() - packet.capture_ts_ms
                if age > drop_age:
                    dropped += 1
                    continue
                detections: list[Detection] = []
                calib = store.view(packet.camera_id)
                for step in steps:
                    if isinstance(step, BaseDetector):
                        detections = step.infer(packet.frame_bgr, packet.camera_id)
                        detections = trackers[packet.camera_id].update(detections)
                    elif isinstance(step, BaseEstimator):
                        if not calib.valid:
                            continue
                        detections = step.estimate(
                            packet.frame_bgr, packet.camera_id, detections, calib
                        )
                events = eventer.feed(packet.camera_id, packet.capture_ts_ms, detections)
                for ev in events:
                    try:
                        event_queue.put_nowait(ev)
                    except Exception:
                        log.warning("event queue full, drop event %s", ev.event_type)
    finally:
        for step in steps:
            step.release()
        log.info("pipeline stop id=%s dropped_stale=%s", pipeline_id, dropped)
