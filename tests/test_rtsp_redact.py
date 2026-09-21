from core.ingest.sources import FFMPEG_CAPTURE_OPTIONS, redact_rtsp


def test_redact_rtsp_hides_password():
    assert redact_rtsp("rtsp://admin:secret@192.168.1.64:554/Streaming/Channels/101") == (
        "rtsp://***@192.168.1.64:554/Streaming/Channels/101"
    )


def test_redact_rtsp_plain():
    assert redact_rtsp("rtsp://127.0.0.1:8554/cam01") == "rtsp://127.0.0.1:8554/cam01"


def test_ffmpeg_capture_options_low_delay():
    assert "nobuffer" in FFMPEG_CAPTURE_OPTIONS
    assert "probesize;32" in FFMPEG_CAPTURE_OPTIONS
    assert "max_delay;0" in FFMPEG_CAPTURE_OPTIONS
