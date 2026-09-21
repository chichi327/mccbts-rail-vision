"""
实时人体检测 — 使用 YOLO11 预训练模型 yolo11n.pt（COCO，仅检测 person）

本文件只是同事原来的独立演示，算法服务不要用它启动。
正式入口：PersonVehicleDetector（detector.py），由 main.py 流水线调用。

用法（仅本地看模型）:
  python person_detect_live.py

配置:
  修改 VIDEO_SOURCE — 0 为默认摄像头，也可填 RTSP 地址或本地视频路径
  按 q 退出，按 s 保存当前帧截图
"""

import time

import cv2
from ultralytics import YOLO

# ========== 配置 ==========
MODEL_PATH = "./models/yolo11n.pt"  #
VIDEO_SOURCE = 0  # 0=摄像头；或 "rtsp://..." / "./video.mp4"
CONFIDENCE_THRESHOLD = 0.5
PERSON_CLASS_ID = 0  # COCO 数据集中 person 的类别 ID
WINDOW_NAME = "Person Detection"
RECONNECT_DELAY_SECONDS = 5


def open_capture(source):
    """打开视频源；RTSP/网络流使用 FFMPEG 后端。"""
    if isinstance(source, str) and (
        source.startswith("rtsp://")
        or source.startswith("http://")
        or source.startswith("https://")
    ):
        cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
    else:
        cap = cv2.VideoCapture(source)
    if cap.isOpened():
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def draw_person_boxes(frame, boxes, model):
    """在帧上绘制人体检测框，返回标注帧与人数。"""
    annotated = frame.copy()
    person_count = 0

    for box in boxes:
        class_id = int(box.cls[0])
        if class_id != PERSON_CLASS_ID:
            continue

        conf = float(box.conf[0])
        if conf < CONFIDENCE_THRESHOLD:
            continue

        person_count += 1
        x1, y1, x2, y2 = box.xyxy[0].int().tolist()
        label = f"person {conf:.2f}"

        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        label_y = max(y1 - 8, label_size[1] + 8)
        cv2.rectangle(
            annotated,
            (x1, label_y - label_size[1] - 6),
            (x1 + label_size[0] + 4, label_y + 4),
            (0, 255, 0),
            -1,
        )
        cv2.putText(
            annotated,
            label,
            (x1 + 2, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            2,
        )

    return annotated, person_count


def main():
    print("正在加载模型...")
    model = YOLO(MODEL_PATH)
    print(f"✅ 模型加载成功: {MODEL_PATH}")

    cap = open_capture(VIDEO_SOURCE)
    if not cap.isOpened():
        print(f"❌ 无法打开视频源: {VIDEO_SOURCE}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps_src = cap.get(cv2.CAP_PROP_FPS)
    print(f"视频信息: {width}x{height} @ {fps_src:.2f}fps")
    print("开始实时检测人体，按 q 退出，按 s 保存截图")

    need_reconnect = False
    frame_count = 0
    start_time = time.time()

    try:
        while True:
            if need_reconnect or not cap.isOpened():
                print(f"\n尝试重连视频源: {VIDEO_SOURCE}")
                if cap.isOpened():
                    cap.release()
                cap = open_capture(VIDEO_SOURCE)
                if cap.isOpened():
                    print("✅ 视频源重连成功")
                    need_reconnect = False
                else:
                    print(f"❌ 重连失败，{RECONNECT_DELAY_SECONDS} 秒后重试...")
                    need_reconnect = True
                    time.sleep(RECONNECT_DELAY_SECONDS)
                    continue

            ret, frame = cap.read()
            if not ret or frame is None:
                print("❌ 无法读取视频帧")
                need_reconnect = True
                continue

            frame_count += 1
            elapsed = time.time() - start_time
            process_fps = frame_count / (elapsed + 1e-8)

            results = model(frame, classes=[PERSON_CLASS_ID], verbose=False)
            boxes = results[0].boxes
            annotated, person_count = draw_person_boxes(frame, boxes, model)

            info = f"persons: {person_count}  FPS: {process_fps:.1f}"
            cv2.putText(
                annotated,
                info,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                2,
            )

            cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
            cv2.imshow(WINDOW_NAME, annotated)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("\n用户退出")
                break
            if key == ord("s"):
                save_path = f"person_detect_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(save_path, annotated)
                print(f"✅ 截图已保存: {save_path}")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("检测结束")


if __name__ == "__main__":
    main()
