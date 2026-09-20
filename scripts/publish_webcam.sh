#!/usr/bin/env bash
# 本机 USB → FFmpeg 推流到 MediaMTX → 与现场相同的 ingest RTSP。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DEVICE="${WEBCAM_DEVICE:-0}"
SIZE="${WEBCAM_SIZE:-1280x720}"
# macOS avfoundation 常把 15 判成非法，设备表却写着 15–30；默认 30。
FPS="${WEBCAM_FPS:-30}"
DEST="${WEBCAM_RTSP:-rtsp://127.0.0.1:8554/cam01}"
# 多数内置摄像头是 uyvy422； Continuity Camera 可试 WEBCAM_PIXEL_FORMAT=nv12
PIXEL="${WEBCAM_PIXEL_FORMAT:-uyvy422}"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "需要 ffmpeg。macOS: brew install ffmpeg" >&2
  exit 1
fi

echo "publish webcam device=${DEVICE} ${SIZE}@${FPS} -> ${DEST}"
echo "macOS 请在系统设置 → 隐私 → 相机 允许「终端」或 ffmpeg"

uname_s="$(uname -s)"
if [[ "${uname_s}" == "Darwin" ]]; then
  exec ffmpeg -hide_banner -loglevel warning \
    -f avfoundation -pixel_format "${PIXEL}" -framerate "${FPS}" \
    -video_size "${SIZE}" -i "${DEVICE}:none" \
    -pix_fmt yuv420p -c:v libx264 -preset ultrafast -tune zerolatency -g "${FPS}" \
    -f rtsp -rtsp_transport tcp "${DEST}"
fi
if [[ "${uname_s}" == "Linux" ]]; then
  exec ffmpeg -hide_banner -loglevel warning \
    -f v4l2 -framerate "${FPS}" -video_size "${SIZE}" -i "/dev/video${DEVICE}" \
    -pix_fmt yuv420p -c:v libx264 -preset ultrafast -tune zerolatency -g "${FPS}" \
    -f rtsp -rtsp_transport tcp "${DEST}"
fi
echo "不支持的系统: ${uname_s}" >&2
exit 1
