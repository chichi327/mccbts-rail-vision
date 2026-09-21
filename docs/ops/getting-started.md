# 启动与本地运行

面向人的操作说明。架构原理见 [system-design.md](../architecture/system-design.md)。

**macOS / Linux 用 `scripts/*.sh`，Windows 用 `scripts/*.ps1`。** 海康接入逻辑两边一样。

| 系统 | 启动算法 | 停算法 + MediaMTX |
|------|----------|-------------------|
| macOS / Linux | `bash scripts/start.sh` | `bash scripts/stop.sh` |
| Windows | `powershell -ExecutionPolicy Bypass -File scripts\start.ps1` | `powershell -ExecutionPolicy Bypass -File scripts\stop.ps1` |

前面都要先：`docker compose up -d mediamtx`（两台电脑命令相同）。

## 环境要求

- Linux 算法服务器建议：NVIDIA GPU + 驱动，Python 3.10+
- ingest **只拉本机 MediaMTX RTSP**（`rtsp://127.0.0.1:8554/...`）。海康地址写在 `config/mediamtx.yml`。

## 第一次安装

在仓库根目录。

Linux / macOS：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
cp .env.example .env        # 填后端 URL 和 token
```

Windows PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
Copy-Item .env.example .env
```

无编辑安装时也可用：`pip install -r requirements.txt`，并把仓库根加入 `PYTHONPATH`。`ultralytics` 会带上 PyTorch，体积较大。人车权重放 `algorithms/person_vehicle_detect/models/yolo11n.pt`（不进 git）。

## 生成示例标定（无供应商文件时）

```bash
python scripts/gen_sample_calib.py
```

会在 `config/calib/cam01/` 写入可跑通几何链路的示例，**不能当现场精度用**。

## 启动

1. 填写 `config/mediamtx.yml` 里 `paths.cam01.source` 为海康主码流  
2. `config/cameras.yaml`：`source: rtsp`，`rtsp_main: rtsp://127.0.0.1:8554/cam01`  
3. 起中转再起算法（两台电脑都要先起 MediaMTX）：

macOS / Linux：

```bash
docker compose up -d mediamtx
bash scripts/start.sh
```

Windows：

```powershell
docker compose up -d mediamtx
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```

等价于 `python main.py --config-dir config`。浏览器打开 `http://127.0.0.1:8081/preview`（见 [verify-with-camera.md](verify-with-camera.md)）。

`.env` 里后端若仍是占位 `http://backend/...`，则跳过 HTTP 上报，不刷超时。

工位一台海康与现场多路同一套接法，详见 [mediamtx.md](mediamtx.md)。6 路模板见 `config/cameras.rtsp.example.yaml`。

业务上后续要拍板的事项见 [follow-up-checklist.md](follow-up-checklist.md)。

## 单路调试

```bash
python scripts/test_single_camera.py --camera-id cam01
```

只拉一帧、跑人车链并打印 Detection，不启动完整多进程。须先有 MediaMTX 码流。

## 健康检查

默认 HTTP：`http://127.0.0.1:8080/health`（见 `config/system.yaml` 的 `health.port`）。

JSON 含每路心跳快照。`status=degraded` 表示有运维问题，不是「没人」。日志可 grep：

- `HEALTH_FAULT` / `HEALTH_RECOVER` / `HEALTH_STATUS`
- `issue=camera_offline` | `pipeline_person_dead` | `pipeline_obstacle_dead` | `calib_invalid`

## 跑测试

```bash
pytest -q
```

无相机即可跑通（不连海康）。验证真码流用上面的启动步骤。

## 停服务

一次性停算法（Windows 会杀掉 spawn 子进程）和本仓库 MediaMTX 容器。

macOS / Linux：

```bash
bash scripts/stop.sh
```

Windows：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\stop.ps1
```

不要只关 Cursor 后台任务，子进程可能还占着 8080/8081。现场发布包用包内 `./stop.sh`。
