#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "打包需要本机 Docker。" >&2
  exit 1
fi

mkdir -p dist
VERSION="$(python -c "import re; print(re.search(r'^version = \"([^\"]+)\"', open('pyproject.toml').read(), re.M).group(1))")"
TAG="mccbts-rail-vision:${VERSION}"
MTX="bluenviron/mediamtx:1.11.3"
# Docker Hub 不通时可用：PYTHON_IMAGE=... MEDIAMTX_IMAGE=... bash scripts/package.sh
PYTHON_IMAGE="${PYTHON_IMAGE:-python:3.11-slim-bookworm}"
PYTHON_IMAGE_MIRROR="${PYTHON_IMAGE_MIRROR:-docker.m.daocloud.io/library/python:3.11-slim-bookworm}"
MEDIAMTX_IMAGE="${MEDIAMTX_IMAGE:-bluenviron/mediamtx:1.11.3}"
BUNDLE="dist/mccbts-rail-vision-${VERSION}"
TGZ="dist/mccbts-rail-vision-${VERSION}-field.tgz"

build_app() {
  local base="$1"
  echo "docker build PYTHON_IMAGE=${base}"
  docker build --build-arg "PYTHON_IMAGE=${base}" -t "$TAG" -t mccbts-rail-vision:local .
}

if ! build_app "$PYTHON_IMAGE"; then
  if [[ "$PYTHON_IMAGE" == "$PYTHON_IMAGE_MIRROR" ]]; then
    exit 1
  fi
  echo "官方基础镜像拉取失败，改用 ${PYTHON_IMAGE_MIRROR}" >&2
  build_app "$PYTHON_IMAGE_MIRROR"
fi
if ! docker image inspect "$MTX" >/dev/null 2>&1; then
  docker pull "$MEDIAMTX_IMAGE"
  if [[ "$MEDIAMTX_IMAGE" != "$MTX" ]]; then
    docker tag "$MEDIAMTX_IMAGE" "$MTX"
  fi
fi

rm -rf "$BUNDLE"
mkdir -p "$BUNDLE/images" "$BUNDLE/data"
docker save -o "$BUNDLE/images/mccbts-rail-vision-${VERSION}.tar" "$TAG"
docker save -o "$BUNDLE/images/mediamtx-1.11.3.tar" "$MTX"

cp deploy/field/docker-compose.yml "$BUNDLE/"
cp deploy/field/docker-compose.cpu.yml "$BUNDLE/"
cp deploy/field/start.sh "$BUNDLE/"
cp deploy/field/stop.sh "$BUNDLE/"
chmod +x "$BUNDLE/start.sh" "$BUNDLE/stop.sh"
printf '%s\n' "$VERSION" > "$BUNDLE/VERSION"
cp .env.example "$BUNDLE/.env.example"
cp -a config "$BUNDLE/config"

cat > "$BUNDLE/README.txt" <<EOF
解压后在本目录执行：
  ./start.sh          # Linux 现场 GPU + host 网络
  ./start.sh --cpu    # 无 GPU
  ./stop.sh

首次请改 config/mediamtx.yml（海康 source）和 config/calib/。
.env 首次会自动从 .env.example 复制。
EOF

tar -C dist -czf "$TGZ" "mccbts-rail-vision-${VERSION}"
echo "bundle $TGZ"
echo "field: tar xzf $(basename "$TGZ") && cd mccbts-rail-vision-${VERSION} && ./start.sh"
