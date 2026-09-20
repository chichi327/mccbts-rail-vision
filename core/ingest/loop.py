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
) -> None:
    setup_logging(log_level)
    store = CalibStore()
    view = store.load_camera(cam["id"], calib_dir)
    src = open_source(cam)
    log.info("ingest start camera=%s source=%s calib_valid=%s", cam["id"], cam.get("source"), view.valid)
    try:
        while not stop_event.is_set():
            packet = src.read()
            if packet is None:
                time.sleep(0.001)
                continue
            packet.frame_bgr = undistort_bgr(packet.frame_bgr, view)
            packet.undistorted = view.valid
            frame_buf.write(packet.frame_bgr, packet.capture_ts_ms)
    finally:
        src.release()
        log.info("ingest stop camera=%s", cam["id"])
