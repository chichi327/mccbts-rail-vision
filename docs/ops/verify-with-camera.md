# 用手头摄像头验证架构已通

目标：证明 **拉流 → 去畸变 → 两条流水线 → 事件** 已经串起来。  
**不证明**：人/车/障碍物识别准、测距测高准（现在是假检测框 + 示例标定）。

若画面是你的房间/办公室，框却钉在固定位置，这是正常的——插件还没换成真模型。只要图是摄像头拍的、JSON 里有 `object_id` 和距离/高度，架构通路就算过。

待确认的业务项见 [follow-up-checklist.md](follow-up-checklist.md)。

ingest **只认 RTSP**（默认 `rtsp://127.0.0.1:8554/cam01`）。本机 USB 与现场海康的差别只在谁把画面送进 MediaMTX，Python 侧不再维护第二套采集。

---

## 0. 先停掉旧进程

若之前 `bash scripts/start.sh` 还在跑，在那个终端 `Ctrl+C`。改 `cameras.yaml` 后必须重启才生效。`--webcam` 与现场 `docker compose` 的 MediaMTX **不要同时占 8554**。

```bash
source .venv/bin/activate
python scripts/gen_sample_calib.py   # 没有 calib 时做一次即可
```

验证时把 `.env` 里的地址改成占位，避免再刷 `timed out`：

```
BACKEND_EVENTS_URL=http://backend/api/vision/events
BACKEND_HEARTBEAT_URL=http://backend/api/vision/heartbeat
```

代码遇到 `http://backend` 开头会跳过 HTTP，事件仍会打在终端日志里。

---

## 1. 选一种接入方式

### 方式 A：笔记本 / USB 摄像头

`config/cameras.yaml` 保持默认即可（拉本机 8554）：

```yaml
cameras:
  - id: cam01
    name: 经本机 MediaMTX（海康或 FFmpeg 推流）
    source: rtsp
    rtsp_main: rtsp://127.0.0.1:8554/cam01
    width: 1280
    height: 720
    target_fps: 15
    calib_dir: config/calib/cam01
```

需要 FFmpeg（macOS: `brew install ffmpeg`）。macOS 若提示无权限：系统设置 → 隐私与安全 → 相机 → 允许 **终端**。

```bash
source .venv/bin/activate
bash scripts/start.sh --webcam
```

脚本会起 publisher 模式的 MediaMTX、用 FFmpeg 推 USB，再启动 `main.py`。设备序号用环境变量 `WEBCAM_DEVICE`（默认 `0`）。

不要写 `source: webcam`——ingest 会直接报错。

### 方式 B：海康 RTSP（工位一台也一样）

先起拉海康的中转，步骤见 [mediamtx.md](mediamtx.md)。`cameras.yaml` 与方式 A 相同，只改分辨率等参数以匹配码流：

```yaml
cameras:
  - id: cam01
    name: 现场或试验相机
    source: rtsp
    rtsp_main: rtsp://127.0.0.1:8554/cam01
    width: 1920
    height: 1080
    target_fps: 10
    calib_dir: config/calib/cam01
```

`mediamtx.yml` 里 `paths.cam01.source` 必须等于海康地址。然后：

```bash
docker compose up -d mediamtx
source .venv/bin/activate
bash scripts/start.sh
```

---

## 2. 用主进程持续识别并看画面（推荐）

日志里会出现：

```text
open preview http://127.0.0.1:8081/preview
```

浏览器打开该地址，应看到**实时画面 + 绿/橙色框**。预览走共享内存，不把整帧 pickle 进子进程。

若仍觉得卡：关其它占用摄像头的软件，只开一个预览标签页。`target_fps` 可在 `cameras.yaml` 调到 15～20。

健康检查仍是 `http://127.0.0.1:8080/health`。

假检测器框不会跟着你走。`person_enter_warning` 日志通常只出现一次。画面会一直刷新。

关预览：`config/system.yaml` 里 `preview.enabled: false`。

---

## 3. 最小验证（可选）：单帧抓拍

不要与 `start.sh` 同时跑（会抢同一路 RTSP 以外的资源；webcam 模式下会抢 USB）。须先让 MediaMTX 上已有画面（`--webcam` 起的中转，或 compose 拉海康）。在仓库根：

```bash
python scripts/test_single_camera.py --camera-id cam01 --pipeline person_vehicle
python scripts/test_single_camera.py --camera-id cam01 --pipeline obstacle
```

**通过标准**

| 检查 | 通过 |
|------|------|
| 终端打印 `Detection(...)` | 有 `object_id`、人车链有 `distance_to_track_m`、障碍物链有 `height_m` |
| 打开 `data/debug/last_frame.jpg` | 能认出是**你的摄像头画面**（不是灰底假图） |
| 图上有绿框和字 | 框是骨架假检测器画的，位置可不准 |

**失败排查**

- `读不到帧`：8554 上没有推流/拉流；海康地址、账号、防火墙；`--webcam` 时 FFmpeg/相机权限
- `打不开摄像头`：macOS 未授权终端访问相机；`WEBCAM_DEVICE` 换 `1`
- JPEG 仍是灰图带一条白线：实际读的是 `cameras.synthetic.yaml`，不是真相机
- 有图但全黑：摄像头被占用（腾讯会议/浏览器先退出）
- `source=webcam` 报错：配置写错，改回 `source: rtsp`

---

## 4. 完整服务（无预览时看日志）

方式 A 用 `bash scripts/start.sh --webcam`；方式 B 用 compose 起中转后 `bash scripts/start.sh`。

另开终端：

```bash
curl -s http://127.0.0.1:8080/health
```

应为 `"status":"ok"` 且含 `cam01`。

启动日志里应出现类似：

```text
started processes=['ingest-cam01', 'pipe-person_vehicle', 'pipe-obstacle', 'report-health']
event camera=cam01 type=person_enter_warning dist=...
event camera=cam01 type=obstacle_appeared ...
```

假检测器每路几乎一直能检出同一个框，所以 **warning / appeared 通常只打一次**（状态不变不再发事件）。这是设计如此，不是卡死。

**通过标准**：进程四件套都在、health 正常、日志里有上述两类 event。  
然后 `Ctrl+C` 停掉。

---

## 5. 这一步**不能**当成验收的

- 框没有套在你身上（假检测器位置固定）
- 距离不是拿米尺量轨道的结果（用的是 `config/calib/cam01` 示例单应）

真模型进来后，预览上的框应跟着人走；再拿现场标定对比测距。
