from __future__ import annotations

import logging
import time
from multiprocessing import Queue
from queue import Empty
from typing import Any

from core.calib.store import CalibStore
from core.health.classify import build_heartbeat, log_health_transitions
from core.ingest.shm_frame import SharedFrameBuffer
from core.logger import setup_logging
from core.report.reporter import HTTPReporter

log = logging.getLogger(__name__)


def run_health(
    cameras: list[dict],
    event_queue: Queue,
    backend: dict,
    system: dict,
    stop_event,
    process_alive: Any,
    frame_buf_args: dict[str, dict[str, Any]],
    drop_counters: dict[str, Any],
    latest_payloads: Any,
) -> None:
    setup_logging(str(system.get("log_level", "INFO")))
    reporter = HTTPReporter(backend)
    store = CalibStore()
    bufs = {cam_id: SharedFrameBuffer(**kwargs) for cam_id, kwargs in frame_buf_args.items()}
    for cam in cameras:
        view = store.load_camera(cam["id"], cam["calib_dir"])
        log.info(
            "health loaded calib camera=%s valid=%s reason=%s",
            cam["id"],
            view.valid,
            store.reason(cam["id"]) or "-",
        )
    interval = float(system.get("heartbeat_interval_s", 5))
    offline_after_ms = int(system.get("camera_offline_after_ms", 3000))
    last = 0.0
    prev_issues: dict[str, list[str]] = {cam["id"]: [] for cam in cameras}
    try:
        while not stop_event.is_set():
            try:
                ev = event_queue.get(timeout=0.05)
                reporter.report_event(ev)
                reporter.drain_retry()
            except Empty:
                pass
            now = time.time()
            if now - last < interval:
                continue
            last = now
            ts_ms = int(now * 1000)
            dropped = 0
            for counter in drop_counters.values():
                dropped += int(counter.value)
            person_alive = bool(process_alive.get("person_vehicle", False))
            obstacle_alive = bool(process_alive.get("obstacle", False))
            for cam in cameras:
                cam_id = cam["id"]
                buf = bufs[cam_id]
                with buf.lock:
                    last_ts = int(buf.ts_ms.value)
                hb = build_heartbeat(
                    camera_id=cam_id,
                    ts_ms=ts_ms,
                    last_frame_ts_ms=last_ts,
                    offline_after_ms=offline_after_ms,
                    pipeline_person_alive=person_alive,
                    pipeline_obstacle_alive=obstacle_alive,
                    calib_status=store.status(cam_id),
                    dropped_stale_frames=dropped,
                    calib_reason=store.reason(cam_id),
                )
                log_health_transitions(cam_id, prev_issues[cam_id], hb.issues, hb)
                prev_issues[cam_id] = list(hb.issues)
                latest_payloads[cam_id] = hb.to_payload()
                reporter.report_heartbeat(hb)
    finally:
        for buf in bufs.values():
            buf.close(unlink=False)
        reporter.close()
