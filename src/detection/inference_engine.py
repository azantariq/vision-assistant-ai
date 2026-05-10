import cv2
import time
import threading
import uvicorn

import web_api

from src.detection.model_loader import YOLOModelLoader
from src.detection.detector import ObjectDetector
from src.analysis.scene_analyzer import SceneAnalyzer
from src.alerts.alert_manager import AlertManager
from src.audio.voice_engine import VoiceEngine


class InferenceEngine:
    def __init__(self):

        # ----------------------------
        # AI SYSTEM INIT
        # ----------------------------
        loader = YOLOModelLoader()
        self.model = loader.load_model()

        self.detector = ObjectDetector(self.model)
        self.analyzer = SceneAnalyzer()
        self.alert_manager = AlertManager()
        self.voice = VoiceEngine()

        self.cap = cv2.VideoCapture(0)

        # ----------------------------
        # START FASTAPI SERVER
        # ----------------------------
        def start_api():
            uvicorn.run(web_api.app, host="127.0.0.1", port=8001, log_level="warning")

        # Keep the API alive even if the main inference loop stops.
        threading.Thread(target=start_api, daemon=False).start()

        print("[INFO] FastAPI bridge started on port 8001")

    # ----------------------------
    # DRAW BOUNDING BOXES
    # ----------------------------
    def draw_boxes(self, frame, detections):
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = det["label"]
            conf = det["confidence"]

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                f"{label} {conf:.2f}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )

    # ----------------------------
    # MAIN LOOP
    # ----------------------------
    def run(self):
        print("[INFO] Starting real-time inference...")

        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")

        prev_time = 0

        while True:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            height, width, _ = frame.shape

            # ----------------------------
            # YOLO DETECTION + TRACKING
            # ----------------------------
            results = self.model.track(frame, persist=True, verbose=False)[0]

            detections = []

            if results.boxes is not None:
                for box in results.boxes:

                    conf = float(box.conf[0])
                    if conf < 0.5:
                        continue

                    cls_id = int(box.cls[0])
                    label = self.model.names[cls_id]

                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    track_id = int(box.id[0]) if box.id is not None else -1

                    detections.append({
                        "label": label,
                        "confidence": conf,
                        "bbox": (x1, y1, x2, y2),
                        "id": track_id
                    })

            # ----------------------------
            # SCENE ANALYSIS
            # ----------------------------
            scene_data = self.analyzer.analyze(detections, width)

            # ----------------------------
            # UPDATE DASHBOARD STATE
            # ----------------------------
            current_fps = 0

            curr_time = time.time()
            if prev_time != 0:
                current_fps = 1 / (curr_time - prev_time)
            prev_time = curr_time

            web_api.update_state(
                fps=current_fps,
                object_count=len(detections),
                risk_avg=0,
                voice_active=True,
                last_spoken="",
                is_speaking=False,
                queue_size=0
            )

            # ----------------------------
            # ALERT SYSTEM + VOICE + DASHBOARD PUSH
            # ----------------------------
            for item in scene_data:

                key = item["message"]
                priority = item["priority"]

                if self.alert_manager.should_alert(key, priority):

                    message = self.alert_manager.generate_message(item)

                    print("[ALERT]", message)

                    # voice output
                    self.voice.speak(message)

                    # send to dashboard
                    web_api.push_alert(message, priority)

            # ----------------------------
            # SEND DETECTIONS TO DASHBOARD
            # ----------------------------
            for item in scene_data:

                # convert text distance into numeric estimate
                distance_map = {
                    "VERY_CLOSE": 1,
                    "CLOSE": 3,
                    "MEDIUM": 6,
                    "FAR": 10
                }

                # convert speed text into numeric estimate
                speed_map = {
                    "FAST": 3,
                    "MEDIUM": 2,
                    "SLOW": 1,
                    "UNKNOWN": 0
                }

                web_api.push_detection(
                    label=item["label"],
                    zone=item["zone"],
                    distance_m=distance_map.get(item["distance"], 0),
                    speed_mps=speed_map.get(item["speed"], 0),
                    risk_score=item["risk_score"],
                    risk_level=item["priority"]
                )

            # ----------------------------
            # DRAW UI
            # ----------------------------
            self.draw_boxes(frame, detections)

            cv2.putText(frame, f"FPS: {int(current_fps)}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (255, 0, 0),
                        2)

            # Push the latest annotated frame to the FastAPI bridge so the
            # dashboard's /stream endpoint has actual JPEG data to serve.
            web_api.update_frame(frame)

            cv2.imshow("Vision Assistant AI", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()