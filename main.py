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
from core.ingest.shm_frame import SharedFrameBuffer
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

    frame_bufs = {
        cam["id"]: SharedFrameBuffer(cam["width"], cam["height"], ctx=ctx) for cam in cfg.cameras
    }
    frame_buf_args = {cam_id: buf.attach_kwargs() for cam_id, buf in frame_bufs.items()}
    det_boxes = {
        pipe["id"]: {cam["id"]: LatestFrameMailbox(ctx) for cam in cfg.cameras} for pipe in cfg.pipelines
    }
    event_queue = ctx.Queue(maxsize=256)
    procs: list[mp.Process] = []

    log_level = str(cfg.system.get("log_level", "INFO"))
    manager = ctx.Manager()
    process_alive = manager.dict()
    latest_payloads = manager.dict()
    drop_counters = {pipe["id"]: ctx.Value("q", 0) for pipe in cfg.pipelines}
    for pipe in cfg.pipelines:
        process_alive[pipe["id"]] = True

    ingest_threads: list[threading.Thread] = []
    for cam in cfg.cameras:
        thread = threading.Thread(
            name=f"ingest-{cam['id']}",
            target=run_ingest,
            args=(cam, frame_bufs[cam["id"]], cam["calib_dir"], stop, log_level),
            daemon=True,
        )
        ingest_threads.append(thread)
        thread.start()
    pipe_procs: list[mp.Process] = []
    for pipe in cfg.pipelines:
        proc = ctx.Process(
            name=f"pipe-{pipe['id']}",
            target=run_pipeline,
            args=(
                pipe["id"],
                pipe["steps"],
                cfg.algorithms,
                cfg.cameras,
                frame_buf_args,
                det_boxes[pipe["id"]],
                event_queue,
                cfg.system,
                stop,
                drop_counters[pipe["id"]],
            ),
        )
        pipe_procs.append(proc)
        procs.append(proc)

    health_proc = ctx.Process(
        name="report-health",
        target=run_health,
        args=(
            cfg.cameras,
            event_queue,
            cfg.backend,
            cfg.system,
            stop,
            process_alive,
            frame_buf_args,
            drop_counters,
            latest_payloads,
        ),
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
            lambda: health_snapshot(
                latest_payloads,
                extra={"cameras": [c["id"] for c in cfg.cameras]},
            ),
            stop,
        ),
        daemon=True,
        name="health-http",
    ).start()
    preview_cfg = cfg.system.get("preview") or {}
    start_preview_thread(
        bool(preview_cfg.get("enabled", True)),
        str(preview_cfg.get("host", "127.0.0.1")),
        int(preview_cfg.get("port", 8081)),
        [c["id"] for c in cfg.cameras],
        frame_bufs,
        det_boxes,
        stop,
        int(preview_cfg.get("max_width", 960)),
        int(preview_cfg.get("jpeg_quality", 60)),
    )

    log.info("started ingest_threads=%s processes=%s", [t.name for t in ingest_threads], [p.name for p in procs])
    if preview_cfg.get("enabled", True):
        log.info("open preview http://127.0.0.1:%s/preview", int(preview_cfg.get("port", 8081)))
    try:
            logged_ingest_dead: set[str] = set()
            while not stop.is_set():
                if not health_proc.is_alive():
                    log.error("HEALTH_PROCESS_DEAD name=%s exitcode=%s", health_proc.name, health_proc.exitcode)
                    stop.set()
                    break
                for proc in pipe_procs:
                    pipe_id = proc.name.removeprefix("pipe-")
                    if proc.is_alive():
                        continue
                    if process_alive.get(pipe_id, False):
                        issue = (
                            "pipeline_person_dead"
                            if pipe_id == "person_vehicle"
                            else "pipeline_obstacle_dead"
                        )
                        log.error(
                            "HEALTH_FAULT camera=* issue=%s name=%s exitcode=%s",
                            issue,
                            proc.name,
                            proc.exitcode,
                        )
                        process_alive[pipe_id] = False
                for thread in ingest_threads:
                    if thread.is_alive() or thread.name in logged_ingest_dead:
                        continue
                    cam_id = thread.name.removeprefix("ingest-")
                    log.error("HEALTH_FAULT camera=%s issue=camera_offline ingest_thread_dead", cam_id)
                    logged_ingest_dead.add(thread.name)
                time.sleep(0.3)
    finally:
        stop.set()
        for proc in procs:
            proc.join(timeout=3)
            if proc.is_alive():
                proc.terminate()
        for buf in frame_bufs.values():
            buf.close(unlink=True)
        log.info("shutdown complete")


if __name__ == "__main__":
    main()
