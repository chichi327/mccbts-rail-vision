from __future__ import annotations

import logging
import threading

log = logging.getLogger(__name__)


def start_preview_thread(enabled: bool) -> None:
    if not enabled:
        return
    log.info("preview placeholder enabled (MediaMTX overlay not wired in skeleton)")
    threading.Thread(target=lambda: None, daemon=True).start()
