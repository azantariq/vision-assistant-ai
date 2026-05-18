import cv2
import time
import threading
import uvicorn
import requests

import web_api

from src.detection.model_loader import YOLOModelLoader
from src.analysis.scene_analyzer import SceneAnalyzer
from src.audio.voice_engine import VoiceEngine

# from src.ocr.ocr_engine import OCREngine
# from src.ocr.text_filter import OCRTextFilter
from src.brain.decision_engine import DecisionEngine

from src.analysis.object_memory import ObjectMemory


class InferenceEngine:

    def __init__(self):

        # ----------------------------
        # INIT AI SYSTEM
        # ----------------------------
        print("[INFO] Loading YOLOv8 model...")

        loader = YOLOModelLoader()
        self.model = loader.load_model()

        print("[INFO] Model loaded successfully.")

        # ----------------------------
        # ENABLED MODULES
        # ----------------------------
        self.memory = ObjectMemory()

        # ----------------------------
        # DISABLED MODULES (FOR NOW)
        # ----------------------------
        self.analyzer = SceneAnalyzer()
        self.voice = VoiceEngine()

        self.brain = DecisionEngine()
        self.behavior_triggered = set()

        # OCR
        # self.ocr_engine = OCREngine()
        # self.ocr_filter = OCRTextFilter()

        # ----------------------------
        # CAMERA
        # ----------------------------
        self.cap = cv2.VideoCapture(0)

        # ----------------------------
        # STATE
        # ----------------------------
        self.frame_counter = 0
        self.latest_frame = None
        self.current_ocr_results = []

        self.last_motion_state = {}
        self.cooldowns = {}  # {key: last_time}
        self.COOLDOWN_SEC = 2.0
        self.is_speaking = False

        # ----------------------------
        # MOTION TRACKING MEMORY
        # ----------------------------
        self.track_memory = {}
        self.behavior_history = {}
        self.behavior_cooldown = {}
        self.BEHAVIOR_COOLDOWN_SEC = 5

        # ----------------------------
        # OCR THREAD DISABLED
        # ----------------------------
        # self.ocr_running = True
        # threading.Thread(
        #     target=self.ocr_worker,
        #     daemon=True
        # ).start()

        # ----------------------------
        # FASTAPI DISABLED
        # ----------------------------
        def start_api():
            uvicorn.run(
                web_api.app,
                host="127.0.0.1",
                port=8001,
                log_level="warning"
            )

        threading.Thread(
            target=start_api,
            daemon=True
        ).start()

        print("[INFO] FastAPI bridge started on port 8001")

    # def send_to_server(self, detections, motions, scene_data, fps):
    #     try:
    #         payload = {
    #             "fps": fps,
    #             "objects": [
    #                 {
    #                     "id": d.get("id", -1),
    #                     "label": d["label"],
    #                     "zone": "CENTER",
    #                     "risk": 50,
    #                     "age": 0,
    #                     "motion": "STABLE"
    #                 }
    #                 for d in detections
    #             ],
    #             "alerts": [
    #                 {
    #                     "id": int(time.time() * 1000),
    #                     "type": "BEHAVIOR",
    #                     "message": "Live update from Python",
    #                     "risk_level": "LOW",
    #                     "timestamp": time.time()
    #                 }
    #             ],
    #             "scene_summary": "Live Python AI running",
    #             "dominant_objects": [d["label"] for d in detections[:3]],
    #             "activity_status": "ACTIVE",
    #             "uptime": time.time(),
    #             "frame_count": self.frame_counter
    #         }

    #         requests.post("http://localhost:8000/api/python", json=payload, timeout=0.2)

    #     except Exception as e:
    #         print("[PIPE ERROR]", e)

    def update_behavior(self, motions):

        for m in motions:

            obj_id = m["id"]

            if obj_id not in self.behavior_history:
                self.behavior_history[obj_id] = []

            self.behavior_history[obj_id].append({
                "direction": m["direction"],
                "motion": m["motion"],
                "time": time.time()
            })

            # keep only last 10 states
            self.behavior_history[obj_id] = self.behavior_history[obj_id][-10:]

    def get_object_age(self, obj_id):

        obj = self.memory.get(obj_id)

        if not obj:
            return 0

        return time.time() - obj["first_seen"]

    def detect_lifecycle(self):

        current_ids = set(self.track_memory.keys())
        stored_ids = set(self.memory.get_all().keys())

        entered = current_ids - stored_ids
        left = stored_ids - current_ids

        return {
            "entered": list(entered),
            "left": list(left)
        }
    
    def update_memory(self, detections):

        current_time = time.time()

        for det in detections:

            obj_id = det.get("id", -1)

            if obj_id == -1:
                continue

            x1, y1, x2, y2 = det["bbox"]

            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2

            zone = "UNKNOWN"

            # safe zone inference (basic fallback)
            if cx < 200:
                zone = "LEFT"
            elif cx > 440:
                zone = "RIGHT"
            else:
                zone = "CENTER"

            # ✅ FIXED CALL (match your ObjectMemory signature)
            self.memory.update(
                obj_id,
                det["label"],
                det["bbox"],
                zone,
                current_time
                
            )

    def speak_safe(self, message):

        if self.is_speaking:
            return

        self.is_speaking = True

        try:
            self.voice.speak(message)
        finally:
            self.is_speaking = False


    def can_trigger(self, key):
        current = time.time()
        last_time = self.cooldowns.get(key, 0)

        if current - last_time > self.COOLDOWN_SEC:
            self.cooldowns[key] = current
            return True

        return False

    # ----------------------------
    # MOTION ANALYSIS
    # ----------------------------
    def update_motion(self, detections):

        motions = []

        current_time = time.time()

        for det in detections:

            obj_id = det.get("id", -1)

            if obj_id == -1:
                continue

            x1, y1, x2, y2 = det["bbox"]

            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2

            # First appearance
            if obj_id not in self.track_memory:

                self.track_memory[obj_id] = (
                    cx,
                    cy,
                    current_time
                )

                continue

            prev_x, prev_y, prev_t = self.track_memory[obj_id]

            dx = cx - prev_x
            dy = cy - prev_y

            dt = current_time - prev_t

            if dt <= 0:
                continue

            vx = dx / dt
            vy = dy / dt

            # Update tracking memory
            self.track_memory[obj_id] = (
                cx,
                cy,
                current_time
            )

            # Horizontal movement
            if abs(vx) < 15:
                direction = "STABLE"

            elif vx > 0:
                direction = "RIGHT"

            else:
                direction = "LEFT"

            # Vertical movement
            if abs(vy) < 10:
                motion = "STATIC"

            elif vy > 0:
                motion = "APPROACHING"

            else:
                motion = "AWAY"

            motions.append({
                "id": obj_id,
                "vx": vx,
                "vy": vy,
                "direction": direction,
                "motion": motion
            })

        return motions

    # ----------------------------
    # OCR THREAD (DISABLED)
    # ----------------------------
    # def ocr_worker(self):

    #     while self.ocr_running:

    #         try:

    #             if self.latest_frame is None:
    #                 time.sleep(0.2)
    #                 continue

    #             frame = self.latest_frame.copy()

    #             ocr_results = self.ocr_engine.extract_text(frame)

    #             self.current_ocr_results = ocr_results

    #             for item in ocr_results:

    #                 text = item["text"]

    #                 if self.ocr_filter.should_speak(text):

    #                     msg = f"Text detected: {text}"

    #                     print("[OCR]", msg)

    #                     threading.Thread(
    #                         target=self.voice.speak,
    #                         args=(msg,),
    #                         daemon=True
    #                     ).start()

    #             time.sleep(2)

    #         except Exception as e:
    #             print("[OCR ERROR]", e)

    # ----------------------------
    # DRAW BOXES
    # ----------------------------
    def draw_boxes(self, frame, detections):

        # ----------------------------
        # OBJECT BOXES
        # ----------------------------
        for det in detections:

            x1, y1, x2, y2 = det["bbox"]

            label = det["label"]
            conf = det["confidence"]

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

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
        # OCR OVERLAY DISABLED
        # ----------------------------
        # for item in self.current_ocr_results:

        #     bbox = item["bbox"]
        #     text = item["text"]

        #     top_left = tuple(map(int, bbox[0]))
        #     bottom_right = tuple(map(int, bbox[2]))

        #     cv2.rectangle(
        #         frame,
        #         top_left,
        #         bottom_right,
        #         (0, 0, 255),
        #         2
        #     )

        #     cv2.putText(
        #         frame,
        #         text,
        #         (top_left[0], top_left[1] - 10),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         0.6,
        #         (0, 0, 255),
        #         2
        #     )

    # ----------------------------
    # MAIN LOOP
    # ----------------------------
    def run(self):

        print("[INFO] Starting real-time inference...")

        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")

        prev_time = 0

        FRAME_SKIP = 2

        while True:

            # ----------------------------
            # CAMERA READ
            # ----------------------------
            ret, frame = self.cap.read()

            if not ret:

                print("[WARNING] Failed to read frame")

                time.sleep(0.05)
                continue

            # ----------------------------
            # RESIZE FRAME
            # ----------------------------
            frame = cv2.resize(frame, (640, 480))

            self.latest_frame = frame.copy()

            self.frame_counter += 1

            # ----------------------------
            # FRAME SKIP
            # ----------------------------
            if self.frame_counter % FRAME_SKIP != 0:

                cv2.imshow(
                    "Vision Assistant AI",
                    frame
                )

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                continue

            height, width, _ = frame.shape

            # ----------------------------
            # YOLO DETECTION
            # ----------------------------
            results = self.model.track(
                frame,
                persist=True,
                verbose=False,
                conf=0.6,
                imgsz=480
            )[0]

            detections = []

            

            # ----------------------------
            # PROCESS DETECTIONS
            # ----------------------------
            if results.boxes is not None:

                for box in results.boxes:

                    conf = float(box.conf[0])

                    if conf < 0.5:
                        continue

                    cls_id = int(box.cls[0])

                    label = self.model.names[cls_id]

                    x1, y1, x2, y2 = map(
                        int,
                        box.xyxy[0]
                    )

                    track_id = (
                        int(box.id[0])
                        if box.id is not None
                        else -1
                    )

                    detections.append({
                        "label": label,
                        "confidence": conf,
                        "bbox": (x1, y1, x2, y2),
                        "id": track_id
                    })
            self.update_memory(detections)

            lifecycle = self.detect_lifecycle()

            for obj_id in lifecycle["left"]:
                self.memory.remove(obj_id)

                # reset behavior trigger
                key = f"behavior_{obj_id}_staying_long"
                if key in self.behavior_triggered:
                    self.behavior_triggered.remove(key)

            for obj_id in lifecycle["entered"]:
                print(f"[LIFECYCLE] ENTERED: {obj_id}")

            for obj_id in lifecycle["left"]:
                print(f"[LIFECYCLE] LEFT: {obj_id}")

            # ----------------------------
            # MOTION ANALYSIS
            # ----------------------------
            motions = self.update_motion(detections)
            self.update_behavior(motions)

            # ----------------------------
            # PRINT MOTION INFO
            # ----------------------------
            for motion in motions:

                obj_id = motion["id"]

                current_state = (motion["direction"], motion["motion"])
                previous_state = self.last_motion_state.get(obj_id)

                # ONLY PRINT IF STATE CHANGES + COOLDOWN
                if current_state != previous_state:

                    key = f"motion_{obj_id}"

                    if self.can_trigger(key):

                        print(
                            f"[MOTION] ID={obj_id} "
                            f"{motion['direction']} "
                            f"{motion['motion']}"
                        )

                        self.last_motion_state[obj_id] = current_state

            if motions:
                self.update_behavior(motions)

            # ----------------------------
            # SCENE ANALYSIS DISABLED
            # ----------------------------
            scene_data = self.analyzer.analyze(
                detections,
                width,
                height
            )
            for item in scene_data:

                obj_id = item.get("id", -1)
                age = self.get_object_age(obj_id)

                print(
                    f"[SCENE] "
                    f"{item['label']} | "
                    f"{item['zone']} | "
                    f"{item['distance']} | "
                    f"Age={age:.1f}s | "
                    f"Risk={item['risk_score']}"
                )

            # ----------------------------
            # 🔧 STEP 5 — BEHAVIOR INTELLIGENCE UPGRADE
            # ----------------------------
            # ----------------------------
            # BEHAVIOR INTELLIGENCE (FIXED)
            # ----------------------------

            for obj_id, obj in self.memory.get_all().items():

                age = time.time() - obj["first_seen"]

                if age > 5:

                    key = f"behavior_{obj_id}_staying_long"

                    # only trigger ONCE
                    if key not in self.behavior_triggered:

                        print(f"[BEHAVIOR ALERT] {obj['label']} staying too long: {age:.1f}s")

                        self.behavior_triggered.add(key)

            # ----------------------------
            # FPS
            # ----------------------------
            curr_time = time.time()

            fps = (
                1 / (curr_time - prev_time)
                if prev_time
                else 0
            )

            prev_time = curr_time

            web_api.update_state(
                fps=fps,
                object_count=len(detections),
                risk_avg=0.0,
                voice_active=self.is_speaking,
                last_spoken=None,
                is_speaking=self.is_speaking,
                queue_size=0
            )   


            for det in detections[:10]:
                web_api.push_detection(
                    label=det["label"],
                    zone="CENTER",
                    risk_score=0.0,
                    risk_level="low"
                )
            

            cv2.putText(
                frame,
                f"FPS: {int(fps)}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 0, 0),
                2
            )

            # self.send_to_server(detections, motions, scene_data, fps)

            # ----------------------------
            # DASHBOARD DISABLED
            # ----------------------------
            

            # ----------------------------
            # ----------------------------
            # BRAIN + ALERTS DISABLED
            # ----------------------------

            for det in scene_data:

                obj_id = det.get("id", -1)

                motion = next(
                    (m for m in motions if m["id"] == det.get("id")),
                    None
                )

                message = self.brain.generate_message(det, motion)

                key = f"brain_{det['label']}_{det['zone']}"

                if self.can_trigger(key):

                    print("[BRAIN]", message)

                    threading.Thread(
                        target=self.speak_safe,
                        args=(message,),
                        daemon=True
                    ).start()

            #         web_api.push_alert(
            #             message,
            #             det["priority"]
            #         )

            # ----------------------------
            # DRAW UI
            # ----------------------------
            self.draw_boxes(
                frame,
                detections
            )
            if self.latest_frame is not None:
                web_api.update_frame(frame)

            # ----------------------------
            # STREAM DISABLED
            # ----------------------------
            

            # ----------------------------
            # SHOW WINDOW
            # ----------------------------
            cv2.imshow(
                "Vision Assistant AI",
                frame
            )

            # ----------------------------
            # EXIT KEY
            # ----------------------------
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # ----------------------------
        # CLEANUP
        # ----------------------------
        self.cap.release()

        cv2.destroyAllWindows()