# 文档索引

人和 AI 都从这里按需打开文档。**不要通读整棵 `docs/`。**

新增或搬迁 `docs/` 下的说明文件时，必须在本页加一行；`python scripts/sync_architecture_map.py` 会检查每个 `docs/**/*.md`（本文件除外）是否被本页链接。

仓库根：[README.md](../README.md)（人）· [AGENTS.md](../AGENTS.md)（AI 入口）

## 按意图查找

| 我想… | 打开 |
|--------|------|
| 安装、启动 | [ops/getting-started.md](ops/getting-started.md) |
| 后续要逐项确认的事 | [ops/follow-up-checklist.md](ops/follow-up-checklist.md) |
| 手头摄像头验证架构通路 | [ops/verify-with-camera.md](ops/verify-with-camera.md) |
| MediaMTX 拉流中转、断网恢复 | [ops/mediamtx.md](ops/mediamtx.md) |
| Docker / 现场打包 | [ops/packaging.md](ops/packaging.md) |
| 相机、标定、`.env`、YAML | [ops/configuration.md](ops/configuration.md) |
| 给标定供应商：去畸变怎么做、交哪些文件 | [ops/calibration-vendor.md](ops/calibration-vendor.md) |
| 系统怎么拆、延迟预算、两条 DAG | [architecture/system-design.md](architecture/system-design.md) |
| 这个目录谁维护、禁止做什么 | [ai/architecture-map.md](ai/architecture-map.md)（源：[ai/module-map.yaml](ai/module-map.yaml)） |
| 上次拍板了什么、有哪些例外 | [ai/memory.md](ai/memory.md) |
| 接口、命名、上报、文档以谁为准 | [ai/conventions.md](ai/conventions.md) |
| AI 改代码时文档怎么跟 | [ai/README.md](ai/README.md) |
| 算法团队怎么接检测器/量测器 | [algorithms/plugin-guide.md](algorithms/plugin-guide.md) |

## 按目录

### `docs/architecture/` — 拍板架构

| 文件 | 读者 | 内容 |
|------|------|------|
| [system-design.md](architecture/system-design.md) | 全员 | 延迟 <300ms、两条流水线、标定、上报；改模块边界以本文为准 |

### `docs/ops/` — 人怎么跑

| 文件 | 读者 | 内容 |
|------|------|------|
| [getting-started.md](ops/getting-started.md) | 开发/部署 | 安装、启动、健康检查 |
| [follow-up-checklist.md](ops/follow-up-checklist.md) | 项目负责人 | 后端/相机/标定/业务/算法团队待确认项 |
| [verify-with-camera.md](ops/verify-with-camera.md) | 开发 | 海康经 MediaMTX 验证拉流与流水线 |
| [mediamtx.md](ops/mediamtx.md) | 部署 | 同机中转、透传、断网验收 |
| [configuration.md](ops/configuration.md) | 开发/部署 | YAML、标定目录、密钥 |
| [calibration-vendor.md](ops/calibration-vendor.md) | 标定供应商 | 去畸变 OpenCV 步骤、文件格式、还须交付什么 |
| [packaging.md](ops/packaging.md) | 部署 | `package.sh` 打 field 包、现场 `./start.sh` |

### `docs/algorithms/` — 插件

| 文件 | 读者 | 内容 |
|------|------|------|
| [plugin-guide.md](algorithms/plugin-guide.md) | 算法团队 | `BaseDetector` / `BaseEstimator`、类别与物理量字段 |

### `docs/ai/` — 目录实况与跨会话记忆

| 文件 | 读者 | 内容 |
|------|------|------|
| [README.md](ai/README.md) | AI / 人 | AI 工作顺序、人怎么查 map/memory |
| [module-map.yaml](ai/module-map.yaml) | 改目录时先改 | 路径 → 职责/禁止；信息源 |
| [architecture-map.md](ai/architecture-map.md) | 全员 | 上表生成稿，勿手改 |
| [memory.md](ai/memory.md) | 全员 | 已拍板决策，只追加 |
| [conventions.md](ai/conventions.md) | 写代码时 | 延迟、插件、进程、标定、上报禁忌 |

## 维护规则

1. 新文档放进对应子目录（架构 / 操作 / 算法插件 / AI 活文档），不要在仓库根再开一套说明。
2. 在本索引「按意图查找」和「按目录」各加一行（意图表按常见查询；目录表按文件）。
3. 若增删的是代码目录而不是文档文件，改 [ai/module-map.yaml](ai/module-map.yaml) 并跑同步脚本；不要只改本索引假装目录还在。
4. `architecture-map.md` 由脚本生成，不在本索引手写职责表。
