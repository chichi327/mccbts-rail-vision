from core.health.classify import (
    ISSUE_CALIB_INVALID,
    ISSUE_CAMERA_OFFLINE,
    ISSUE_PIPELINE_OBSTACLE_DEAD,
    ISSUE_PIPELINE_PERSON_DEAD,
    build_heartbeat,
    issues_of,
)
from services.health_check import health_snapshot


def test_issues_distinguish_three_failures():
    none = issues_of(
        camera_online=True,
        pipeline_person_alive=True,
        pipeline_obstacle_alive=True,
        calib_status="ok",
    )
    assert none == []

    stream = issues_of(
        camera_online=False,
        pipeline_person_alive=True,
        pipeline_obstacle_alive=True,
        calib_status="ok",
    )
    assert stream == [ISSUE_CAMERA_OFFLINE]

    person_dead = issues_of(
        camera_online=True,
        pipeline_person_alive=False,
        pipeline_obstacle_alive=True,
        calib_status="ok",
    )
    assert person_dead == [ISSUE_PIPELINE_PERSON_DEAD]

    obstacle_dead = issues_of(
        camera_online=True,
        pipeline_person_alive=True,
        pipeline_obstacle_alive=False,
        calib_status="ok",
    )
    assert obstacle_dead == [ISSUE_PIPELINE_OBSTACLE_DEAD]

    calib = issues_of(
        camera_online=True,
        pipeline_person_alive=True,
        pipeline_obstacle_alive=True,
        calib_status="invalid",
    )
    assert calib == [ISSUE_CALIB_INVALID]


def test_build_heartbeat_marks_offline_when_no_frame():
    hb = build_heartbeat(
        camera_id="cam01",
        ts_ms=10_000,
        last_frame_ts_ms=0,
        offline_after_ms=3000,
        pipeline_person_alive=True,
        pipeline_obstacle_alive=True,
        calib_status="ok",
        dropped_stale_frames=0,
    )
    assert hb.camera_online is False
    assert ISSUE_CAMERA_OFFLINE in hb.issues


def test_build_heartbeat_online_when_frame_fresh():
    hb = build_heartbeat(
        camera_id="cam01",
        ts_ms=10_000,
        last_frame_ts_ms=9_500,
        offline_after_ms=3000,
        pipeline_person_alive=True,
        pipeline_obstacle_alive=True,
        calib_status="ok",
        dropped_stale_frames=2,
    )
    assert hb.camera_online is True
    assert hb.last_frame_age_ms == 500
    assert hb.issues == []
    payload = hb.to_payload()
    assert payload["dropped_stale_frames"] == 2


def test_health_snapshot_degraded_when_issues():
    snap = health_snapshot(
        {"cam01": {"camera_id": "cam01", "issues": ["camera_offline"]}},
        extra={"cameras": ["cam01"]},
    )
    assert snap["status"] == "degraded"
    assert snap["cameras"] == ["cam01"]


def test_log_health_transitions(caplog):
    import logging

    from core.health.classify import log_health_transitions

    hb = build_heartbeat(
        camera_id="cam01",
        ts_ms=10_000,
        last_frame_ts_ms=0,
        offline_after_ms=3000,
        pipeline_person_alive=False,
        pipeline_obstacle_alive=True,
        calib_status="invalid",
        dropped_stale_frames=0,
        calib_reason="missing files",
    )
    with caplog.at_level(logging.INFO):
        log_health_transitions("cam01", [], hb.issues, hb)
    text = caplog.text
    assert "HEALTH_FAULT" in text
    assert "issue=camera_offline" in text
    assert "issue=pipeline_person_dead" in text
    assert "issue=calib_invalid" in text
    assert "HEALTH_STATUS" in text
    caplog.clear()
    with caplog.at_level(logging.INFO):
        log_health_transitions("cam01", hb.issues, [], hb)
    assert "HEALTH_RECOVER" in caplog.text
