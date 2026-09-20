# MediaMTX 拉流中转

现场默认：MediaMTX 与算法 **同一台服务器**；算法只拉本机 RTSP。原因：直连海康时，相机断网再联网有概率码流恢复不了。

Python ingest **只有这一条真实路径**。本机 USB 用 FFmpeg 推到 `config/mediamtx.webcam.yml`（`source: publisher`），海康由 `config/mediamtx.yml` 拉取。无相机单测才用 `config/cameras.synthetic.yaml`。

## 本机 USB（与现场同一条 ingest）

不要改 `cameras.yaml` 去直采设备。停掉占用 8554 的现场 compose 后：

```bash
brew install ffmpeg   # 若尚未安装
bash scripts/start.sh --webcam
```

`WEBCAM_DEVICE` 默认 `0`。macOS 默认推 **30fps**（15 常被 avfoundation 拒绝）。Ctrl+C 会停 FFmpeg 和临时 MediaMTX 容器。推流失败时 ingest 会对 `cam01` 报 404，预览没有画面。

## 本机只接一台海康

1. 电脑和相机同一局域网，用 VLC 能打开：  
   `rtsp://用户:密码@相机IP:554/Streaming/Channels/101`
2. `config/mediamtx.yml` 只改 `paths.cam01.source` 为上面这条（其余 cam02… 可先删或保持占位）
3. `config/cameras.yaml`：

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

4. 先起中转再起算法：

```bash
docker compose up -d mediamtx
# 或: mediamtx config/mediamtx.yml
source .venv/bin/activate
bash scripts/start.sh
```

预览仍是 `http://127.0.0.1:8081/preview`。Mac 上 Docker 桥接若拉不到相机，用本机安装的 `mediamtx` 二进制，或保证容器能访问相机网段。

## 配置

| 文件 | 作用 |
|------|------|
| `config/mediamtx.yml` | 现场/工位：每路 `paths.<id>.source` = 海康主码流；**不要配 ffmpeg 转码** |
| `config/mediamtx.webcam.yml` | 本机 USB：`cam01` 为 `publisher`，配合 `bash scripts/start.sh --webcam` |
| `config/cameras.rtsp.example.yaml` | 6 路示例：`rtsp_main` 指向 `rtsp://127.0.0.1:8554/<id>` |
| `config/cameras.yaml` | ingest 实际读取的列表（只拉 8554） |
| `config/cameras.synthetic.yaml` | 无硬件单测，不是第二种摄像头接入 |

path 名必须等于相机 `id`。改海康地址时 **yml 与 example 一起改**。

Compose 里算法容器若走桥接网络，把 `rtsp_main` 改成 `rtsp://mediamtx:8554/cam01`。Linux 现场推荐：

```bash
docker compose -f docker-compose.yml -f docker-compose.field.yml up -d
```

`field` 使用 host 网络，此时 `127.0.0.1:8554` 可用。

不经过 Docker、本机已装二进制时：

```bash
mediamtx config/mediamtx.yml
```

再 `bash scripts/start.sh`。

## 延迟

`writeQueueSize: 64` 偏小。验收：6 路事件链路仍要 <300ms。变卡先查是否误开转码/HLS，再减小队列，不要加长算法侧缓冲。

WebRTC 预览端口 8889（MediaMTX 自带）。叠框预览仍是 `http://127.0.0.1:8081/preview`。

## 断网验收

1. 算法已稳定出帧  
2. 拔相机网线数秒再插  
3. MediaMTX 日志应重新拉源；ingest 日志出现 `rtsp reconnect` 后应 `rtsp opened`  
4. 预览/事件恢复，无需重启 Python 进程  

若中转已恢复、Python 仍无帧，才是 ingest 重连有 bug。
