# 后续待确认清单

本文把「架构已经搭好、但业务还没闭环」的事项拆开，方便你逐项研究后勾选。架构对错仍以 [system-design.md](../architecture/system-design.md) 为准。

确认结果请写在每条的「我的结论」里；拍板后追加到 [ai/memory.md](../ai/memory.md)，并改对应配置，不要只改对话记录。

手头摄像头怎么验证通路，见 [verify-with-camera.md](verify-with-camera.md)。

图例：`- [ ]` 未确认 · `- [x]` 已确认（请手动改）。

---

## A. 后端对接

### A1. 事件接口长什么样？

- [ ] 已拿到正式 URL、方法（建议 POST）、鉴权（token / 其他）
- [ ] 已确认字段是否必须用我们现在的 JSON（见 system-design 第 8.2 节），还是要适配他们现有结构
- [ ] 已确认他们按 `event_id` 做幂等，避免重试重复告警
- **落点**：`.env` 的 `BACKEND_EVENTS_URL`、`BACKEND_TOKEN`；若字段不同，改 `core/report/reporter.py` 的映射，不要改算法插件
- **我的结论**：

### A2. 心跳接口？

- [ ] 是否要独立 URL（建议要）
- [ ] 周期（现在默认 5 秒）是否可接受
- **落点**：`.env` 的 `BACKEND_HEARTBEAT_URL`；`config/system.yaml` 的 `heartbeat_interval_s`
- **我的结论**：

### A3. 上报语义：事件还是逐帧？

- [ ] 业务侧确认「只在状态变化时推」（进入预警/危险、障碍物出现消失），而不是每帧全量框
- [ ] 若他们坚持逐帧，需要单独评估 300ms 和后端容量（当前架构不按逐帧设计）
- **我的结论**：

---

## B. 相机与现场

### B1. 相机清单

- [ ] 路数（现场 6 路）、安装位置、每路 ID（与 MediaMTX path 同名）
- [ ] 海康主码流写入 `config/mediamtx.yml`；`rtsp_main` 指向本机 `8554/<id>`
- [ ] 账号密码、网段是否和算法服务器互通
- **落点**：`config/mediamtx.yml`、`config/cameras.yaml`（示例 `cameras.rtsp.example.yaml`）
- **我的结论**：

### B2. 分辨率与帧率

- [ ] 主码流是否 1080p（或现场实际值）
- [ ] 算法 `target_fps` 5～10 是否被相机 GOP/码率允许
- **落点**：`config/cameras.yaml` 的 `width` / `height` / `target_fps`
- **我的结论**：

### B3. 算法服务器

- [ ] GPU 型号与数量、驱动、是否 Docker + NVIDIA runtime
- [ ] 预计一路卡接几路相机（基线 4～8，以压测为准）
- **落点**：部署说明 [packaging.md](packaging.md)；`system.gpu_id`
- **我的结论**：

---

## C. 供应商标定

### C1. 交付物是否齐全（每路相机一套）

- [ ] 内参 `K` + 畸变
- [ ] 外参 `R,t` 或安装高度 + 姿态（测高必须）
- [ ] 去畸变图到地面的单应 `H`（测距必须）
- [ ] 地面坐标系下两条钢轨（或中心线）几何
- [ ] 书面：以上均基于**去畸变图**；标定时分辨率
- [ ] 距离/高度误差范围（验收用）
- **落点**：`config/calib/<camera_id>/`；清单见 [configuration.md](configuration.md)
- **我的结论**：

### C2. 单目高度是否承诺能算

- [ ] 供应商书面确认：仅单目 + 外参能否出障碍物高度、大概精度
- [ ] 若不能，高度是降级（粗估 + 低置信）还是上双目/深度
- **我的结论**：

### C3. 重标定规则

- [ ] 挪机、撞击、换镜头后谁负责重标、多久一次体检
- **我的结论**：

---

## D. 业务规则

### D1. 「到铁轨的距离」口径

- [ ] 确认：人脚点 / 车底中心 → **最近钢轨** 的水平距离（当前实现）
- [ ] 若工务要「到限界」或「到轨道中心」，只改标定几何/量测，不改检测器
- **落点**：`rails.yaml` + `algorithms/track_distance`
- **我的结论**：

### D2. 预警 / 危险阈值

- [ ] 预警 2.0m、危险 1.0m 是否被工务/安监认可
- **落点**：`config/system.yaml` 的 `warning_distance_m` / `danger_distance_m`
- **我的结论**：

### D3. 人车 vs 障碍物

- [ ] 确认人/车只走算法 1，落石异物走算法 2，互不重复告警
- **我的结论**：

### D4. 障碍物高度要不要告警阈值

- [ ] 是否需要 `obstacle_height_alert`（例如高于 0.5m）
- **落点**：事件层配置（确认后再加，不要四个团队各写各的）
- **我的结论**：

---

## E. 四个算法团队

### E1. 人员车辆检测

- [ ] 负责人、交付日期、模型格式（PyTorch / TensorRT）
- [ ] 已阅读 [plugin-guide.md](../algorithms/plugin-guide.md)
- [ ] 替换 `algorithms/person_vehicle_detect/` 里的假检测器
- **我的结论**：

### E2. 铁轨测距

- [ ] 是否直接用框架 `CalibView.bbox_foot_to_rail_distance`，还是自有几何
- [ ] 替换或确认 `algorithms/track_distance/`
- **我的结论**：

### E3. 障碍物检测

- [ ] 类别不含 person/car/truck
- [ ] 替换 `algorithms/obstacle_detect/`
- **我的结论**：

### E4. 障碍物高度

- [ ] 基于障碍物框 + 标定，不自己再检一套框
- [ ] 替换 `algorithms/obstacle_height/`
- **我的结论**：

### E5. 仓库协作方式

- [ ] 同一 Git 仓库四个子目录（当前约定）是否被各团队接受
- [ ] 模型 `.pt` 不进 git，现场如何分发
- **我的结论**：

---

## F. 体验与验收（框架侧）

### F1. 预览与拉流中转

- [x] 本地叠框：`http://127.0.0.1:8081/preview`
- [x] MediaMTX 与算法同机：透传拉海康、ingest 对本机 RTSP 重连；本机 USB 走 FFmpeg publisher，无第二套 ingest（见 [mediamtx.md](mediamtx.md)）
- [ ] 6 路真实地址写入 `mediamtx.yml` 后做断网再联网恢复验收，并确认事件仍 <300ms
- **我的结论**：

### F2. 延迟压测

- [ ] 真相机 + 真模型后，事件从采集到 HTTP 发出是否 < 300ms
- [ ] 丢帧率是否可接受（高了先降分辨率/fps/上 TensorRT，不加长队列）
- **我的结论**：

### F3. 失败与运维

- [ ] 相机断流、算法进程崩溃、标定失效，后端是否要看心跳区分「没人」和「系统挂了」
- **我的结论**：

---

## 建议你研究的顺序

1. A1 后端事件接口（没有它，现场也只是本地 JSON）
2. B1 相机清单（决定能不能接真流）
3. C1 标定交付（决定测距测高有没有物理意义）
4. D2 阈值 + D1 距离口径（业务对错）
5. E1～E4 算法团队排期
6. 填写 `mediamtx.yml` 并做断网恢复（[mediamtx.md](mediamtx.md)）
7. F2 上真模型后再压 300ms

不要并行把「假检测器」和「供应商标定精度」混在一次验收里：先证明**管道通**（[verify-with-camera.md](verify-with-camera.md)），再证明**测得准**。
