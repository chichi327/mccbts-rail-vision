from pathlib import Path

import numpy as np
import yaml

from core.calib.store import CalibStore
from core.calib.view import FileCalibView


def _write_sample(dirpath: Path) -> None:
    dirpath.mkdir(parents=True)
    np.savez(dirpath / "camera.npz", K=np.eye(3), dist=np.zeros(5))
    np.savez(dirpath / "extrinsics.npz", R=np.eye(3), t=np.array([0.0, 0.0, 8.0]), height_m=np.array(8.0))
    H = np.array([[12 / 1920, 0, -6], [0, -20 / 1080, 21], [0, 0, 1]], dtype=float)
    np.savez(dirpath / "homography.npz", H=H)
    rails = {"rails": [{"p0": [0.0, 0.0], "p1": [0.0, 200.0]}, {"p0": [1.435, 0.0], "p1": [1.435, 200.0]}]}
    (dirpath / "rails.yaml").write_text(yaml.safe_dump(rails), encoding="utf-8")
    (dirpath / "meta.yaml").write_text(yaml.safe_dump({"undistorted": True, "width": 1920, "height": 1080}), encoding="utf-8")


def test_missing_files_invalid(tmp_path: Path):
    store = CalibStore()
    view = store.load_camera("c1", tmp_path / "empty")
    assert not view.valid
    assert store.status("c1") == "invalid"


def test_foot_distance(tmp_path: Path):
    calib_dir = tmp_path / "cam"
    _write_sample(calib_dir)
    view = FileCalibView(calib_dir)
    # u=960 -> x=0 落在左轨
    dist = view.bbox_foot_to_rail_distance([910, 800, 1010, 1080])
    assert dist < 0.2
