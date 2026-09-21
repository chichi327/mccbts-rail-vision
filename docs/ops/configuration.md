# 配置与标定

密钥放 `.env`，不要提交。结构说明放 YAML。

## 文件

| 路径 | 作用 |
|------|------|
| `config/cameras.yaml` | 相机列表；只有 `rtsp`（`rtsp_main` 指向本机 8554） |
| `config/cameras.rtsp.example.yaml` | 现场 6 路 + 本机中转地址模板 |
| `config/mediamtx.yml` | MediaMTX：海康 `source`、透传、小队列 |
| `config/algorithms.yaml` | 插件开关、模块路径、算法私有参数 |
| `config/pipelines.yaml` | 两条 DAG：人车链、障碍物链 |
| `config/system.yaml` | GPU、300ms 相关阈值、健康端口、预览、心跳周期、断流判定 `camera_offline_after_ms` |
| `.env` | 后端 URL、token（覆盖 system.yaml 中的占位） |
| `config/calib/<camera_id>/` | 供应商标定 |

## 每路标定必须有

| 文件 | 内容 |
|------|------|
| `camera.npz` | `K` (3×3)、`dist` |
| `extrinsics.npz` | `R` (3×3)、`t` (3,)，或 `height_m` + `rpy_rad` |
| `homography.npz` | `H` (3×3)，**去畸变图 → 地面** |
| `rails.yaml` | 地面系钢轨几何 |
| `meta.yaml` | 分辨率、`undistorted: true`、日期、误差、供应商 |

缺文件时该相机 `calib_status=invalid`：检测可跑，距离/高度不上报。心跳 `issues` 含 `calib_invalid`，日志 `HEALTH_FAULT issue=calib_invalid`。

最新帧超过 `camera_offline_after_ms`（默认 3000）则 `camera_online=false`，与「没检出人」无关。

## 环境变量

见 `.env.example`。启动时 `core` 会用环境变量覆盖 `system.backend.*`。
