from __future__ import annotations

import logging
import time

from core.calib.store import CalibStore
from core.ingest.shm_frame import SharedFrameBuffer
from core.ingest.sources import open_source
from core.ingest.undistort import undistort_bgr
from core.logger import setup_logging

log = logging.getLogger(__name__)


def run_ingest(
    cam: dict,
    frame_buf: SharedFrameBuffer,
    calib_dir: str,
    stop_event,
    log_level: str = "INFO",
    timing_on: bool = False,
    timing_every_n: int = 30,
) -> None:
    setup_logging(log_level)
    store = CalibStore()
    view = store.load_camera(cam["id"], calib_dir)
    src = open_source(cam)
    every_n = max(1, int(timing_every_n))
    timed_frames = 0
    log.info(
        "ingest start camera=%s source=%s calib_valid=%s timing=%s",
        cam["id"],
        cam.get("source"),
        view.valid,
        timing_on,
    )
    try:
        while not stop_event.is_set():
            t0 = time.perf_counter() if timing_on else 0.0
            packet = src.read()
            if packet is None:
                time.sleep(0.001)
                continue
            t_read = time.perf_counter() if timing_on else 0.0
            packet.frame_bgr = undistort_bgr(packet.frame_bgr, view)
            packet.undistorted = view.valid
            t_undist = time.perf_counter() if timing_on else 0.0
            frame_buf.write(packet.frame_bgr, packet.capture_ts_ms)
            if timing_on:
                timed_frames += 1
                if timed_frames % every_n == 0:
                    log.info(
                        "timing ingest camera=%s read_ms=%.1f undistort_ms=%.1f write_ms=%.1f",
                        cam["id"],
                        (t_read - t0) * 1000,
                        (t_undist - t_read) * 1000,
                        (time.perf_counter() - t_undist) * 1000,
                    )
    finally:
        src.release()
        log.info("ingest stop camera=%s", cam["id"])
