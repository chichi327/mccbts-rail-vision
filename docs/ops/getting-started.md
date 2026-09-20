# 启动与本地运行

面向人的操作说明。架构原理见 [system-design.md](../architecture/system-design.md)。

## 环境要求

- Linux 算法服务器建议：NVIDIA GPU + 驱动，Python 3.10+
- macOS / 无 GPU：可用合成帧源跑通框架（`cameras.yaml` 里 `source: synthetic`），不测硬解
- 依赖：FFmpeg（拉 RTSP 时）、可选 [MediaMTX](https://github.com/bluenviron/mediamtx)（仅预览）

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

默认 `config/cameras.yaml` 使用 `source: synthetic`，不连真实相机也会出帧、跑两条流水线、尝试向后端 POST（失败则进本地重试队列，见日志）。

## 接海康相机

1. 编辑 `config/cameras.yaml`：`source: rtsp`，填写 `rtsp_main` / `rtsp_sub`
2. 把供应商文件放到 `config/calib/<camera_id>/`（清单见 [configuration.md](configuration.md)）
3. `.env` 里配置 `BACKEND_EVENTS_URL`、`BACKEND_HEARTBEAT_URL`、`BACKEND_TOKEN`
4. 再执行 `./scripts/start.sh`

## 单路调试

```bash
python scripts/test_single_camera.py --camera-id cam01
```

只拉一帧、跑人车链并打印 Detection，不启动完整多进程。

## 健康检查

默认 HTTP：`http://127.0.0.1:8080/health`（见 `config/system.yaml` 的 `health.port`）。

## 跑测试

```bash
pytest -q
```

## 停服务

`Ctrl+C` 即可。`scripts/start.sh` 会把子进程打到同一进程组。
