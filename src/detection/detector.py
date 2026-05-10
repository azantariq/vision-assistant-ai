import cv2

class ObjectDetector:
    def __init__(self, model, conf_threshold=0.5):
        self.model = model
        self.conf_threshold = conf_threshold

    def detect(self, frame):
        """
        Runs YOLO detection on a single frame
        """
        results = self.model(frame)[0]

        detections = []

        for box in results.boxes:
            conf = float(box.conf[0])

            if conf < self.conf_threshold:
                continue

            cls_id = int(box.cls[0])
            label = self.model.names[cls_id]

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            detections.append({
                "label": label,
                "confidence": conf,
                "bbox": (x1, y1, x2, y2)
            })

        return detections