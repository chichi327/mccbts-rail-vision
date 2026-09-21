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

- 决策：现场交付是一份 `*-field.tgz`：开发机 `bash scripts/package.sh`，服务器解压后 `./start.sh`。包内带算法镜像与 MediaMTX 镜像；host 网络；`.env` 不进包。
- 范围：`scripts/package.sh`、`deploy/field/`、`docs/ops/packaging.md`。
- 例外：相机 RTSP、标定、后端 URL 仍须在现场改 `config/` 与 `.env`。无 GPU 用 `./start.sh --cpu`。Docker Hub 不通时 `package.sh` 用 `PYTHON_IMAGE` / 自动 DaoCloud 镜像拉基础层。

- 决策：`docs/README.md` 是文档总索引；新增或搬迁 `docs/**/*.md` 必须写入该索引。`python scripts/sync_architecture_map.py` 校验链接。
- 范围：`docs/`、`scripts/sync_architecture_map.py`、`.cursor/rules` 与文档同步 skill。
- 例外：自动生成的 `docs/ai/architecture-map.md` 仍只由脚本改写，但必须出现在索引里。

- 决策：整体按 `docs/architecture/system-design.md` 落地；四算法两条 DAG；供应商标定由框架加载。
- 决策：端到端延迟 **< 300ms**（覆盖原先「1s 即可」的默认建议）。
- 决策：算法直拉主码流；MediaMTX 仅预览。
- 决策（修订）：现场 MediaMTX 与算法同机作拉流中转（透传）；ingest 对本机 RTSP 重连。工位海康与现场海康同一套接法。同事反馈：海康断网再联网直连有概率无法恢复。
- 决策：距离 = 脚点/车底中心到最近钢轨的水平距离；默认预警 2.0m、危险 1.0m。
- 决策：上报事件化 + 心跳；人车必须跟踪。
- 范围：框架 `core/`、插件 `algorithms/`、配置 `config/`。
- 例外：后端正式 URL / token、供应商标定精度、工务最终阈值待对接后只改配置。
- 决策：主进程预览 `http://127.0.0.1:8081/preview`。
- 决策（修订）：取消 `source: webcam`。本机 USB 经 FFmpeg → MediaMTX publisher → ingest 只拉 `127.0.0.1:8554`，与现场同一条 Python 链路。`bash scripts/start.sh --webcam`。合成源仅单测（`cameras.synthetic.yaml`）。
- 决策：预览卡顿因整帧经 Manager/Queue pickle；改为 SharedMemory 传帧，检测结果走小 Queue。
- 决策：心跳必须能区分相机断流、人车/障碍物流水线崩溃、标定失效；与「没人」无关。故障打 `HEALTH_FAULT`，恢复打 `HEALTH_RECOVER`。一条流水线退出不拉停另一条。
- 范围：`core/health`、心跳 JSON、`GET /health`、ingest/pipeline 日志。
- 例外：后端如何展示这些字段仍待对接。

## 2026-09-21

- 决策：去掉 USB webcam 与合成源。ingest 只保留 `source: rtsp`（本机 MediaMTX）。无 `start.sh --webcam`、无 `cameras.synthetic.yaml`。
- 范围：`core/ingest/sources.py`、`scripts/start.sh`、删除 `config/mediamtx.webcam.yml`、`scripts/publish_webcam.sh`、`config/cameras.synthetic.yaml`；文档入口与约定。
- 例外：`pytest` 不连海康；真码流验证用 MediaMTX + `main.py`。6 路模板仍是 `cameras.rtsp.example.yaml`。

- 决策：可选耗时埋点，默认关。`config/system.yaml` 的 `timing.enabled` / `log_every_n`；环境变量 `TIMING_ENABLED` 可覆盖。日志前缀 `timing`（ingest 的 read/undistort/write；流水线的 detect/track/estimate/total/e2e）。`e2e_ms` 从 ingest 打戳到本帧处理完，不含海康编码。现场关闭以免刷日志。
- 范围：`core/runtime/timing.py`、`pipeline.py`、`core/ingest/loop.py`、`main.py`、`config/system.yaml`、`.env.example`。
- 例外：不写入事件 JSON；预览编码不计入这条埋点。

- 现象（工位 timing）：`undistort_ms≈96`，流水线 `age_ms`/`e2e_ms≈110`，假检测 `detect_ms≈0`。根因是每帧 `getOptimalNewCameraMatrix` + `cv2.undistort` 重建 1080p 映射表，不是算法慢。
- 决策：按相机目录和分辨率缓存 `initUndistortRectifyMap`（`CV_16SC2`），每帧 `cv2.remap`。GPU remap 仍待（常见 OpenCV wheel 无 CUDA）。
- 范围：`core/ingest/undistort.py`；约定禁止再走每帧 `undistort`。
- 例外：标定无效则跳过，原图进流水线。
