from __future__ import annotations

from dataclasses import dataclass

from core.base.types import Detection


def _iou(a: list[float], b: list[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    denom = area_a + area_b - inter
    return inter / denom if denom > 0 else 0.0


@dataclass
class _Track:
    object_id: str
    bbox: list[float]
    missed: int
    type: str


class IoUTracker:
    def __init__(self, prefix: str, iou_thresh: float = 0.3, max_missed: int = 15):
        self.prefix = prefix
        self.iou_thresh = iou_thresh
        self.max_missed = max_missed
        self._seq = 0
        self._tracks: list[_Track] = []

    def update(self, detections: list[Detection]) -> list[Detection]:
        used: set[int] = set()
        for det in detections:
            best_i, best_iou = -1, 0.0
            for i, tr in enumerate(self._tracks):
                if i in used or tr.type != det.type:
                    continue
                score = _iou(det.bbox_xyxy, tr.bbox)
                if score > best_iou:
                    best_i, best_iou = i, score
            if best_i >= 0 and best_iou >= self.iou_thresh:
                tr = self._tracks[best_i]
                tr.bbox = det.bbox_xyxy
                tr.missed = 0
                det.object_id = tr.object_id
                used.add(best_i)
            else:
                self._seq += 1
                oid = f"{self.prefix}-{self._seq}"
                self._tracks.append(_Track(oid, det.bbox_xyxy, 0, det.type))
                det.object_id = oid
        alive: list[_Track] = []
        for i, tr in enumerate(self._tracks):
            if i not in used:
                tr.missed += 1
            if tr.missed <= self.max_missed:
                alive.append(tr)
        self._tracks = alive
        return detections
