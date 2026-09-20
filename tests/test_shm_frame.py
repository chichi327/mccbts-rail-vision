import multiprocessing as mp

import numpy as np

from core.ingest.shm_frame import SharedFrameBuffer


def test_shared_frame_roundtrip():
    ctx = mp.get_context("spawn")
    buf = SharedFrameBuffer(32, 16, ctx=ctx)
    try:
        frame = np.full((16, 32, 3), 7, dtype=np.uint8)
        buf.write(frame, 123)
        out, ts, seq = buf.read_copy()
        assert ts == 123
        assert seq >= 1
        assert out is not None
        assert out.shape == (16, 32, 3)
        assert int(out[0, 0, 0]) == 7
    finally:
        buf.close(unlink=True)
