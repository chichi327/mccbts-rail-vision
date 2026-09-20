from __future__ import annotations

import argparse
import logging
import multiprocessing as mp
import signal
import threading
import time

from core.health.loop import run_health
from core.health.server import serve_health
from core.ingest.loop import run_ingest
from core.ingest.mailbox import LatestFrameMailbox
from core.logger import setup_logging
from core.runtime.config import load_app_config
from core.runtime.pipeline import run_pipeline
from services.health_check import health_snapshot
from services.preview_server import start_preview_thread

log = logging.getLogger("main")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="mccbts-rail-vision")
    p.add_argument("--config-dir", default="config")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_app_config(args.config_dir)
    setup_logging(str(cfg.system.get("log_level", "INFO")))
    ctx = mp.get_context("spawn")
    stop = ctx.Event()

    def _stop(*_):
        stop.set()

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    mailboxes = {cam["id"]: LatestFrameMailbox(ctx) for cam in cfg.cameras}
    event_queue = ctx.Queue(maxsize=256)
    procs: list[mp.Process] = []

    for cam in cfg.cameras:
        proc = ctx.Process(
            name=f"ingest-{cam['id']}",
            target=run_ingest,
            args=(cam, mailboxes[cam["id"]], cam["calib_dir"], stop),
        )
        procs.append(proc)
    for pipe in cfg.pipelines:
        proc = ctx.Process(
            name=f"pipe-{pipe['id']}",
            target=run_pipeline,
            args=(
                pipe["id"],
                pipe["steps"],
                cfg.algorithms,
                cfg.cameras,
                mailboxes,
                event_queue,
                cfg.system,
                stop,
            ),
        )
        procs.append(proc)

    health_proc = ctx.Process(
        name="report-health",
        target=run_health,
        args=(cfg.cameras, event_queue, cfg.backend, cfg.system, stop, {"person_vehicle": True, "obstacle": True}),
    )
    procs.append(health_proc)

    for proc in procs:
        proc.start()

    health_cfg = cfg.system.get("health") or {}
    threading.Thread(
        target=serve_health,
        args=(
            health_cfg.get("host", "127.0.0.1"),
            int(health_cfg.get("port", 8080)),
            lambda: health_snapshot({"cameras": [c["id"] for c in cfg.cameras]}),
            stop,
        ),
        daemon=True,
        name="health-http",
    ).start()
    start_preview_thread(bool((cfg.system.get("preview") or {}).get("enabled")))

    log.info("started processes=%s", [p.name for p in procs])
    try:
        while not stop.is_set():
            dead = [p.name for p in procs if not p.is_alive()]
            if dead:
                log.error("process exited: %s", dead)
                stop.set()
                break
            time.sleep(0.3)
    finally:
        stop.set()
        for proc in procs:
            proc.join(timeout=3)
            if proc.is_alive():
                proc.terminate()
        log.info("shutdown complete")


if __name__ == "__main__":
    main()
