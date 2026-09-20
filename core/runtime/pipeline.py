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
from core.ingest.packet import FramePacket
from core.ingest.shm_frame import SharedFrameBuffer
from core.logger import setup_logging
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
    frame_buf_args: dict[str, dict[str, Any]],
    det_boxes: dict[str, LatestFrameMailbox],
    event_queue: Queue,
    system: dict[str, Any],
    stop_event,
    drop_counter=None,
) -> None:
    setup_logging(str(system.get("log_level", "INFO")))
    steps = load_pipeline_steps(step_names, algorithms)
    store = CalibStore()
    bufs = {cam_id: SharedFrameBuffer(**kwargs) for cam_id, kwargs in frame_buf_args.items()}
    for cam in cameras:
        store.load_camera(cam["id"], cam["calib_dir"])
    trackers = {cam["id"]: IoUTracker(prefix=f"{cam['id']}-{pipeline_id}") for cam in cameras}
    eventer = Eventer(
        warning_m=float(system.get("warning_distance_m", 2.0)),
        danger_m=float(system.get("danger_distance_m", 1.0)),
    )
    drop_age = int(system.get("drop_if_frame_age_ms", 200))
    dropped = 0
    last_seq = {cam["id"]: -1 for cam in cameras}
    logged_invalid_calib: set[str] = set()
    log.info("pipeline start id=%s steps=%s", pipeline_id, step_names)
    try:
        while not stop_event.is_set():
            progressed = False
            for cam in cameras:
                cam_id = cam["id"]
                frame, ts_ms, seq = bufs[cam_id].read_copy()
                if frame is None or seq == last_seq[cam_id]:
                    continue
                last_seq[cam_id] = seq
                progressed = True
                age = now_ms() - ts_ms
                if age > drop_age:
                    dropped += 1
                    if drop_counter is not None:
                        drop_counter.value = dropped
                    log.debug(
                        "drop stale frame camera=%s pipeline=%s age_ms=%s count=%s",
                        cam_id,
                        pipeline_id,
                        age,
                        dropped,
                    )
                    continue
                packet = FramePacket(
                    camera_id=cam_id,
                    capture_ts_ms=ts_ms,
                    frame_bgr=frame,
                    undistorted=True,
                )
                detections: list[Detection] = []
                calib = store.view(packet.camera_id)
                for step in steps:
                    if isinstance(step, BaseDetector):
                        detections = step.infer(packet.frame_bgr, packet.camera_id)
                        detections = trackers[packet.camera_id].update(detections)
                    elif isinstance(step, BaseEstimator):
                        if not calib.valid:
                            if cam_id not in logged_invalid_calib:
                                reason = getattr(calib, "reason", "invalid")
                                log.warning(
                                    "HEALTH_FAULT camera=%s issue=calib_invalid pipeline=%s reason=%s",
                                    cam_id,
                                    pipeline_id,
                                    reason,
                                )
                                logged_invalid_calib.add(cam_id)
                            continue
                        detections = step.estimate(
                            packet.frame_bgr, packet.camera_id, detections, calib
                        )
                det_boxes[cam_id].publish(detections)
                events = eventer.feed(packet.camera_id, packet.capture_ts_ms, detections)
                for ev in events:
                    log.info(
                        "event camera=%s type=%s dist=%s height=%s",
                        ev.camera_id,
                        ev.event_type,
                        ev.object.distance_to_track_m,
                        ev.object.height_m,
                    )
                    try:
                        event_queue.put_nowait(ev)
                    except Exception:
                        log.warning("event queue full, drop event %s", ev.event_type)
            if not progressed:
                time.sleep(0.002)
    finally:
        for buf in bufs.values():
            buf.close(unlink=False)
        for step in steps:
            step.release()
        log.info("pipeline stop id=%s dropped_stale=%s", pipeline_id, dropped)
