# docs/ai — 给 AI 与人共用的活文档

改代码时**同时改这里**，不要只把决策留在对话里。

| 文件 | 谁维护 | 内容 |
|------|--------|------|
| [architecture-map.md](architecture-map.md) | 改目录/模块职责时必须更新 | 路径 → 功能 → 谁能改。由 `docs/ai/module-map.yaml` 生成实况表 |
| [module-map.yaml](module-map.yaml) | 增删目录时先改这份 | 架构信息源。`python scripts/sync_architecture_map.py` 校验并回写 map |
| [memory.md](memory.md) | 用户拍板或踩坑后追加 | 跨会话记忆：决策、禁忌、未决项 |
| [conventions.md](conventions.md) | 约定变化时更新 | 接口、命名、延迟、上报 |

## AI 工作顺序

1. 读 `AGENTS.md`（仓库根）
2. 涉及架构/新模块：读 `docs/architecture/system-design.md` + `memory.md`
3. 改哪个目录：先看 `architecture-map.md` 里该路径的「职责 / 禁止」
4. 改完若动了边界：更新 `module-map.yaml` 并运行 `python scripts/sync_architecture_map.py`
5. 新的已拍板决策：追加 `memory.md`（日期 + 一句话 + 影响范围）

## 人怎么用

- 找「这个文件夹干什么」：看 architecture-map
- 找「上次为什么这么定」：看 memory
- 找「系统整体怎么跑」：看 system-design，不要只看对话记录
