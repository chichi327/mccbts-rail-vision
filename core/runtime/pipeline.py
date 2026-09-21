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
from core.runtime.timing import timing_enabled, timing_log_every_n
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
    bufs = {
        cam_id: SharedFrameBuffer(**kwargs) for cam_id, kwargs in frame_buf_args.items()
    }
    for cam in cameras:
        store.load_camera(cam["id"], cam["calib_dir"])
    trackers = {
        cam["id"]: IoUTracker(prefix=f"{cam['id']}-{pipeline_id}") for cam in cameras
    }
    eventer = Eventer(
        warning_m=float(system.get("warning_distance_m", 2.0)),
        danger_m=float(system.get("danger_distance_m", 1.0)),
    )
    drop_age = int(system.get("drop_if_frame_age_ms", 200))
    max_e2e = int(system.get("max_e2e_ms", 300))
    do_timing = timing_enabled(system)
    every_n = timing_log_every_n(system)
    timed_frames = 0
    dropped = 0
    last_seq = {cam["id"]: -1 for cam in cameras}
    logged_invalid_calib: set[str] = set()
    log.info(
        "pipeline start id=%s steps=%s timing=%s every_n=%s",
        pipeline_id,
        step_names,
        do_timing,
        every_n if do_timing else 0,
    )
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
                t0 = time.perf_counter() if do_timing else 0.0
                detect_ms = track_ms = estimate_ms = 0.0
                for step in steps:
                    if isinstance(step, BaseDetector):
                        t_step = time.perf_counter() if do_timing else 0.0
                        detections = step.infer(packet.frame_bgr, packet.camera_id)
                        if do_timing:
                            detect_ms += (time.perf_counter() - t_step) * 1000
                            t_step = time.perf_counter()
                        detections = trackers[packet.camera_id].update(detections)
                        if do_timing:
                            track_ms += (time.perf_counter() - t_step) * 1000
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
                        t_step = time.perf_counter() if do_timing else 0.0
                        detections = step.estimate(
                            packet.frame_bgr, packet.camera_id, detections, calib
                        )
                        if do_timing:
                            estimate_ms += (time.perf_counter() - t_step) * 1000
                det_boxes[cam_id].publish(detections)
                events = eventer.feed(
                    packet.camera_id, packet.capture_ts_ms, detections
                )
                if do_timing:
                    timed_frames += 1
                    if timed_frames % every_n == 0:
                        total_ms = (time.perf_counter() - t0) * 1000
                        e2e_ms = now_ms() - ts_ms
                        line = (
                            "timing camera=%s pipeline=%s age_ms=%s detect_ms=%.1f "
                            "track_ms=%.1f estimate_ms=%.1f total_ms=%.1f e2e_ms=%s"
                        )
                        args = (
                            cam_id,
                            pipeline_id,
                            age,
                            detect_ms,
                            track_ms,
                            estimate_ms,
                            total_ms,
                            e2e_ms,
                        )
                        if e2e_ms > max_e2e:
                            log.warning(line + " over_max_e2e=%s", *args, max_e2e)
                        else:
                            log.info(line, *args)
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
