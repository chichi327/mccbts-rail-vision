#!/usr/bin/env python3
"""单路单帧调试：不启动完整多进程。"""
from __future__ import annotations

import argparse

from core.calib.store import CalibStore
from core.ingest.sources import open_source
from core.ingest.undistort import undistort_bgr
from core.runtime.config import load_app_config
from core.runtime.loader import load_pipeline_steps
from core.track.iou_tracker import IoUTracker
from core.base.detector import BaseDetector
from core.base.estimator import BaseEstimator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-dir", default="config")
    parser.add_argument("--camera-id", default="cam01")
    parser.add_argument("--pipeline", default="person_vehicle")
    args = parser.parse_args()
    cfg = load_app_config(args.config_dir)
    cam = next(c for c in cfg.cameras if c["id"] == args.camera_id)
    pipe = next(p for p in cfg.pipelines if p["id"] == args.pipeline)
    steps = load_pipeline_steps(pipe["steps"], cfg.algorithms)
    store = CalibStore()
    view = store.load_camera(cam["id"], cam["calib_dir"])
    src = open_source(cam)
    packet = None
    for _ in range(50):
        packet = src.read()
        if packet is not None:
            break
    src.release()
    if packet is None:
        raise SystemExit("no frame")
    packet.frame_bgr = undistort_bgr(packet.frame_bgr, view)
    dets = []
    tracker = IoUTracker(prefix=f"{cam['id']}-{args.pipeline}")
    for step in steps:
        if isinstance(step, BaseDetector):
            dets = step.infer(packet.frame_bgr, cam["id"])
            dets = tracker.update(dets)
        elif isinstance(step, BaseEstimator) and view.valid:
            dets = step.estimate(packet.frame_bgr, cam["id"], dets, view)
    for d in dets:
        print(d)
    for step in steps:
        step.release()


if __name__ == "__main__":
    main()
