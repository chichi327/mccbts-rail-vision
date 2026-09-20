#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p dist
VERSION="$(python -c "import re; print(re.search(r'^version = \"([^\"]+)\"', open('pyproject.toml').read(), re.M).group(1))")"
TAG="mccbts-rail-vision:${VERSION}"
docker build -t "$TAG" -t mccbts-rail-vision:local .
docker save -o "dist/mccbts-rail-vision-${VERSION}.tar" "$TAG"
echo "image $TAG"
echo "tar dist/mccbts-rail-vision-${VERSION}.tar"
