import time

class AlertManager:
    def __init__(self):
        self.last_alert_time = {}
        self.cooldown = 3.0

        self.priority_rank = {
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1
        }

    def should_alert(self, key, priority):
        current_time = time.time()
        last_time = self.last_alert_time.get(key, 0)

        if current_time - last_time < self.cooldown:
            return False

        self.last_alert_time[key] = current_time
        return True

    def generate_message(self, item):
        label = item["label"]
        zone = item["zone"]
        priority = item["priority"]

        if priority == "HIGH":
            return f"Warning! {label} ahead from {zone}"
        elif priority == "MEDIUM":
            return f"{label} detected on {zone}"
        else:
            return f"{label} on {zone}"