import pytest

from core.ingest.sources import open_source


def test_open_source_requires_rtsp_main():
    with pytest.raises(ValueError, match="rtsp_main"):
        open_source({"id": "cam01", "source": "rtsp", "width": 64, "height": 48})


def test_open_source_rejects_non_rtsp():
    with pytest.raises(ValueError, match="只支持 source=rtsp"):
        open_source(
            {
                "id": "cam01",
                "source": "synthetic",
                "width": 64,
                "height": 48,
                "target_fps": 30,
            }
        )
    with pytest.raises(ValueError, match="只支持 source=rtsp"):
        open_source(
            {
                "id": "cam01",
                "source": "webcam",
                "width": 64,
                "height": 48,
                "device_index": 0,
            }
        )
