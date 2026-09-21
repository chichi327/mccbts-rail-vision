# mccbts-rail-vision

铁路沿线视觉算法服务：接入海康相机，跑人员/车辆检测与到轨距离、障碍物检测与高度，把**事件**推到现有后端。端到端延迟目标 **< 300ms**。

## 人从这里开始

完整文档目录：[docs/README.md](docs/README.md)。

| 我想… | 打开 |
|--------|------|
| 安装、启动、单路调试 | [docs/ops/getting-started.md](docs/ops/getting-started.md) |
| 后续逐项确认清单 | [docs/ops/follow-up-checklist.md](docs/ops/follow-up-checklist.md) |
| 手头摄像头验证通路 | [docs/ops/verify-with-camera.md](docs/ops/verify-with-camera.md) |
| MediaMTX 现场中转 | [docs/ops/mediamtx.md](docs/ops/mediamtx.md) |
| 打现场包、服务器 ./start.sh | [docs/ops/packaging.md](docs/ops/packaging.md) |
| 相机 / 标定 / `.env` | [docs/ops/configuration.md](docs/ops/configuration.md) |
| 整体架构（拍板文档） | [docs/architecture/system-design.md](docs/architecture/system-design.md) |
| 这个目录是干什么的 | [docs/ai/architecture-map.md](docs/ai/architecture-map.md) |
| 算法团队怎么接插件 | [docs/algorithms/plugin-guide.md](docs/algorithms/plugin-guide.md) |

最短路径：先改 `config/mediamtx.yml` 海康 `source`。Docker 起中转两边相同：`docker compose up -d mediamtx`。

macOS / Linux：

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python scripts/gen_sample_calib.py
docker compose up -d mediamtx
bash scripts/start.sh
# 停：bash scripts/stop.sh
```

Windows：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
python scripts\gen_sample_calib.py
docker compose up -d mediamtx
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
# 停：powershell -ExecutionPolicy Bypass -File scripts\stop.ps1
```

健康检查：`http://127.0.0.1:8080/health`。有码流后预览：`http://127.0.0.1:8081/preview`。

## AI 从这里开始

读 [AGENTS.md](AGENTS.md)。按需打开 [docs/README.md](docs/README.md)。改代码后按 `.cursor/rules` 同步 `docs/ai/module-map.yaml` 并运行 `python scripts/sync_architecture_map.py`。已拍板决策写在 [docs/ai/memory.md](docs/ai/memory.md)。

## 运行时结构（摘要）

```
海康主码流 → 本机 MediaMTX（透传重连）→ ingest → 共享内存
                ├─ 流水线 person_vehicle：检测 → 跟踪 → 距
                └─ 流水线 obstacle：检测 → 跟踪 → 高度
                        → 事件 → HTTP 上报
叠框预览 8081（旁路，不计入 300ms）
```
