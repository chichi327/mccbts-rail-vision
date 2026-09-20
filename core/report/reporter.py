from __future__ import annotations

import json
import logging
from collections import deque
from pathlib import Path
from typing import Any

import httpx

from core.base.types import Heartbeat, VisionEvent

log = logging.getLogger(__name__)


class HTTPReporter:
    def __init__(self, backend: dict[str, Any], queue_dir: str = "data/retry_queue"):
        self.events_url = backend.get("events_url") or ""
        self.heartbeat_url = backend.get("heartbeat_url") or ""
        self.token = backend.get("token") or ""
        self.timeout = float(backend.get("post_timeout_ms", 100)) / 1000.0
        self.max_queue = int(backend.get("retry_queue_size", 1000))
        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self._pending: deque[tuple[str, dict[str, Any]]] = deque()
        self._client = httpx.Client(timeout=self.timeout)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def report_event(self, event: VisionEvent) -> None:
        self._post(self.events_url, event.to_payload())

    def report_heartbeat(self, hb: Heartbeat) -> None:
        self._post(self.heartbeat_url, hb.to_payload())

    def drain_retry(self, max_n: int = 20) -> None:
        for _ in range(min(max_n, len(self._pending))):
            url, payload = self._pending.popleft()
            if not self._send(url, payload):
                self._pending.appendleft((url, payload))
                break

    def _post(self, url: str, payload: dict[str, Any]) -> None:
        if not url or url.startswith("http://backend"):
            log.debug("skip report (placeholder url) %s", payload.get("event_type") or "heartbeat")
            return
        if not self._send(url, payload):
            if len(self._pending) >= self.max_queue:
                self._pending.popleft()
            self._pending.append((url, payload))
            self._spill()

    def _send(self, url: str, payload: dict[str, Any]) -> bool:
        try:
            r = self._client.post(url, json=payload, headers=self._headers())
            return r.status_code < 500
        except Exception as exc:  # noqa: BLE001
            log.warning("report failed: %s", exc)
            return False

    def _spill(self) -> None:
        path = self.queue_dir / "pending.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for url, payload in self._pending:
                f.write(json.dumps({"url": url, "payload": payload}, ensure_ascii=False) + "\n")

    def close(self) -> None:
        self._client.close()
