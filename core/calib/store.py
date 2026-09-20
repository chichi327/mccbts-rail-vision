from __future__ import annotations

from pathlib import Path

from core.base.types import CalibStatus
from core.calib.view import CalibView, FileCalibView, InvalidCalibView

REQUIRED = ("camera.npz", "extrinsics.npz", "homography.npz", "rails.yaml", "meta.yaml")


class CalibStore:
    def __init__(self) -> None:
        self._views: dict[str, CalibView] = {}
        self._status: dict[str, CalibStatus] = {}

    def load_camera(self, camera_id: str, calib_dir: str | Path) -> CalibView:
        path = Path(calib_dir)
        missing = [name for name in REQUIRED if not (path / name).exists()]
        if missing:
            view: CalibView = InvalidCalibView(f"missing {missing}")
            self._views[camera_id] = view
            self._status[camera_id] = "invalid"
            return view
        try:
            view = FileCalibView(path)
            if not view.valid:
                self._views[camera_id] = InvalidCalibView("meta.undistorted is not true")
                self._status[camera_id] = "invalid"
                return self._views[camera_id]
            self._views[camera_id] = view
            self._status[camera_id] = "ok"
            return view
        except Exception as exc:  # noqa: BLE001 — 启动时标定失败应降级而非崩溃
            view = InvalidCalibView(str(exc))
            self._views[camera_id] = view
            self._status[camera_id] = "invalid"
            return view

    def view(self, camera_id: str) -> CalibView:
        if camera_id not in self._views:
            return InvalidCalibView(f"no calib for {camera_id}")
        return self._views[camera_id]

    def status(self, camera_id: str) -> CalibStatus:
        return self._status.get(camera_id, "invalid")

    def reason(self, camera_id: str) -> str:
        view = self._views.get(camera_id)
        if isinstance(view, InvalidCalibView):
            return view.reason
        if camera_id not in self._views:
            return f"no calib for {camera_id}"
        return ""
