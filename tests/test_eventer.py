from core.base.types import Detection
from core.event.eventer import Eventer, alert_level


def test_alert_level():
    assert alert_level(3.0, 2.0, 1.0) == "none"
    assert alert_level(1.5, 2.0, 1.0) == "warning"
    assert alert_level(0.4, 2.0, 1.0) == "danger"
    assert alert_level(None, 2.0, 1.0) == "none"


def test_person_enter_warning_once():
    ev = Eventer()
    det = Detection(
        type="person",
        confidence=0.9,
        bbox_xyxy=[1, 2, 3, 4],
        object_id="p1",
        distance_to_track_m=1.6,
    )
    first = ev.feed("cam01", 1, [det])
    second = ev.feed("cam01", 2, [det])
    assert [e.event_type for e in first] == ["person_enter_warning"]
    assert second == []


def test_obstacle_appear_and_clear():
    ev = Eventer(obstacle_ttl_miss=1)
    det = Detection(type="obstacle", confidence=0.8, bbox_xyxy=[0, 0, 10, 10], object_id="o1")
    appeared = ev.feed("cam01", 1, [det])
    assert appeared[0].event_type == "obstacle_appeared"
    ev.feed("cam01", 2, [])
    cleared = ev.feed("cam01", 3, [])
    assert any(e.event_type == "obstacle_cleared" for e in cleared)
