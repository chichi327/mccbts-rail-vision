import numpy as np

from core.base.types import Detection
from core.preview.annotate import annotate_frame


def test_annotate_keeps_shape():
    frame = np.zeros((80, 80, 3), dtype=np.uint8)
    det = Detection(type="person", confidence=0.9, bbox_xyxy=[10, 10, 40, 50], distance_to_track_m=1.2)
    out = annotate_frame(frame, [det])
    assert out.shape == frame.shape
    assert not np.array_equal(out, frame)
