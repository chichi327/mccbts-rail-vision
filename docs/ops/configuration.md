# 配置与标定

密钥放 `.env`，不要提交。结构说明放 YAML。

## 文件

| 路径 | 作用 |
|------|------|
| `config/cameras.yaml` | 相机列表、分辨率、`source`（`synthetic` / `webcam` / `rtsp`）、标定目录 |
| `config/algorithms.yaml` | 插件开关、模块路径、算法私有参数 |
| `config/pipelines.yaml` | 两条 DAG：人车链、障碍物链 |
| `config/system.yaml` | GPU、300ms 相关阈值、健康端口、预览 |
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

缺文件时该相机 `calib_status=invalid`：检测可跑，距离/高度不上报。

## 环境变量

见 `.env.example`。启动时 `core` 会用环境变量覆盖 `system.backend.*`。
