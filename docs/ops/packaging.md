# 打包与部署

## 本地可编辑包

```bash
pip install -e .
```

产物是 Python 包 `mccbts-rail-vision`（见 `pyproject.toml`），运行入口仍是仓库根的 `main.py`。

## Docker 镜像

仓库根：

```bash
bash scripts/package.sh
```

该脚本会：

1. `docker build -t mccbts-rail-vision:local .`
2. 可选：`docker save` 出 `dist/mccbts-rail-vision-local.tar` 便于拷到算法服务器

手动构建：

```bash
docker build -t mccbts-rail-vision:local .
```

运行（GPU 机器）：

```bash
docker compose up -d rail-vision
```

仅预览中转：

```bash
docker compose --profile preview up -d
```

Compose 里 `rail-vision` 服务需要 NVIDIA Container Toolkit；无 GPU 时用：

```bash
docker compose -f docker-compose.yml -f docker-compose.cpu.yml up
```

（若未提供 cpu override，可改 `docker-compose.yml` 去掉 `runtime: nvidia`，并把相机 `source` 设为 `synthetic`。）

## 拷到现场算法服务器

1. 镜像 tar 或从内网仓库 pull
2. 挂载 `config/`（含标定）和 `.env`
3. 相机网段与容器网络打通，RTSP 走内网
4. 不要把 `.env` 打进镜像

```bash
docker run --rm --gpus all --env-file .env \
  -v "$PWD/config:/app/config:ro" \
  -p 8080:8080 \
  mccbts-rail-vision:local
```

## 版本号

改版本只动 `pyproject.toml` 的 `version`，镜像 tag 与之对齐（`scripts/package.sh` 会读该字段）。
