#!/usr/bin/env python3
"""单路单帧调试：不启动完整多进程。可把带框抓拍存成 JPEG。"""
from __future__ import annotations

import argparse
from pathlib import Path
from time import sleep

import cv2

from core.base.detector import BaseDetector
from core.base.estimator import BaseEstimator
from core.base.types import Detection
from core.calib.store import CalibStore
from core.ingest.sources import open_source
from core.ingest.undistort import undistort_bgr
from core.preview.annotate import annotate_frame
from core.runtime.config import load_app_config
from core.runtime.loader import load_pipeline_steps
from core.track.iou_tracker import IoUTracker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-dir", default="config")
    parser.add_argument("--camera-id", default="cam01")
    parser.add_argument("--pipeline", default="person_vehicle")
    parser.add_argument("--save-jpeg", default="data/debug/last_frame.jpg")
    parser.add_argument("--tries", type=int, default=80, help="webcam 需要多读几帧预热")
    args = parser.parse_args()
    cfg = load_app_config(args.config_dir)
    cam = next(c for c in cfg.cameras if c["id"] == args.camera_id)
    pipe = next(p for p in cfg.pipelines if p["id"] == args.pipeline)
    steps = load_pipeline_steps(pipe["steps"], cfg.algorithms)
    store = CalibStore()
    view = store.load_camera(cam["id"], cam["calib_dir"])
    src = open_source(cam)
    packet = None
    for _ in range(args.tries):
        packet = src.read()
        if packet is not None:
            break
        sleep(0.03)
    src.release()
    if packet is None:
        raise SystemExit("读不到帧：检查 source=webcam/rtsp、权限、地址")
    packet.frame_bgr = undistort_bgr(packet.frame_bgr, view)
    dets: list[Detection] = []
    tracker = IoUTracker(prefix=f"{cam['id']}-{args.pipeline}")
    for step in steps:
        if isinstance(step, BaseDetector):
            dets = step.infer(packet.frame_bgr, cam["id"])
            dets = tracker.update(dets)
        elif isinstance(step, BaseEstimator) and view.valid:
            dets = step.estimate(packet.frame_bgr, cam["id"], dets, view)
    for d in dets:
        print(d)
    out_path = Path(args.save_jpeg)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    vis = annotate_frame(packet.frame_bgr, dets)
    cv2.imwrite(str(out_path), vis)
    print(f"saved {out_path}  source={cam.get('source')}  calib_valid={view.valid}")
    for step in steps:
        step.release()


if __name__ == "__main__":
    main()
