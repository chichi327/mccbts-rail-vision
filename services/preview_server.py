from __future__ import annotations

import logging
import threading
from typing import Any

from core.preview.server import serve_preview

log = logging.getLogger(__name__)


def start_preview_thread(
    enabled: bool,
    host: str,
    port: int,
    camera_ids: list[str],
    buffers: Any,
    det_boxes: Any,
    stop_event,
    max_width: int = 960,
    jpeg_quality: int = 60,
) -> None:
    if not enabled:
        log.info("preview disabled")
        return
    log.info("preview http://%s:%s/preview", host, port)
    threading.Thread(
        target=serve_preview,
        args=(host, port, camera_ids, buffers, det_boxes, stop_event, max_width, jpeg_quality),
        daemon=True,
        name="preview-http",
    ).start()
