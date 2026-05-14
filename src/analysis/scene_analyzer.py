import time


class SceneAnalyzer:
    def __init__(self):

        self.last_alert_time = {}
        self.cooldown = 2.0

        self.zones = ["LEFT", "CENTER", "RIGHT"]

        # tracking memory
        self.prev_positions = {}
        self.prev_time = {}

        # Priority system
        self.priority_map = {
            "car": "HIGH",
            "bus": "HIGH",
            "motorcycle": "HIGH",
            "bicycle": "HIGH",
            "person": "MEDIUM",
            "stairs": "MEDIUM",
            "chair": "LOW",
            "bottle": "LOW"
        }

    # ----------------------------
    # ZONE DETECTION
    # ----------------------------
    def get_zone(self, x1, x2, frame_width):
        center_x = (x1 + x2) / 2

        if center_x < frame_width / 3:
            return "LEFT"
        elif center_x < (frame_width * 2 / 3):
            return "CENTER"
        else:
            return "RIGHT"

    # ----------------------------
    # DISTANCE ESTIMATION
    # ----------------------------
    def estimate_distance(self, bbox, frame_width, frame_height):

        x1, y1, x2, y2 = bbox

        area = (x2 - x1) * (y2 - y1)
        frame_area = frame_width * frame_height

        ratio = area / frame_area

        if ratio > 0.4:
            return "VERY_CLOSE"
        elif ratio > 0.2:
            return "CLOSE"
        elif ratio > 0.05:
            return "MEDIUM"
        else:
            return "FAR"

    # ----------------------------
    # MAIN ANALYSIS ENGINE
    # ----------------------------
    def analyze(self, detections, frame_width, frame_height):
        scene_output = []
        current_time = time.time()

        for det in detections:
            label = det["label"]
            confidence = det["confidence"]
            x1, y1, x2, y2 = det["bbox"]

            zone = self.get_zone(x1, x2, frame_width)
            priority = self.priority_map.get(label, "LOW")

            # ----------------------------
            # DISTANCE
            # ----------------------------
            distance = self.estimate_distance(
                det["bbox"],
                frame_width,
                frame_height
                )

            # ----------------------------
            # MOTION (SPEED ESTIMATION)
            # ----------------------------
            key = f"{label}_{det.get('id', -1)}"

            center_x = (x1 + x2) / 2

            prev_x = self.prev_positions.get(key, None)
            prev_t = self.prev_time.get(key, None)

            speed = "UNKNOWN"

            if prev_x is not None and prev_t is not None:
                dx = center_x - prev_x
                dt = current_time - prev_t

                if dt > 0:
                    velocity = dx / dt

                    if abs(velocity) > 50:
                        speed = "FAST"
                    elif abs(velocity) > 20:
                        speed = "MEDIUM"
                    else:
                        speed = "SLOW"

            self.prev_positions[key] = center_x
            self.prev_time[key] = current_time

            # ----------------------------
            # RISK SCORING SYSTEM
            # ----------------------------
            risk_score = 0

            # priority weight
            risk_score += {"HIGH": 3, "MEDIUM": 2, "LOW": 1}[priority]

            # distance weight
            if distance == "VERY_CLOSE":
                risk_score += 3
            elif distance == "CLOSE":
                risk_score += 2
            else:
                risk_score += 1

            # speed weight
            if speed == "FAST":
                risk_score += 3
            elif speed == "MEDIUM":
                risk_score += 2
            else:
                risk_score += 1

            # ----------------------------
            # ALERT COOLDOWN
            # ----------------------------
            message_key = f"{label}_{zone}"

            last_time = self.last_alert_time.get(message_key, 0)

            if current_time - last_time < self.cooldown:
                continue

            self.last_alert_time[message_key] = current_time

            # ----------------------------
            # INTELLIGENT MESSAGE ENGINE
            # ----------------------------
            if risk_score >= 7:
                message = f"WARNING! {label} approaching quickly from {zone}"
            elif risk_score >= 5:
                message = f"{label} is close on {zone}"
            else:
                message = f"{label} on {zone}"

            scene_output.append({
                "message": message,
                "priority": priority,
                "zone": zone,
                "label": label,
                "confidence": confidence,
                "distance": distance,
                "speed": speed,
                "risk_score": risk_score
            })

        return scene_output