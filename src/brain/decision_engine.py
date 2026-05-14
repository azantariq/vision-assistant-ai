import time


class DecisionEngine:
    """
    Central AI brain that converts raw detections + motion
    into meaningful assistant-level messages.
    """

    def __init__(self):

        self.last_messages = {}
        self.cooldown = 2.5

    def should_speak(self, key):

        current_time = time.time()
        last_time = self.last_messages.get(key, 0)

        if current_time - last_time < self.cooldown:
            return False

        self.last_messages[key] = current_time
        return True

    def generate_message(self, det, motion=None):

        label = det["label"]
        zone = det["zone"]
        priority = det["priority"]

        # Base message
        message = ""

        # -----------------------------
        # HIGH RISK OBJECTS
        # -----------------------------
        if priority == "HIGH":

            if motion and motion.get("motion") == "APPROACHING":
                message = f"Warning! {label} is approaching from {zone}"
            else:
                message = f"Warning! {label} detected on your {zone}"

        # -----------------------------
        # MEDIUM RISK
        # -----------------------------
        elif priority == "MEDIUM":

            if motion and motion.get("direction") != "STABLE":
                message = f"{label} moving on your {motion['direction'].lower()} side"
            else:
                message = f"{label} detected on {zone}"

        # -----------------------------
        # LOW RISK
        # -----------------------------
        else:
            message = f"{label} detected"

        return message

    def compute_risk_score(self, priority, motion):

        score = 0

        if priority == "HIGH":
            score += 70
        elif priority == "MEDIUM":
            score += 40
        else:
            score += 10

        if motion:

            if motion.get("motion") == "APPROACHING":
                score += 25

            if abs(motion.get("vx", 0)) > 20:
                score += 10

        return min(score, 100)