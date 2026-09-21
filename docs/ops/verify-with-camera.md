# 用海康验证架构已通

目标：证明 **拉流 → 去畸变 → 两条流水线 → 事件** 已经串起来。  
**不证明**：人/车/障碍物识别准、测距测高准（现在是假检测框 + 示例标定）。

若画面是你的房间/办公室，框却钉在固定位置，这是正常的——插件还没换成真模型。只要图是摄像头拍的、JSON 里有 `object_id` 和距离/高度，架构通路就算过。

待确认的业务项见 [follow-up-checklist.md](follow-up-checklist.md)。

ingest **只认** `rtsp://127.0.0.1:8554/<相机id>`。海康地址只写在 `config/mediamtx.yml`。

---

## 0. 先停掉旧进程

若之前算法还在跑，先停掉。改 `cameras.yaml` 或 `mediamtx.yml` 后必须重启对应进程才生效。

macOS / Linux：`bash scripts/stop.sh`  
Windows：`powershell -ExecutionPolicy Bypass -File scripts\stop.ps1`

```bash
python scripts/gen_sample_calib.py   # 没有 calib 时做一次即可
```

验证时把 `.env` 里的地址改成占位，避免再刷 `timed out`：

```
BACKEND_EVENTS_URL=http://backend/api/vision/events
BACKEND_HEARTBEAT_URL=http://backend/api/vision/heartbeat
```

代码遇到 `http://backend` 开头会跳过 HTTP，事件仍会打在终端日志里。

---

## 1. 接海康

步骤见 [mediamtx.md](mediamtx.md)。`cameras.yaml` 只拉本机中转：

```yaml
cameras:
  - id: cam01
    name: 工位海康
    source: rtsp
    rtsp_main: rtsp://127.0.0.1:8554/cam01
    width: 1920
    height: 1080
    target_fps: 10
    calib_dir: config/calib/cam01
```

`mediamtx.yml` 里 `paths.cam01.source` 必须等于海康主码流。然后：

macOS / Linux：

```bash
docker compose up -d mediamtx
bash scripts/start.sh
```

Windows：

```powershell
docker compose up -d mediamtx
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```

---

## 2. 用主进程持续识别并看画面（推荐）

日志里会出现：

```text
open preview http://127.0.0.1:8081/preview
```

浏览器打开该地址，应看到**实时画面 + 绿/橙色框**。预览走共享内存，不把整帧 pickle 进子进程。纯看视频（更跟手）可用 MediaMTX WebRTC：`http://127.0.0.1:8889`。

若仍觉得卡：关其它占用预览的标签页。`target_fps` 可在 `cameras.yaml` 调。

健康检查仍是 `http://127.0.0.1:8080/health`。断流 / 流水线挂 / 标定失效看 `issues` 和日志 `HEALTH_FAULT`，不要和「没检出人」混在一起。

假检测器框不会跟着你走。`person_enter_warning` 日志通常只出现一次。画面会一直刷新。

关预览：`config/system.yaml` 里 `preview.enabled: false`。

看算法耗时：把 `system.timing.enabled` 改成 `true`（或 `.env` 里 `TIMING_ENABLED=true`），日志会出现 `timing camera=... detect_ms=... e2e_ms=...` 和 `timing ingest ...`。现场关掉。

---

## 3. 最小验证（可选）：单帧抓拍

不要与 `start.sh` 同时跑（会抢同一路本机 RTSP）。须先让 MediaMTX 上已有画面。在仓库根：

```bash
python scripts/test_single_camera.py --camera-id cam01 --pipeline person_vehicle
python scripts/test_single_camera.py --camera-id cam01 --pipeline obstacle
```

**通过标准**

| 检查 | 通过 |
|------|------|
| 终端打印 `Detection(...)` | 有 `object_id`、人车链有 `distance_to_track_m`、障碍物链有 `height_m` |
| 打开 `data/debug/last_frame.jpg` | 能认出是**海康画面** |
| 图上有绿框和字 | 框是骨架假检测器画的，位置可不准 |

**失败排查**

- `读不到帧`：8554 上没有码流；海康地址、账号、防火墙；Docker 容器访问不到相机网段
- 有图但全黑：镜头盖 / 曝光

---

## 4. 完整服务（无预览时看日志）

先 `docker compose up -d mediamtx`，再按系统启动：`bash scripts/start.sh` 或 `scripts\start.ps1`。

另开终端：

```bash
curl -s http://127.0.0.1:8080/health
```

应为 `"status":"ok"` 且含 `cam01`。

启动日志里应出现类似：

```text
started ingest_threads=['ingest-cam01'] processes=['pipe-person_vehicle', 'pipe-obstacle', 'report-health']
event camera=cam01 type=person_enter_warning dist=...
event camera=cam01 type=obstacle_appeared ...
```

假检测器每路几乎一直能检出同一个框，所以 **warning / appeared 通常只打一次**（状态不变不再发事件）。这是设计如此，不是卡死。

**通过标准**：进程都在、health 正常、日志里有上述两类 event。  
停掉：macOS / Linux 用 `bash scripts/stop.sh`，Windows 用 `scripts\stop.ps1`。

---

## 5. 这一步**不能**当成验收的

- 框没有套在你身上（假检测器位置固定）
- 距离不是拿米尺量轨道的结果（用的是 `config/calib/cam01` 示例单应）

真模型进来后，预览上的框应跟着人走；再拿现场标定对比测距。
