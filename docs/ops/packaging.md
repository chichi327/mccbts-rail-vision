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

运行（GPU 机器，含 MediaMTX 中转）：

```bash
docker compose up -d
```

Linux 现场相机网段用 host 网络：

```bash
docker compose -f docker-compose.yml -f docker-compose.field.yml up -d
```

无 GPU：

```bash
docker compose -f docker-compose.yml -f docker-compose.cpu.yml up -d
```

## 拷到现场算法服务器

1. 镜像 tar 或从内网仓库 pull
2. 挂载 `config/`（含标定）和 `.env`
3. 相机网段与容器网络打通，RTSP 走内网
4. 不要把 `.env` 打进镜像

单独 `docker run` 算法镜像时，须在同机另起 MediaMTX，且 `rtsp_main` 指向中转；现场请用 compose（含 `mediamtx` 服务）。

## 版本号

改版本只动 `pyproject.toml` 的 `version`，镜像 tag 与之对齐（`scripts/package.sh` 会读该字段）。
