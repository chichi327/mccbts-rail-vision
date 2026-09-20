# 算法插件指南

四个团队只改自己的 `algorithms/<name>/`，实现 `core.base` 接口，在 `config/algorithms.yaml` 注册。不要改 `core/`。

## 检测器

继承 `core.base.detector.BaseDetector`，实现 `load` / `infer` / `release`。

- 输入帧已去畸变 BGR
- 只返回 `Detection` 的 `type, confidence, bbox_xyxy`
- 人车团队：`person` | `car` | `truck`
- 障碍物团队：只 `obstacle`

## 量测器

继承 `core.base.estimator.BaseEstimator`，实现 `load` / `estimate` / `release`。

- 必须使用传入的 `detections`，用 `calib`（`CalibView`）补物理量
- 测距：`distance_to_track_m`，优先 `calib.bbox_foot_to_rail_distance`
- 高度：`height_m`，优先 `calib.bbox_to_height_m`
- 不得丢弃上游目标、不得另起一套 bbox 当主结果

## 注册

`config/algorithms.yaml` 的 `module` + `class`，流水线顺序写在 `config/pipelines.yaml`。

## 模型文件

放 `algorithms/<name>/models/`，大文件不要进 git（已 gitignore `*.pt`）。
