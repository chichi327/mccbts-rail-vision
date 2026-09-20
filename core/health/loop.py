from __future__ import annotations

import logging
import time
from multiprocessing import Queue

from queue import Empty

from core.base.types import Heartbeat
from core.calib.store import CalibStore
from core.report.reporter import HTTPReporter

log = logging.getLogger(__name__)


def run_health(
    cameras: list[dict],
    event_queue: Queue,
    backend: dict,
    system: dict,
    stop_event,
    process_alive: dict,
) -> None:
    reporter = HTTPReporter(backend)
    store = CalibStore()
    for cam in cameras:
        store.load_camera(cam["id"], cam["calib_dir"])
    interval = float(system.get("heartbeat_interval_s", 5))
    last = 0.0
    try:
        while not stop_event.is_set():
            try:
                ev = event_queue.get(timeout=0.05)
                reporter.report_event(ev)
                reporter.drain_retry()
            except Empty:
                pass
            now = time.time()
            if now - last >= interval:
                last = now
                for cam in cameras:
                    hb = Heartbeat(
                        camera_id=cam["id"],
                        ts_ms=int(now * 1000),
                        camera_online=True,
                        pipeline_person_alive=bool(process_alive.get("person_vehicle", True)),
                        pipeline_obstacle_alive=bool(process_alive.get("obstacle", True)),
                        calib_status=store.status(cam["id"]),
                        last_frame_age_ms=0,
                        dropped_stale_frames=0,
                    )
                    reporter.report_heartbeat(hb)
    finally:
        reporter.close()
