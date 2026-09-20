from __future__ import annotations

import logging
from typing import Iterable

from core.base.types import CalibStatus, Heartbeat

log = logging.getLogger(__name__)

ISSUE_CAMERA_OFFLINE = "camera_offline"
ISSUE_PIPELINE_PERSON_DEAD = "pipeline_person_dead"
ISSUE_PIPELINE_OBSTACLE_DEAD = "pipeline_obstacle_dead"
ISSUE_CALIB_INVALID = "calib_invalid"
ISSUE_CALIB_STALE = "calib_stale"


def frame_age_ms(last_frame_ts_ms: int, now_ms: int) -> int:
    if last_frame_ts_ms <= 0:
        return now_ms
    return max(0, now_ms - last_frame_ts_ms)


def camera_is_online(age_ms: int, last_frame_ts_ms: int, offline_after_ms: int) -> bool:
    if last_frame_ts_ms <= 0:
        return False
    return age_ms <= offline_after_ms


def issues_of(
    *,
    camera_online: bool,
    pipeline_person_alive: bool,
    pipeline_obstacle_alive: bool,
    calib_status: CalibStatus,
) -> list[str]:
    issues: list[str] = []
    if not camera_online:
        issues.append(ISSUE_CAMERA_OFFLINE)
    if not pipeline_person_alive:
        issues.append(ISSUE_PIPELINE_PERSON_DEAD)
    if not pipeline_obstacle_alive:
        issues.append(ISSUE_PIPELINE_OBSTACLE_DEAD)
    if calib_status == "invalid":
        issues.append(ISSUE_CALIB_INVALID)
    elif calib_status == "stale":
        issues.append(ISSUE_CALIB_STALE)
    return issues


def build_heartbeat(
    *,
    camera_id: str,
    ts_ms: int,
    last_frame_ts_ms: int,
    offline_after_ms: int,
    pipeline_person_alive: bool,
    pipeline_obstacle_alive: bool,
    calib_status: CalibStatus,
    dropped_stale_frames: int,
    calib_reason: str = "",
) -> Heartbeat:
    age = frame_age_ms(last_frame_ts_ms, ts_ms)
    online = camera_is_online(age, last_frame_ts_ms, offline_after_ms)
    issues = issues_of(
        camera_online=online,
        pipeline_person_alive=pipeline_person_alive,
        pipeline_obstacle_alive=pipeline_obstacle_alive,
        calib_status=calib_status,
    )
    return Heartbeat(
        camera_id=camera_id,
        ts_ms=ts_ms,
        camera_online=online,
        pipeline_person_alive=pipeline_person_alive,
        pipeline_obstacle_alive=pipeline_obstacle_alive,
        calib_status=calib_status,
        last_frame_age_ms=age,
        dropped_stale_frames=dropped_stale_frames,
        issues=issues,
        calib_reason=calib_reason if calib_status != "ok" else "",
    )


def log_health_transitions(
    camera_id: str,
    previous: Iterable[str],
    current: Iterable[str],
    hb: Heartbeat,
) -> None:
    prev = set(previous)
    curr = set(current)
    extra = (
        f"age_ms={hb.last_frame_age_ms} person_alive={hb.pipeline_person_alive} "
        f"obstacle_alive={hb.pipeline_obstacle_alive} calib={hb.calib_status}"
        f"{' reason=' + hb.calib_reason if hb.calib_reason else ''}"
    )
    for issue in sorted(curr - prev):
        log.warning("HEALTH_FAULT camera=%s issue=%s %s", camera_id, issue, extra)
    for issue in sorted(prev - curr):
        log.info("HEALTH_RECOVER camera=%s issue=%s %s", camera_id, issue, extra)
    if curr:
        log.info("HEALTH_STATUS camera=%s issues=%s %s", camera_id, ",".join(hb.issues), extra)
    else:
        log.debug("HEALTH_STATUS camera=%s issues=none %s", camera_id, extra)
