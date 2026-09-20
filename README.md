# mccbts-rail-vision

铁路沿线视觉算法服务：接入海康相机，跑人员/车辆检测与到轨距离、障碍物检测与高度，把**事件**推到现有后端。端到端延迟目标 **< 300ms**。

## 人从这里开始

| 我想… | 打开 |
|--------|------|
| 安装、启动、单路调试 | [docs/ops/getting-started.md](docs/ops/getting-started.md) |
| Docker 打包、现场部署 | [docs/ops/packaging.md](docs/ops/packaging.md) |
| 相机 / 标定 / `.env` | [docs/ops/configuration.md](docs/ops/configuration.md) |
| 整体架构（拍板文档） | [docs/architecture/system-design.md](docs/architecture/system-design.md) |
| 这个目录是干什么的 | [docs/ai/architecture-map.md](docs/ai/architecture-map.md) |
| 算法团队怎么接插件 | [docs/algorithms/plugin-guide.md](docs/algorithms/plugin-guide.md) |

最短路径：

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python scripts/gen_sample_calib.py
bash scripts/start.sh
```

健康检查：`http://127.0.0.1:8080/health`。默认相机是合成帧，不连海康也能把两条流水线跑起来。

## AI 从这里开始

读 [AGENTS.md](AGENTS.md)。改代码后按 `.cursor/rules` 同步 `docs/ai/module-map.yaml` 并运行 `python scripts/sync_architecture_map.py`。已拍板决策写在 [docs/ai/memory.md](docs/ai/memory.md)。

## 运行时结构（摘要）

```
海康主码流 → ingest（硬解/OpenCV、去畸变、最新帧）
                ├─ 流水线 person_vehicle：检测 → 跟踪 → 测距
                └─ 流水线 obstacle：检测 → 跟踪 → 高度
                        → 事件 → HTTP 上报现有后端
子码流 → MediaMTX 预览（不在 300ms 链路上）
```
