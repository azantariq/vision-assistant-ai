import cv2
import time
import threading
import uvicorn

# import web_api

from src.detection.model_loader import YOLOModelLoader
from src.analysis.scene_analyzer import SceneAnalyzer
from src.audio.voice_engine import VoiceEngine

# from src.ocr.ocr_engine import OCREngine
# from src.ocr.text_filter import OCRTextFilter
# from src.brain.decision_engine import DecisionEngine

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
        # self.voice = VoiceEngine()

        # self.brain = DecisionEngine()

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

        # ----------------------------
        # MOTION TRACKING MEMORY
        # ----------------------------
        self.track_memory = {}

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
        # def start_api():
        #     uvicorn.run(
        #         web_api.app,
        #         host="127.0.0.1",
        #         port=8001,
        #         log_level="warning"
        #     )

        # threading.Thread(
        #     target=start_api,
        #     daemon=True
        # ).start()

        # print("[INFO] FastAPI bridge started on port 8001")

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

            # ----------------------------
            # MOTION ANALYSIS
            # ----------------------------
            motions = self.update_motion(detections)

            # ----------------------------
            # PRINT MOTION INFO
            # ----------------------------
            for motion in motions:

                obj_id = motion["id"]

                current_state = (
                    motion["direction"],
                    motion["motion"]
                )

                previous_state = self.last_motion_state.get(obj_id)

                # print only if state changes
                if current_state != previous_state:

                    print(
                        f"[MOTION] "
                        f"ID={obj_id} "
                        f"{motion['direction']} "
                        f"{motion['motion']}"
                    )

                    self.last_motion_state[obj_id] = current_state

            # ----------------------------
            # SCENE ANALYSIS DISABLED
            # ----------------------------
            scene_data = self.analyzer.analyze(
                detections,
                width,
                height
            )
            for item in scene_data:

                print(
                    f"[SCENE] "
                    f"{item['label']} | "
                    f"{item['zone']} | "
                    f"{item['distance']} | "
                    f"Risk={item['risk_score']}"
                    )

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

            cv2.putText(
                frame,
                f"FPS: {int(fps)}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 0, 0),
                2
            )

            # ----------------------------
            # DASHBOARD DISABLED
            # ----------------------------
            # web_api.update_state(
            #     fps=fps,
            #     object_count=len(detections),
            #     risk_avg=0,
            #     voice_active=True,
            #     last_spoken="",
            #     is_speaking=False,
            #     queue_size=0
            # )

            # ----------------------------
            # BRAIN + ALERTS DISABLED
            # ----------------------------
            # for det in scene_data:

            #     motion = next(
            #         (
            #             m for m in motions
            #             if m["id"] == det.get("id")
            #         ),
            #         None
            #     )

            #     message = self.brain.generate_message(
            #         det,
            #         motion
            #     )

            #     key = (
            #         f"{det['label']}_{det['zone']}"
            #     )

            #     if self.brain.should_speak(key):

            #         print(
            #             "[BRAIN ALERT]",
            #             message
            #         )

            #         threading.Thread(
            #             target=self.voice.speak,
            #             args=(message,),
            #             daemon=True
            #         ).start()

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

            # ----------------------------
            # STREAM DISABLED
            # ----------------------------
            # web_api.update_frame(frame)

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