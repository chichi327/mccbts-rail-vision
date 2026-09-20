from core.ingest.sources import redact_rtsp


def test_redact_rtsp_hides_password():
    assert redact_rtsp("rtsp://admin:secret@192.168.1.64:554/Streaming/Channels/101") == (
        "rtsp://***@192.168.1.64:554/Streaming/Channels/101"
    )


def test_redact_rtsp_plain():
    assert redact_rtsp("rtsp://127.0.0.1:8554/cam01") == "rtsp://127.0.0.1:8554/cam01"
