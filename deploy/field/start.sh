#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "现场需要已安装 Docker。" >&2
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "现场需要 Docker Compose v2（docker compose）。" >&2
  exit 1
fi

CPU=0
FORCE_LOAD=0
for arg in "$@"; do
  case "$arg" in
    --cpu) CPU=1 ;;
    --reload-images) FORCE_LOAD=1 ;;
    -h|--help)
      echo "用法: ./start.sh [--cpu] [--reload-images]"
      echo "  --cpu            无 NVIDIA 运行时"
      echo "  --reload-images  强制重新 docker load 包内镜像"
      exit 0
      ;;
    *)
      echo "未知参数: $arg （./start.sh --help）" >&2
      exit 1
      ;;
  esac
done

load_if_needed() {
  local image="$1"
  local tarpath="$2"
  if [[ "${FORCE_LOAD}" == "1" ]] || ! docker image inspect "${image}" >/dev/null 2>&1; then
    echo "导入 ${image} ← ${tarpath}"
    docker load -i "${tarpath}"
  fi
}

VERSION="$(cat VERSION)"
load_if_needed "mccbts-rail-vision:${VERSION}" "images/mccbts-rail-vision-${VERSION}.tar"
load_if_needed "bluenviron/mediamtx:1.11.3" "images/mediamtx-1.11.3.tar"
if ! docker image inspect mccbts-rail-vision:local >/dev/null 2>&1; then
  docker tag "mccbts-rail-vision:${VERSION}" mccbts-rail-vision:local
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "已从 .env.example 生成 .env（后端仍是占位则跳过上报）。"
fi
mkdir -p data

COMPOSE=(docker compose -f docker-compose.yml)
if [[ "${CPU}" == "1" ]]; then
  COMPOSE+=(-f docker-compose.cpu.yml)
fi
"${COMPOSE[@]}" up -d

echo "已启动。健康 http://127.0.0.1:8080/health  预览 http://127.0.0.1:8081/preview"
echo "改相机：编辑 config/mediamtx.yml 与 config/cameras.yaml 后执行 ./start.sh"
echo "停止：./stop.sh"
