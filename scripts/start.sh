#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

WEBCAM=0
if [[ "${1:-}" == "--webcam" ]]; then
  WEBCAM=1
fi

if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
if [[ ! -f config/calib/cam01/camera.npz ]]; then
  python scripts/gen_sample_calib.py
fi

MTX_CID="mccbts-mediamtx-webcam"
FFMPEG_PID=""
MTX_PID=""

cleanup() {
  if [[ -n "${FFMPEG_PID}" ]]; then
    kill "${FFMPEG_PID}" 2>/dev/null || true
  fi
  if [[ -n "${MTX_PID}" ]]; then
    kill "${MTX_PID}" 2>/dev/null || true
  fi
  docker rm -f "${MTX_CID}" 2>/dev/null || true
}

if [[ "${WEBCAM}" == "1" ]]; then
  if ! command -v docker >/dev/null 2>&1 && ! command -v mediamtx >/dev/null 2>&1; then
    echo "本机 webcam 需要 Docker（跑 MediaMTX）或本机 mediamtx 二进制。" >&2
    exit 1
  fi
  echo "本机 webcam：FFmpeg → MediaMTX → ingest（与现场同一条 RTSP 链路）"
  echo "请先停掉占用 8554 的其它 MediaMTX（如 docker compose 现场配置）。"
  trap cleanup EXIT INT TERM
  if command -v docker >/dev/null 2>&1; then
    docker rm -f "${MTX_CID}" 2>/dev/null || true
    docker run -d --name "${MTX_CID}" \
      -p 8554:8554 -p 8889:8889 \
      -v "${ROOT}/config/mediamtx.webcam.yml:/mediamtx.yml:ro" \
      bluenviron/mediamtx:1.11.3
  else
    mediamtx "${ROOT}/config/mediamtx.webcam.yml" &
    MTX_PID=$!
  fi
  sleep 2
  bash "${ROOT}/scripts/publish_webcam.sh" &
  FFMPEG_PID=$!
  echo "等待推流就绪…"
  sleep 3
  if ! kill -0 "${FFMPEG_PID}" 2>/dev/null; then
    echo "FFmpeg 推流失败（常见：macOS 帧率须 30，或相机权限/被占用）。预览不会有画面。" >&2
    echo "可试：WEBCAM_FPS=30 WEBCAM_PIXEL_FORMAT=nv12 bash scripts/start.sh --webcam" >&2
    exit 1
  fi
  python main.py --config-dir config
  exit $?
fi

exec python main.py --config-dir config
