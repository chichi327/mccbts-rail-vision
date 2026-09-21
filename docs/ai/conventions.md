# 工程约定

## 延迟

- 事件链路端到端 **< 300ms**（采集完成 → HTTP 请求已发出）
- 帧年龄 `> drop_if_frame_age_ms`（默认 200）必须丢弃
- 耗时埋点默认关（`system.timing.enabled` / `TIMING_ENABLED`）；打开后打 `timing` 日志，现场保持关闭
- 算法只拉 **同机 MediaMTX 透传** 地址；禁止经 MediaMTX **转码**或默认大缓冲当算法源
- ingest 只有 `source: rtsp`（本机 MediaMTX）；禁止 webcam / synthetic / 直连海康
- 禁止用加长队列「扛延迟」
- 去畸变必须缓存 `initUndistortRectifyMap`，每帧只 `remap`；禁止每帧 `cv2.undistort` 重建映射表

## 算法插件

- 检测器只出框；量测器只补 `distance_to_track_m` 或 `height_m`
- 人车不是障碍物
- 量测不得自己再检一套框
- 禁止四个插件无依赖并行后靠 IoU 对框
- 结果类型只用 `core.base.types.Detection`，禁止自造距离/高度字段名

## 进程与异步

- 推理在流水线进程内同步调用；asyncio 仅用于上报/预览 HTTP
- 一条 DAG 流水线一个进程；链内检测 → 跟踪 → 量测串行
- 模型实例不要跨进程共享

## 标定

- 只允许 `core.calib` 解析供应商文件
- 算法通过 `CalibView` 拿几何
- 几何基于去畸变图

## 上报

- 主通道是**状态变化事件**，不是逐帧全量
- 心跳走独立 URL
- 心跳区分断流 / 流水线挂 / 标定失效，禁止把「没检出目标」当成系统故障
- Reporter 失败入本地队列，不阻塞推理

## 文档

- 查找入口以 `docs/README.md` 为准；新增 `docs/**/*.md` 必须写入该索引
- 目录职责以 `docs/ai/module-map.yaml` 为准
- 架构对错以 `docs/architecture/system-design.md` 为准
- 启动打包以 `docs/ops/` 为准
