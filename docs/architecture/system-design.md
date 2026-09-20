# 铁路视觉算法服务 — 架构方案

本文是**架构拍板文档**（由 `info.md` 更名迁入）。搭框架、加算法、改模块边界时以本文为准。

| 读者 | 先看 |
|------|------|
| 人/AI · 文档目录 | [docs/README.md](../README.md) |
| 人 · 启动/打包 | [docs/ops/getting-started.md](../ops/getting-started.md)、[docs/ops/packaging.md](../ops/packaging.md) |
| 人 · 配置/标定 | [docs/ops/configuration.md](../ops/configuration.md) |
| 人/AI · 目录实况 | [docs/ai/architecture-map.md](../ai/architecture-map.md) |
| AI · 约定与记忆 | [docs/ai/README.md](../ai/README.md)、[docs/ai/memory.md](../ai/memory.md) |
| 算法团队 | [docs/algorithms/plugin-guide.md](../algorithms/plugin-guide.md) |

四个算法分团队开发，框架负责拉流、标定、调度、跟踪、事件上报。端到端延迟（成像完成 → 结果到达现有后端）按 **< 300ms** 约束。

---

## 0. 已拍板决策

| 项 | 决策 |
|----|------|
| 算法关系 | 两条流水线，允许依赖：人车检测 → 铁轨测距；障碍物检测 → 高度估计 |
| 测距 / 高度 | 不重复检测。测距用人车框，高度用障碍物框 |
| 人车 vs 障碍物 | 两套模型、两个团队。人车不算障碍物，避免重复告警 |
| 标定 | 供应商按相机交付；框架统一去畸变；单应/外参必须基于去畸变图 |
| 高度可行性 | 单目 + 完整外参（含相机高度/俯仰），不只靠单应。供应商须书面确认精度 |
| 重标定 | 安装后一次；挪机/撞击后重标；运行中做轨面一致性体检 |
| 容量基线 | 1 张 GPU 接 4～8 路；算法吃主码流 1080p；检测 5～10 fps |
| 延迟 | **< 300ms**（见第 3 节预算） |
| 调度 | 检测按帧率跑；测距/高度只对检出目标计算 |
| 上报 | 算法服务 HTTP POST 推事件；失败重试 + 短时本地缓存 |
| 心跳 | 相机在线、算法存活、标定是否有效，与事件分通道 |
| 团队交付 | 同一仓库、四个算法目录；运行时按流水线进程隔离 |
| 预览 | 内网叠框预览给验收/调试；后端只收结构化 JSON |
| 距离定义 | 人脚点 / 车底中心到**最近钢轨**的水平距离 |
| 阈值默认 | 预警 2.0m，危险 1.0m（可配置，待工务确认后改配置不改代码） |
| 跟踪 | 人/车必须有短时 ID；障碍物做出现/持续/消失 |

---

## 1. 系统要做什么

在算法服务器上：

1. 接入海康摄像头主码流
2. 跑四类算法：人员/车辆识别、人/车到铁轨距离、障碍物识别、障碍物高度
3. 把**事件化结果**推到现有后端（接口由后端提供）
4. 提供内网预览，供现场验收和排障

不在本系统范围内：后端业务库、告警推送用户、摄像头安装施工。标定由供应商交付文件，本系统加载使用。

---

## 2. 整体架构

```
                    海康摄像头（多路，现场默认 6 路）
                           │ 每台主码流只被拉一次
                           ▼
              ┌─────────────────────────────┐
              │ MediaMTX（与算法同机）        │
              │ 透传、小队列、对海康重连       │
              │ 本机 rtsp://127.0.0.1:8554/id │
              └──────────┬──────────────────┘
                         │
           ┌─────────────┴──────────────┐
           ▼                            ▼
┌─────────────────┐            子码流 path（按需）
│ 接入层 Ingest    │            → WebRTC / 8081 叠框
│ 对本机 RTSP 重连  │              （不在 300ms 链路上）
│ NVDEC / OpenCV   │
│ 去畸变、最新帧    │
└────────┬────────┘
                 │ 共享内存帧 + camera_id + 采集时间戳 + 该路标定句柄
                 │
        ┌────────┴─────────────────────────┐
        ▼                                  ▼
┌───────────────────────┐      ┌───────────────────────┐
│ 流水线 A（独立进程）    │      │ 流水线 B（独立进程）    │
│ 人员车辆检测           │      │ 障碍物检测             │
│    → 多目标跟踪        │      │    → 障碍物跟踪        │
│    → 铁轨测距          │      │    → 高度估计          │
└───────────┬───────────┘      └───────────┬───────────┘
            │                                │
            └────────────┬───────────────────┘
                         ▼
              ┌─────────────────────┐
              │ 事件层 Eventer      │
              │ 进出预警/危险区      │
              │ 障碍物出现/消失      │
              │ 心跳与标定体检       │
              └──────────┬──────────┘
                         ▼
              ┌─────────────────────┐
              │ 上报适配 Reporter    │
              │ HTTP POST 现有后端   │
              │ 超时、重试、本地队列  │
              └─────────────────────┘
```

要点：

- **MediaMTX 与算法同机，作拉流中转。** 海康断网再联网时由中转重建会话；算法只拉 `127.0.0.1`。必须透传、禁止转码，`writeQueueSize` 保持较小并压测 300ms。
- **ingest 仍要对本机 RTSP 重连。** 中转空窗时不得握死旧 `VideoCapture`。
- **一次解码，两条流水线共享帧。** 不拉四路流，不解码四次。
- **四个算法仍是四个插件目录**，但运行时按 DAG 组成两条链，不靠事后 IoU 猜是不是同一个目标。
- **测距、高度是量测器，不是检测器。** 输入里必须带上游检出的目标和标定。
- **真实画面一律进 MediaMTX，ingest 只拉本机 RTSP。** 海康由中转拉取；本机 USB 由 FFmpeg 推入（`scripts/start.sh --webcam`）。`source: synthetic` 仅单测。禁止 `source: webcam` 直采。

---

## 3. 延迟预算（< 300ms）

从「该帧在相机侧编码完成」到「后端收到事件 HTTP 请求」严格小于 300ms。预览不计入这条链路。

| 环节 | 预算 | 做法 |
|------|------|------|
| RTSP 收流 + 缓冲 | 40ms | FFmpeg `nobuffer` / `low_delay` / 小 `probesize`；禁止累积队列 |
| NVDEC + 颜色转换 | 25ms | 硬解到 GPU，尽量零拷贝 |
| 去畸变 | 10ms | 框架统一做，GPU remap |
| 检测（人车或障碍物） | 80ms | TensorRT / 量化优先；1080p 可 ROI |
| 跟踪 + 量测（距离或高度） | 20ms | 几何计算为主；高度若是小网络也必须吃检测框，禁止再跑一遍检测 |
| 事件判定 | 5ms | 内存态，无磁盘 |
| HTTP 发出 | 30ms | 事件立即 POST，不等待批量窗口；发送失败入本地队列，不阻塞下一帧 |
| 余量 | 90ms | GPU 争用、偶发抖动 |
| **合计** | **300ms** | |

配套硬规则：

1. **只处理最新帧。** 环形缓冲深度 = 1～2。解码快于推理时丢旧帧，绝不让队列把延迟堆上去。
2. **带采集时间戳。** 推理开始前若 `now - capture_ts > 200ms`，该帧直接丢，记过期计数。
3. **两条流水线并行。** 人车链和障碍物链同时跑；链内检测 → 跟踪 → 量测必须串行（量测依赖框）。
4. **上报异步。** `await` 后端不能拖住推理循环；300ms 统计点是「请求已发出」（本网时延通常远小于 30ms）。
5. **MediaMTX 必须透传、小队列。** 禁止用默认大缓冲/转码当算法源；延迟超标先减 `writeQueueSize` 或查 GOP，而不是加长 ingest 队列。

若压测单路检测就 > 80ms：先降推理分辨率/加 ROI/上 TensorRT，而不是加大缓冲。

---

## 4. 模块划分

```
┌──────────────────────────────────────────────────────────┐
│ core/  框架（算法团队只读，不改）                            │
│  ingest     拉流、硬解、去畸变、共享内存帧总线                 │
│  calib      加载供应商文件、按 camera_id 提供几何能力         │
│  runtime    DAG 调度、进程管理、过期丢帧                      │
│  track      人车 ByteTrack 类跟踪；障碍物短时关联             │
│  event      阈值判定、去重、事件状态机                        │
│  report     HTTP 适配现有后端、重试队列                       │
│  preview    叠框预览（旁路）                                  │
│  health     相机/进程/标定心跳                                │
└──────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│ algorithms/  四个插件（各团队自己的目录）                      │
│  person_vehicle_detect   检测器                               │
│  track_distance          量测器（依赖人车检测）                │
│  obstacle_detect         检测器                               │
│  obstacle_height         量测器（依赖障碍物检测）              │
└──────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│ config/  相机、算法开关、系统、标定文件                        │
└──────────────────────────────────────────────────────────┘
```

| 模块 | 职责 | 不做什么 |
|------|------|----------|
| ingest | 稳定出帧；断流重连；打时间戳 | 不跑模型、不理解业务阈值 |
| calib | 统一几何：去畸变、像素↔地面、到轨距离、框估高 | 不在算法里解析 npz |
| runtime | 按 DAG 调插件；进程隔离；丢过期帧 | 不写死某个模型 |
| 检测插件 | 只出框 + 类别 + 置信度 | 不算距离/高度，不上报 |
| 量测插件 | 只给已有目标补 `distance_to_track_m` 或 `height_m` | 不自己重新检出目标 |
| track | 跨帧 ID | 不改检测类别 |
| event | 进出区、出现消失 | 不直接调模型 |
| report | 协议适配、鉴权、重试 | 不改算法语义 |

---

## 5. 四个算法如何解耦

开发时解耦，运行时允许依赖。

```
人员车辆检测团队          铁轨测距团队
     │                        │
     │  Detection[]            │  读 bbox + calib
     └──────────►─────────────┘
              流水线 A 进程内调用

障碍物检测团队            高度估计团队
     │                        │
     │  Detection[]            │  读 bbox + calib
     └──────────►─────────────┘
              流水线 B 进程内调用
```

| 团队 | 类型 | 输入 | 输出 |
|------|------|------|------|
| 人员车辆检测 | 检测器 | 已去畸变帧 | person / car / truck 的 bbox |
| 铁轨测距 | 量测器 | 同一帧 + 人车 detections + 该路标定 | 每个目标的 `distance_to_track_m` |
| 障碍物检测 | 检测器 | 已去畸变帧 | obstacle 的 bbox（不含人车） |
| 障碍物高度 | 量测器 | 同一帧 + 障碍物 detections + 该路标定 | 每个目标的 `height_m` |

注册用配置，不改 `core/`：

```yaml
pipelines:
  - id: person_vehicle
    steps:
      - person_vehicle_detect
      - track_distance          # depends_on: person_vehicle_detect
  - id: obstacle
    steps:
      - obstacle_detect
      - obstacle_height         # depends_on: obstacle_detect
```

新增算法 = 新目录 + 声明类型（detector / estimator）和 `depends_on`。禁止四个插件无依赖并行后再用 IoU 对框。

进程隔离粒度：一条流水线一个进程。某团队模型把进程打崩，只影响该链；另一条链和接入层继续跑。插件之间用进程内函数调用（同一帧上检测完立刻量测），避免 HTTP/RPC 再吃几十毫秒。

---

## 6. 核心接口（算法团队必须遵守）

### 6.1 统一结果，禁止自由 dict

```python
from dataclasses import dataclass, field
from typing import Literal, Optional, List

ObjectType = Literal["person", "car", "truck", "obstacle"]

@dataclass
class Detection:
    object_id: str                    # 跟踪前可空，跟踪后必填
    type: ObjectType
    confidence: float
    bbox_xyxy: List[float]            # 去畸变图上的像素坐标 [x1,y1,x2,y2]
    distance_to_track_m: Optional[float] = None
    height_m: Optional[float] = None
    extra: dict = field(default_factory=dict)  # 仅调试，不上报后端
```

字段名固定。没有的量就 `None`，不要发明 `dist` / `height_cm`。

### 6.2 检测器

```python
class BaseDetector(ABC):
    def load(self, config: dict) -> None: ...
    def infer(self, frame_bgr: np.ndarray, camera_id: str) -> List[Detection]: ...
    def release(self) -> None: ...
```

`frame_bgr` 已去畸变。检测器不读标定，不算物理量。

### 6.3 量测器

```python
class BaseEstimator(ABC):
    def load(self, config: dict) -> None: ...
    def estimate(
        self,
        frame_bgr: np.ndarray,
        camera_id: str,
        detections: List[Detection],
        calib: "CalibView",
    ) -> List[Detection]:
        """原地或返回新列表，补齐 distance_to_track_m 或 height_m。"""
        ...
```

量测器不得丢弃上游目标，不得新增另一套 bbox（除非 `extra` 里写调试信息）。

### 6.4 标定视图（框架提供，算法只调用）

```python
class CalibView(ABC):
    def undistort_points(self, pts): ...
    def pixel_to_ground(self, u: float, v: float) -> tuple[float, float]: ...
    def ground_distance_to_nearest_rail(self, x: float, y: float) -> float: ...
    def bbox_foot_to_rail_distance(self, bbox_xyxy: list[float]) -> float: ...
    def bbox_to_height_m(self, bbox_xyxy: list[float]) -> float: ...
```

测距团队应优先调用 `bbox_foot_to_rail_distance`（人用底边中点，车同样）。高度团队优先调用 `bbox_to_height_m`。若模型要自己算，也必须用同一套外参，禁止再解析供应商文件。

---

## 7. 供应商标定

按**相机**一套文件，放 `config/calib/<camera_id>/`。

| 文件/内容 | 用途 | 是否必须 |
|-----------|------|----------|
| 内参 K、畸变系数 | 去畸变 | 必须 |
| 外参 R、t 或 安装高度 + 俯仰/滚转/偏航 | 像素到三维/高度 | 必须（测高） |
| 轨面/地面单应 H | 像素到地面 | 必须（测距） |
| 两条钢轨或中心线在地面坐标系的几何 | 「到铁轨」的定义 | 必须 |
| 标定时分辨率、已去畸变（必须为是） | 与算法输入对齐 | 必须 |
| 距离/高度误差范围 | 验收 | 必须 |
| 标定日期、供应商、相机序列号 | 追溯 | 必须 |

书面约定：

1. 所有几何量基于**去畸变图像**。
2. 单应只能做地面距离；高度必须有外参或安装高度+姿态，供应商须确认单目高度精度。
3. 相机被挪、被撞、更换镜头后重标。
4. 框架启动时校验文件齐全；缺文件则该相机标为 `calib_invalid`，检测可跑，距离/高度不上报，心跳告警。

运行中体检：若能看到轨面/钢轨，将其与标定轨位置比较，偏差超阈值则 `calib_stale`。

---

## 8. 数据流与上报

### 8.1 一帧在流水线 A 上

```
帧(已去畸变, ts, cam01)
  → 人员车辆检测  → [person bbox...]
  → 跟踪          → 补 object_id
  → 铁轨测距      → 补 distance_to_track_m
  → 事件          → 若穿过 2.0m / 1.0m 则立刻上报
```

### 8.2 上报给后端的事件（主通道）

不是每帧全量框。主通道是事件，可附带当时目标快照。

```json
{
  "camera_id": "cam01",
  "event_id": "uuid",
  "event_type": "person_enter_warning",
  "timestamp_ms": 1726800000123,
  "capture_ts_ms": 1726800000000,
  "object": {
    "object_id": "cam01-p-17",
    "type": "person",
    "confidence": 0.92,
    "bbox": [100, 200, 150, 350],
    "distance_to_track_m": 1.6,
    "height_m": null,
    "alert_level": "warning"
  }
}
```

`event_type` 建议集合：

- `person_enter_warning` / `person_enter_danger` / `person_leave_warning`
- `vehicle_enter_warning` / `vehicle_enter_danger` / `vehicle_leave_warning`
- `obstacle_appeared` / `obstacle_cleared`
- 对应障碍物高度超限若有阈值，另加 `obstacle_height_alert`

`alert_level`：`none` | `warning` | `danger`（距离 ≤ 2.0m 预警，≤ 1.0m 危险）。

同一 `object_id` 在同一状态不要每帧重复 POST。状态变化才发。这与 300ms 不冲突：状态变化的那一帧仍必须在 300ms 内发出。

### 8.3 心跳（独立通道，1～5s 一次即可）

心跳用来区分「画面里没人」和「系统挂了」。没有行人时事件不发、心跳仍应 `camera_online=true` 且两条流水线 `*_alive=true`。

```json
{
  "camera_id": "cam01",
  "ts_ms": 1726800005000,
  "camera_online": true,
  "pipeline_person_alive": true,
  "pipeline_obstacle_alive": true,
  "calib_status": "ok",
  "last_frame_age_ms": 80,
  "dropped_stale_frames": 3,
  "issues": [],
  "calib_reason": ""
}
```

| 现象 | 怎么看心跳 | 日志关键字 |
|------|-------------|------------|
| 相机断流 / ingest 停更 | `camera_online=false`，`issues` 含 `camera_offline`，`last_frame_age_ms` 变大 | `HEALTH_FAULT` + `issue=camera_offline`；RTSP 另有 `rtsp reconnect` |
| 人车流水线进程退出 | `pipeline_person_alive=false`，`issues` 含 `pipeline_person_dead` | `HEALTH_FAULT` + `issue=pipeline_person_dead` |
| 障碍物流水线进程退出 | `pipeline_obstacle_alive=false`，`issues` 含 `pipeline_obstacle_dead` | 同上，`pipeline_obstacle_dead` |
| 标定缺文件或无效 | `calib_status=invalid`，`calib_reason` 有原因，`issues` 含 `calib_invalid` | `HEALTH_FAULT` + `issue=calib_invalid` |
| 画面无人/无障碍物 | 上述字段仍为正常；只是没有 `person_enter_*` / `obstacle_appeared` | 无 `HEALTH_FAULT` |

`calib_status`：`ok` | `invalid` | `stale`。恢复时打 `HEALTH_RECOVER`。异常持续期间每个心跳周期打一条 `HEALTH_STATUS`（含 `issues=`）。本地 `GET /health` 的 `heartbeats` 与上报字段相同，`status` 在有 `issues` 时为 `degraded`。

`camera_online`：该路共享内存最新帧时间戳距现在超过 `system.camera_offline_after_ms`（默认 3000）则视为断流。一条流水线挂掉**不**再拉停另一条，心跳继续上报，便于对照。上报进程自己退出才整机停。

### 8.4 Reporter

- 现有后端 URL、token 走配置
- POST 超时建议 100ms，失败写入本地有界队列（例如 1000 条），后台重试
- 重试不得阻塞推理
- 鉴权、字段映射集中在 Reporter，算法不知道后端长什么样

---

## 9. 目录结构

```
mccbts-rail-vision/
├── AGENTS.md                        # 所有 AI 的入口
├── README.md
├── pyproject.toml
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .cursor/rules/                   # Cursor 持久规则
├── .cursor/skills/                  # 改结构后同步文档的 skill
├── docs/
│   ├── architecture/system-design.md  # 本文
│   ├── ai/                          # AI 记忆、目录实况、约定
│   ├── ops/                         # 人类操作：启动、打包、配置
│   └── algorithms/plugin-guide.md
├── config/
│   ├── cameras.yaml
│   ├── cameras.rtsp.example.yaml    # 现场 6 路 + 本机中转地址
│   ├── mediamtx.yml                 # 同机拉流中转（透传）
│   ├── algorithms.yaml
│   ├── pipelines.yaml
│   ├── system.yaml
│   └── calib/
│       └── cam01/
│           ├── camera.npz          # K, dist
│           ├── extrinsics.npz      # R, t 或 height+rpy
│           ├── homography.npz
│           ├── rails.yaml          # 地面系钢轨几何
│           └── meta.yaml           # 分辨率、是否去畸变、日期、误差
├── core/
│   ├── ingest/                     # 拉流、NVDEC、去畸变、shm 帧总线
│   ├── calib/                      # CalibStore / CalibView
│   ├── runtime/                    # 进程、DAG、丢帧
│   ├── track/
│   ├── event/
│   ├── report/
│   ├── preview/
│   ├── health/
│   └── base/
│       ├── detector.py
│       ├── estimator.py
│       └── types.py
├── algorithms/
│   ├── person_vehicle_detect/
│   │   ├── detector.py
│   │   ├── config.yaml
│   │   └── models/
│   ├── track_distance/
│   │   ├── estimator.py
│   │   └── config.yaml
│   ├── obstacle_detect/
│   │   ├── detector.py
│   │   ├── config.yaml
│   │   └── models/
│   └── obstacle_height/
│       ├── estimator.py
│       ├── config.yaml
│       └── models/
├── services/
│   ├── preview_server.py
│   └── health_check.py
├── main.py
└── scripts/
    ├── start.sh
    └── test_single_camera.py
```

各算法目录可内含自己的 `requirements-algo.txt`，流水线进程按该文件建环境。接口和结果类型必须用 `core.base`。

---

## 10. 配置示例

### `config/cameras.yaml`

```yaml
cameras:
  - id: cam01
    name: 北侧铁轨-1号机
    source: rtsp
    rtsp_camera: rtsp://user:pass@192.168.1.64:554/Streaming/Channels/101
    rtsp_main: rtsp://127.0.0.1:8554/cam01
    width: 1920
    height: 1080
    target_fps: 10
    calib_dir: config/calib/cam01
```

ingest 只用 `rtsp_main`（本机中转）。海康真实地址写在 `config/mediamtx.yml` 对应 path 的 `source`（可与 `rtsp_camera` 保持一致便于对照）。完整 6 路见 `config/cameras.rtsp.example.yaml`。

### `config/algorithms.yaml`

```yaml
algorithms:
  person_vehicle_detect:
    enabled: true
    kind: detector
    module: algorithms.person_vehicle_detect.detector
    class: PersonVehicleDetector
    config:
      model_path: algorithms/person_vehicle_detect/models/yolov8n.pt
      class_names: {0: person, 2: car, 7: truck}

  track_distance:
    enabled: true
    kind: estimator
    depends_on: [person_vehicle_detect]
    module: algorithms.track_distance.estimator
    class: TrackDistanceEstimator
    config:
      foot_point: bbox_bottom_center

  obstacle_detect:
    enabled: true
    kind: detector
    module: algorithms.obstacle_detect.detector
    class: ObstacleDetector
    config:
      model_path: algorithms/obstacle_detect/models/obstacle.pt
      conf_threshold: 0.5

  obstacle_height:
    enabled: true
    kind: estimator
    depends_on: [obstacle_detect]
    module: algorithms.obstacle_height.estimator
    class: ObstacleHeightEstimator
    config: {}
```

### `config/system.yaml`

```yaml
system:
  gpu_id: 0
  max_e2e_ms: 300
  drop_if_frame_age_ms: 200
  heartbeat_interval_s: 5
  camera_offline_after_ms: 3000
  frame_slot_depth: 2
  warning_distance_m: 2.0
  danger_distance_m: 1.0
  backend:
    events_url: http://backend/api/vision/events
    heartbeat_url: http://backend/api/vision/heartbeat
    token: "xxx"
    post_timeout_ms: 100
  preview:
    enabled: true
    mediamtx_addr: 127.0.0.1:8889
```

---

## 11. 运行时与多路相机

- 每路相机：一个 ingest 循环（线程或轻进程）+ 共享该路最新帧。
- 流水线进程可按 GPU 能力选择：每路一条，或一路进程内按相机串行（串行时更要丢旧帧）。
- 所有相机**不得共享非线程安全的模型实例**。一进程一模型，或加锁且接受延迟变差。
- 标定按 `camera_id` 注入，禁止启动时 `calib=None`。
- asyncio 只用于 Reporter/预览 HTTP；解码和推理走线程/进程，不把 GPU 推理 await 进事件循环。

建议启动拓扑（单 GPU、4～8 路）：

```
main
 ├── ingest × N cameras
 ├── pipeline-person  （加载检测1 + 测距，多路轮询最新帧）
 ├── pipeline-obstacle（加载检测2 + 高度）
 ├── event+report
 └── preview（可选）
```

---

## 12. 预览、健康、部署

**预览：** 叠框走进程内 `http://127.0.0.1:8081/preview`（旁路）。MediaMTX WebRTC（8889）可给人看子码流，不计入 300ms。

**健康：** 进程心跳、RTSP 重连日志、过期丢帧率、标定状态。心跳字段区分断流 / 流水线挂 / 标定失效（见 8.3）。丢帧率持续高说明 300ms 预算不够，要降负载而不是加队列。

**部署：** 算法服务器上 **MediaMTX 与 rail-vision 同机**。现场交付 `bash scripts/package.sh` 打出的 `*-field.tgz`，解压后 `./start.sh`（host 网络）。现有后端独立。

---

## 13. 各团队交付清单

| 角色 | 交付 |
|------|------|
| 框架 | ingest、calib、runtime、track、event、report、预览、配置 schema、接口包 |
| 人员车辆团队 | `algorithms/person_vehicle_detect`，实现 `BaseDetector` |
| 测距团队 | `algorithms/track_distance`，实现 `BaseEstimator`，用人车框 + `CalibView` |
| 障碍物团队 | `algorithms/obstacle_detect`，实现 `BaseDetector`，类别不含人车 |
| 高度团队 | `algorithms/obstacle_height`，实现 `BaseEstimator` |
| 供应商 | 第 7 节文件 + 误差说明 + 去畸变图约定 |
| 后端 | events / heartbeat 接口、鉴权、幂等（按 `event_id`） |

联调顺序：单路拉流 → 去畸变画面 → 人车框 → 测距数字 → 事件 POST → 障碍物链 → 多路压测延迟。

---

## 14. 相对初稿改了什么

| 初稿 | 现方案 |
|------|--------|
| 四算法无依赖并行，聚合器对框 | 两条 DAG 流水线，量测显式依赖检测 |
| 同一进程 `process(frame)` | 检测器 / 量测器两种接口；按流水线进程隔离 |
| 算法输入含「已去畸变」但未规定谁做 | ingest 统一去畸变 |
| 只有内参 + 单应 | 补外参、钢轨几何、meta、失效体检 |
| 每帧 HTTP 上报 | 事件 + 心跳；变化立即发，满足 300ms |
| 算法路径走默认 MediaMTX 转码 | 同机透传中转 + ingest 对本机 RTSP 重连；禁止转码 |
| asyncio 里同步推理 | 推理在进程/线程；过期帧丢弃 |
| 示例 640×480 | 算法 1080p |
| `attributes` 自由字段 | 固定 `distance_to_track_m` / `height_m` |
| 无跟踪 | 人车必跟踪，否则无法做进出区事件 |

---

本文可直接作为框架搭建和算法团队接口说明书。后端路径、token、最终预警阈值、供应商标定精度以对接纪要为准，只改配置，不改模块边界。
