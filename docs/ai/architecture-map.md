# 目录实况（自动生成）

勿手改本文件。源文件是 [`module-map.yaml`](module-map.yaml)。
改目录职责后执行：`python scripts/sync_architecture_map.py`。

架构对错仍以 [system-design.md](../architecture/system-design.md) 为准。

| 路径 | 角色 | 维护方 | 职责 | 禁止 |
|------|------|--------|------|------|
| `core/base` | 框架 | 框架团队 | Detection、BaseDetector、BaseEstimator 统一接口 | 在插件里复制一份结果类型 |
| `core/ingest` | 接入 | 框架团队 | 本机 MediaMTX RTSP 拉流、合成源单测、去畸变、共享内存最新帧 | 跑模型、读业务阈值 |
| `core/calib` | 标定 | 框架团队 | 加载供应商文件，提供 CalibView 几何 API | 算法目录自行解析 npz |
| `core/runtime` | 调度 | 框架团队 | 加载插件、DAG 流水线进程、过期丢帧 | 写死某个模型类名（必须走配置） |
| `core/track` | 跟踪 | 框架团队 | 为人车（及障碍物）补 object_id | 修改检测类别 |
| `core/event` | 事件 | 框架团队 | 预警/危险进出、障碍物出现消失 | 直接调模型 |
| `core/report` | 上报 | 框架团队 | HTTP POST 后端、超时、本地重试队列 | 改变算法语义或字段名 |
| `core/health` | 健康 | 框架团队 | 相机/流水线/标定心跳 | 把心跳混进事件通道 |
| `core/preview` | 预览 | 框架团队 | 内网叠框预览（MJPEG /preview），不计入 300ms 链路 | 作为算法输入源 |
| `algorithms/person_vehicle_detect` | 检测器插件 | 人员车辆团队 | 已去畸变帧 → person/car/truck 框 | 计算距离；把人车标成 obstacle |
| `algorithms/track_distance` | 量测器插件 | 测距团队 | 用人车框 + CalibView 补 distance_to_track_m | 自己再跑检测 |
| `algorithms/obstacle_detect` | 检测器插件 | 障碍物团队 | 已去畸变帧 → obstacle 框 | 检出 person/car/truck |
| `algorithms/obstacle_height` | 量测器插件 | 高度团队 | 用障碍物框 + CalibView 补 height_m | 自己再跑检测 |
| `config` | 配置 | 部署/框架 | 相机、算法、流水线、系统阈值、标定、MediaMTX 中转 yml | 把密钥提交进 git（用 .env） |
| `services` | 辅助进程 | 框架团队 | 预览 HTTP、健康检查入口 | 塞进算法逻辑 |
| `scripts` | 工具 | 框架团队 | 启动、打包、文档同步、单路调试 | 作为生产常驻进程 |
| `docs` | 文档 | 全员 | 文档索引 README.md；人和 AI 按意图查找 | 新增 docs 下 md 却不写入 README 索引 |
| `docs/architecture` | 文档 | 全员 | 拍板后的系统架构 | 与代码长期不一致还不改 memory/map |
| `docs/algorithms` | 文档 | 算法团队 / 框架 | 插件接口与接入步骤 | 与 core.base 或 system-design 字段长期不一致 |
| `docs/ai` | 文档 | 全员（AI 改代码时必须跟） | 目录实况、记忆、约定 | 只改代码不改 map |
| `docs/ops` | 文档 | 部署/开发 | 人如何安装、启动、打包 | 把操作步骤只写在 README 一句带过且与脚本不一致 |
| `tests` | 测试 | 框架团队 | 接口、事件、丢帧、标定几何的回归 | 依赖真实海康才能跑的单测（那种放 scripts） |

## 给 AI 的阅读顺序

1. `AGENTS.md`；按需打开 [docs/README.md](../README.md)
2. 本表定位目录
3. `docs/ai/memory.md` 看已拍板例外
4. 对应代码
