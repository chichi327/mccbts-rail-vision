#!/usr/bin/env bash
# 停本仓库开发机：算法 main.py + MediaMTX。Windows 请用本脚本或 scripts/stop.ps1。
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if command -v powershell.exe >/dev/null 2>&1; then
  WIN_PS1="$ROOT/scripts/stop.ps1"
  if command -v cygpath >/dev/null 2>&1; then
    WIN_PS1="$(cygpath -w "$ROOT/scripts/stop.ps1")"
  fi
  exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$WIN_PS1"
fi

if command -v docker >/dev/null 2>&1; then
  docker compose stop mediamtx 2>/dev/null || true
  docker compose stop rail-vision 2>/dev/null || true
  docker rm -f mccbts-mediamtx-webcam 2>/dev/null || true
  echo "已请求停止 docker compose 中的 mediamtx / rail-vision。"
fi

if pgrep -f "${ROOT}.*main.py --config-dir" >/dev/null 2>&1; then
  pkill -f "${ROOT}.*main.py --config-dir" || true
  echo "已结束本仓库 python main.py。"
else
  echo "没有发现本仓库的 python main.py。"
fi
echo "关闭完成。"
