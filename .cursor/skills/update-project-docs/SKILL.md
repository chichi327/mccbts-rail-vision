---
name: update-project-docs
description: >-
  在改动目录结构、模块职责、启动打包、配置项或对外接口后，同步本仓库文档与 AI 记忆。
  当用户或代理增删 core/algorithms/config/docs 路径、改 main.py 启动方式、改 Docker/脚本时使用。
---

# 同步项目文档

## 何时用

代码或脚本已经（或即将）改变「文件夹干什么 / 人怎么启动 / 接口长什么样」。

## 步骤

1. 对照 `docs/ai/module-map.yaml`：有新路径就加一条（path, role, owner, purpose, forbidden）；删了就去掉。
2. 运行 `python scripts/sync_architecture_map.py`（校验路径存在并重写 `docs/ai/architecture-map.md`）。
3. 启动、安装、Docker、环境变量变化 → 更新 `docs/ops/getting-started.md` 或 `packaging.md` 或 `configuration.md`，并核对根 `README.md` 链接。
4. 检测器/量测器接口或事件 JSON 变化 → `docs/algorithms/plugin-guide.md` + `docs/architecture/system-design.md` 第 6/8 节。
5. 用户确认的新决策 → 追加 `docs/ai/memory.md`（日期、决策、范围、例外）。

不要新建平行的「另一套架构说明」。活人文档与 AI 文档共用上述路径。
