#!/usr/bin/env python3
"""生成可跑通框架的示例标定，不能用于现场精度验收。"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "config/calib/cam01"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    K = np.array([[1000.0, 0.0, 960.0], [0.0, 1000.0, 540.0], [0.0, 0.0, 1.0]])
    dist = np.zeros(5)
    np.savez(OUT / "camera.npz", K=K, dist=dist)
    np.savez(
        OUT / "extrinsics.npz",
        R=np.eye(3),
        t=np.array([0.0, 0.0, 8.0]),
        height_m=np.array(8.0),
    )
    H = np.array(
        [
            [12.0 / 1920.0, 0.0, -6.0],
            [0.0, -20.0 / 1080.0, 21.0],
            [0.0, 0.0, 1.0],
        ]
    )
    np.savez(OUT / "homography.npz", H=H)
    rails = {
        "rails": [
            {"id": "left", "p0": [0.0, 0.0], "p1": [0.0, 200.0]},
            {"id": "right", "p0": [1.435, 0.0], "p1": [1.435, 200.0]},
        ]
    }
    (OUT / "rails.yaml").write_text(yaml.safe_dump(rails, allow_unicode=True), encoding="utf-8")
    meta = {
        "width": 1920,
        "height": 1080,
        "undistorted": True,
        "date": "2026-09-20",
        "vendor": "sample-not-for-production",
        "camera_serial": "cam01-sample",
        "error": {"distance_m": None, "height_m": None},
    }
    (OUT / "meta.yaml").write_text(yaml.safe_dump(meta, allow_unicode=True), encoding="utf-8")
    print(f"wrote sample calib under {OUT}")


if __name__ == "__main__":
    main()
