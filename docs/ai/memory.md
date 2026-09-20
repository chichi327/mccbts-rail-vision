# 项目记忆

跨会话保留的已拍板事项。只追加事实，不写过程流水账。

格式：

```
## YYYY-MM-DD
- 决策：...
- 范围：...
- 例外：...
```

## 2026-09-20

- 决策：`docs/README.md` 是文档总索引；新增或搬迁 `docs/**/*.md` 必须写入该索引。`python scripts/sync_architecture_map.py` 校验链接。
- 范围：`docs/`、`scripts/sync_architecture_map.py`、`.cursor/rules` 与文档同步 skill。
- 例外：自动生成的 `docs/ai/architecture-map.md` 仍只由脚本改写，但必须出现在索引里。

- 决策：整体按 `docs/architecture/system-design.md` 落地；四算法两条 DAG；供应商标定由框架加载。
- 决策：端到端延迟 **< 300ms**（覆盖原先「1s 即可」的默认建议）。
- 决策：算法直拉主码流；MediaMTX 仅预览。
- 决策：距离 = 脚点/车底中心到最近钢轨的水平距离；默认预警 2.0m、危险 1.0m。
- 决策：上报事件化 + 心跳；人车必须跟踪。
- 范围：框架 `core/`、插件 `algorithms/`、配置 `config/`。
- 例外：后端正式 URL / token、供应商标定精度、工务最终阈值待对接后只改配置。
- 决策：本机可用 `source: webcam`；主进程预览 `http://127.0.0.1:8081/preview`。
- 决策：预览卡顿因整帧经 Manager/Queue pickle；改为 SharedMemory 传帧，检测结果走小 Queue。
