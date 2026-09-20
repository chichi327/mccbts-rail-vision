from __future__ import annotations

import time
import uuid
from typing import Optional

from core.base.types import AlertLevel, Detection, VisionEvent


def alert_level(distance_m: Optional[float], warning_m: float, danger_m: float) -> AlertLevel:
    if distance_m is None:
        return "none"
    if distance_m <= danger_m:
        return "danger"
    if distance_m <= warning_m:
        return "warning"
    return "none"


class Eventer:
    def __init__(self, warning_m: float = 2.0, danger_m: float = 1.0, obstacle_ttl_miss: int = 8):
        self.warning_m = warning_m
        self.danger_m = danger_m
        self.obstacle_ttl_miss = obstacle_ttl_miss
        self._person_state: dict[str, AlertLevel] = {}
        self._obstacles: dict[str, int] = {}

    def feed(self, camera_id: str, capture_ts_ms: int, detections: list[Detection]) -> list[VisionEvent]:
        events: list[VisionEvent] = []
        seen_obs: set[str] = set()
        now = int(time.time() * 1000)
        for det in detections:
            if det.type in ("person", "car", "truck"):
                level = alert_level(det.distance_to_track_m, self.warning_m, self.danger_m)
                prev = self._person_state.get(det.object_id, "none")
                if level != prev:
                    etype = _transition_event(det.type, prev, level)
                    if etype:
                        events.append(
                            VisionEvent(
                                camera_id=camera_id,
                                event_id=str(uuid.uuid4()),
                                event_type=etype,
                                timestamp_ms=now,
                                capture_ts_ms=capture_ts_ms,
                                object=det,
                                alert_level=level,
                            )
                        )
                    self._person_state[det.object_id] = level
            elif det.type == "obstacle":
                seen_obs.add(det.object_id)
                if det.object_id not in self._obstacles:
                    events.append(
                        VisionEvent(
                            camera_id=camera_id,
                            event_id=str(uuid.uuid4()),
                            event_type="obstacle_appeared",
                            timestamp_ms=now,
                            capture_ts_ms=capture_ts_ms,
                            object=det,
                            alert_level="warning",
                        )
                    )
                self._obstacles[det.object_id] = 0

        gone = []
        for oid in list(self._obstacles):
            if oid in seen_obs:
                continue
            self._obstacles[oid] += 1
            if self._obstacles[oid] > self.obstacle_ttl_miss:
                gone.append(oid)
        for oid in gone:
            del self._obstacles[oid]
            dummy = Detection(type="obstacle", confidence=0.0, bbox_xyxy=[0, 0, 0, 0], object_id=oid)
            events.append(
                VisionEvent(
                    camera_id=camera_id,
                    event_id=str(uuid.uuid4()),
                    event_type="obstacle_cleared",
                    timestamp_ms=now,
                    capture_ts_ms=capture_ts_ms,
                    object=dummy,
                    alert_level="none",
                )
            )
        return events


def _transition_event(obj_type: str, prev: AlertLevel, now: AlertLevel) -> str | None:
    kind = "person" if obj_type == "person" else "vehicle"
    if now == "warning" and prev == "none":
        return f"{kind}_enter_warning"
    if now == "danger" and prev != "danger":
        return f"{kind}_enter_danger"
    if now == "none" and prev in ("warning", "danger"):
        return f"{kind}_leave_warning"
    if now == "warning" and prev == "danger":
        return f"{kind}_enter_warning"
    return None
