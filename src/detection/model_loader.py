from ultralytics import YOLO

class YOLOModelLoader:
    def __init__(self, model_path="yolov8n.pt"):
        self.model_path = model_path
        self.model = None

    def load_model(self):
        print("[INFO] Loading YOLOv8 model...")
        self.model = YOLO(self.model_path)
        print("[INFO] Model loaded successfully.")
        return self.model