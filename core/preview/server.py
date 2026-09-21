from __future__ import annotations

import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import cv2

from core.preview.annotate import annotate_frame
from core.preview.state import snapshot_live


def serve_preview(
    host: str,
    port: int,
    camera_ids: list[str],
    buffers: dict,
    det_boxes: dict,
    stop_event,
    max_width: int = 960,
    jpeg_quality: int = 60,
) -> None:
    det_cache: dict[tuple[str, str], list] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            path = self.path.split("?", 1)[0].rstrip("/") or "/"
            if path in ("/preview", "/"):
                self._html()
                return
            if path.startswith("/preview/stream/"):
                cam_id = path.rsplit("/", 1)[-1]
                if cam_id not in camera_ids:
                    self.send_response(404)
                    self.end_headers()
                    return
                self._mjpeg(cam_id)
                return
            self.send_response(404)
            self.end_headers()

        def _html(self) -> None:
            blocks = []
            for cam_id in camera_ids:
                blocks.append(
                    f'<section><h2>{cam_id}</h2>'
                    f'<img src="/preview/stream/{cam_id}" alt="{cam_id}" />'
                    f"</section>"
                )
            body = (
                "<!DOCTYPE html><html><head><meta charset='utf-8'><title>预览</title>"
                "<style>body{background:#111;color:#ddd;font-family:sans-serif}"
                "img{max-width:100%;background:#000}</style></head><body>"
                "<p>持续预览（旁路，不计入 300ms）。假检测器框位置固定是正常的。</p>"
                + "".join(blocks)
                + "</body></html>"
            )
            data = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _mjpeg(self, camera_id: str) -> None:
            self.send_response(200)
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()
            last_seq = -1
            last_sent = 0.0
            min_interval = 1.0 / 20.0
            try:
                while not stop_event.is_set():
                    frame, dets, seq = snapshot_live(buffers, det_boxes, det_cache, camera_id)
                    if frame is None or seq == last_seq:
                        time.sleep(0.005)
                        continue
                    now = time.time()
                    wait = min_interval - (now - last_sent)
                    if wait > 0:
                        time.sleep(wait)
                        continue
                    vis = annotate_frame(frame, dets)
                    h, w = vis.shape[:2]
                    if w > max_width:
                        nh = int(h * max_width / w)
                        vis = cv2.resize(vis, (max_width, nh))
                    ok, encoded = cv2.imencode(".jpg", vis, [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality])
                    if not ok:
                        continue
                    jpg = encoded.tobytes()
                    self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ")
                    self.wfile.write(str(len(jpg)).encode("ascii"))
                    self.wfile.write(b"\r\n\r\n")
                    self.wfile.write(jpg)
                    self.wfile.write(b"\r\n")
                    self.wfile.flush()
                    last_seq = seq
                    last_sent = time.time()
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
                return

        def log_message(self, fmt, *args):
            return

    server = ThreadingHTTPServer((host, port), Handler)
    server.timeout = 0.5
    while not stop_event.is_set():
        server.handle_request()
    server.server_close()
