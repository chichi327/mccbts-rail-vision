# 打包与现场部署

开发机打一份包，现场解压后启动。不要在开发仓库里直接跑 `deploy/field/` 的 compose。

## 开发机打包

本机已装 Docker，在仓库根：

```bash
bash scripts/package.sh
```

产物只有一个文件：

```
dist/mccbts-rail-vision-<version>-field.tgz
```

（版本来自 `pyproject.toml` 的 `version`。）包内含算法镜像、MediaMTX 镜像、现场 compose、`config/`、启停脚本。**不含**开发机 `.env`。

本机已有 MediaMTX 镜像时不会再拉。构建需要 `python:3.11-slim-bookworm`；连不上 Docker Hub（`auth.docker.io` 被重置）时，脚本会自动改用 DaoCloud 镜像再试。也可手动指定：

```bash
PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.11-slim-bookworm \
MEDIAMTX_IMAGE=docker.m.daocloud.io/bluenviron/mediamtx:1.11.3 \
bash scripts/package.sh
```

## 拷到算法服务器后

```bash
tar xzf mccbts-rail-vision-0.1.0-field.tgz
cd mccbts-rail-vision-0.1.0
# 改 config/mediamtx.yml 海康 source、config/cameras.yaml、标定目录
./start.sh
```

无 GPU：`./start.sh --cpu`。停止：`./stop.sh`。

`start.sh` 会在缺镜像时 `docker load`，缺 `.env` 时从 `.env.example` 复制。健康 `http://127.0.0.1:8080/health`，有码流后预览 `http://127.0.0.1:8081/preview`。

现场 compose 使用 host 网络，相机网段与本机直通。服务器需要 Docker Compose v2；GPU 机需要 NVIDIA Container Toolkit。

## 本地开发（不打包）

可编辑安装：`pip install -e .`，入口仍是仓库根 `main.py`。

调试镜像：

```bash
docker build -t mccbts-rail-vision:local .
docker compose up -d
```

无 GPU 叠 `docker-compose.cpu.yml`。开发机默认桥接网络；Linux 现场请用发布包，不要手动拼 `docker-compose.field.yml`。

不要把 `.env` 打进镜像。单独 `docker run` 算法镜像时须另起 MediaMTX；现场用包内 compose。
