import pytest

from core.ingest.sources import open_source


def test_synthetic_reads_frame():
    src = open_source(
        {"id": "cam01", "source": "synthetic", "width": 64, "height": 48, "target_fps": 30}
    )
    packet = None
    for _ in range(20):
        packet = src.read()
        if packet is not None:
            break
    src.release()
    assert packet is not None
    assert packet.frame_bgr.shape == (48, 64, 3)


def test_webcam_source_removed():
    with pytest.raises(ValueError, match="MediaMTX"):
        open_source(
            {
                "id": "cam01",
                "source": "webcam",
                "width": 64,
                "height": 48,
                "device_index": 0,
            }
        )
