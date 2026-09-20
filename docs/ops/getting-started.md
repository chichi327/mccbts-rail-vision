# 启动与本地运行

面向人的操作说明。架构原理见 [system-design.md](../architecture/system-design.md)。

## 环境要求

- Linux 算法服务器建议：NVIDIA GPU + 驱动，Python 3.10+
- macOS / 无 GPU：无相机时用 `config/cameras.synthetic.yaml` 跑通框架，不测硬解
- 依赖：FFmpeg。ingest **只拉本机 MediaMTX RTSP**（`rtsp://127.0.0.1:8554/...`）。海康由中转拉取；本机 USB 由 `bash scripts/start.sh --webcam` 用 FFmpeg 推入同一中转。无 `source: webcam` 直采。

## 第一次安装

在仓库根目录：

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -U pip
pip install -e ".[dev]"
cp .env.example .env        # 填后端 URL 和 token
```

无编辑安装时也可用：`pip install -r requirements.txt`，并把仓库根加入 `PYTHONPATH`。

## 生成示例标定（无供应商文件时）

```bash
python scripts/gen_sample_calib.py
```

会在 `config/calib/cam01/` 写入可跑通几何链路的示例，**不能当现场精度用**。

## 启动算法服务

```bash
bash scripts/start.sh
```

等价于：

```bash
python main.py --config-dir config
```

默认 `config/cameras.yaml` 已是 `source: rtsp`、`rtsp_main: rtsp://127.0.0.1:8554/cam01`。先有一路画面进 MediaMTX，再 `bash scripts/start.sh`。浏览器打开 `http://127.0.0.1:8081/preview`（见 [verify-with-camera.md](verify-with-camera.md)）。

本机 USB：

```bash
bash scripts/start.sh --webcam
```

无相机单测：临时用 `config/cameras.synthetic.yaml` 覆盖 `config/cameras.yaml` 的内容（加载器读的仍是 `cameras.yaml` 这个文件名）。

`.env` 里后端若仍是占位 `http://backend/...`，则跳过 HTTP 上报，不刷超时。

## 接真实摄像头（验证通路）

步骤见 [verify-with-camera.md](verify-with-camera.md)（本机 `--webcam` 或海康经 MediaMTX）。

业务上后续要拍板的事项见 [follow-up-checklist.md](follow-up-checklist.md)。

## 接海康相机（工位一台或现场多路都一样）

海康与现场同一套：

1. 填写 `config/mediamtx.yml` 里 `paths.cam01.source` 为该相机主码流  
2. `cameras.yaml` 保持 `source: rtsp`，`rtsp_main: rtsp://127.0.0.1:8554/cam01`  
3. `docker compose up -d mediamtx`，再 `bash scripts/start.sh`（不要加 `--webcam`）  
4. 标定仍放 `config/calib/cam01/`  

详见 [mediamtx.md](mediamtx.md)。6 路模板见 `config/cameras.rtsp.example.yaml`。

## 单路调试

```bash
python scripts/test_single_camera.py --camera-id cam01
```

只拉一帧、跑人车链并打印 Detection，不启动完整多进程。

## 健康检查

默认 HTTP：`http://127.0.0.1:8080/health`（见 `config/system.yaml` 的 `health.port`）。

JSON 含每路心跳快照。`status=degraded` 表示有运维问题，不是「没人」。日志可 grep：

- `HEALTH_FAULT` / `HEALTH_RECOVER` / `HEALTH_STATUS`
- `issue=camera_offline` | `pipeline_person_dead` | `pipeline_obstacle_dead` | `calib_invalid`

## 跑测试

```bash
pytest -q
```

## 停服务

`Ctrl+C` 即可。`--webcam` 时脚本会停掉 FFmpeg 和临时 MediaMTX 容器。
