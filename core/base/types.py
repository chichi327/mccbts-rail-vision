from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional

ObjectType = Literal["person", "car", "truck", "obstacle"]
AlertLevel = Literal["none", "warning", "danger"]
CalibStatus = Literal["ok", "invalid", "stale"]


@dataclass
class Detection:
    type: ObjectType
    confidence: float
    bbox_xyxy: list[float]
    object_id: str = ""
    distance_to_track_m: Optional[float] = None
    height_m: Optional[float] = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("extra", None)
        return payload


@dataclass
class VisionEvent:
    camera_id: str
    event_id: str
    event_type: str
    timestamp_ms: int
    capture_ts_ms: int
    object: Detection
    alert_level: AlertLevel

    def to_payload(self) -> dict[str, Any]:
        return {
            "camera_id": self.camera_id,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp_ms": self.timestamp_ms,
            "capture_ts_ms": self.capture_ts_ms,
            "object": {
                **self.object.to_public_dict(),
                "alert_level": self.alert_level,
            },
        }


@dataclass
class Heartbeat:
    camera_id: str
    ts_ms: int
    camera_online: bool
    pipeline_person_alive: bool
    pipeline_obstacle_alive: bool
    calib_status: CalibStatus
    last_frame_age_ms: int
    dropped_stale_frames: int
    issues: list[str] = field(default_factory=list)
    calib_reason: str = ""

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)
