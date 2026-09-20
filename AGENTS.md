# AGENTS.md

本仓库给 Cursor / 其他编码 Agent 的入口。人请从 [README.md](README.md) 和 [docs/ops/getting-started.md](docs/ops/getting-started.md) 开始。

## 必读

1. [docs/architecture/system-design.md](docs/architecture/system-design.md) — 拍板架构（延迟 <300ms、两条 DAG）
2. [docs/ai/architecture-map.md](docs/ai/architecture-map.md) — 目录 → 功能（以 [module-map.yaml](docs/ai/module-map.yaml) 为源）
3. [docs/ai/memory.md](docs/ai/memory.md) — 跨会话已拍板决策
4. [docs/ai/conventions.md](docs/ai/conventions.md) — 接口与禁忌

## 改代码后必须做

结构、职责、启动方式、配置项、对外接口任一变化：

1. 更新 `docs/ai/module-map.yaml`（若增删路径）
2. 运行 `python scripts/sync_architecture_map.py`
3. 操作步骤变化则改 `docs/ops/`
4. 用户新拍板则追加 `docs/ai/memory.md`
5. 模块边界变化则改 `docs/architecture/system-design.md` 对应节，不要让文档撒谎

详细流程见 [docs/ai/README.md](docs/ai/README.md) 与 `.cursor/skills/update-project-docs/SKILL.md`。
