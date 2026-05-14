import time


class OCRTextFilter:
    def __init__(self):
        self.last_spoken = {}
        self.cooldown = 10.0

    def should_speak(self, text):

        current_time = time.time()

        text = text.lower().strip()

        # ignore tiny/noisy text
        if len(text) < 3:
            return False

        last_time = self.last_spoken.get(text, 0)

        # cooldown check
        if current_time - last_time < self.cooldown:
            return False

        self.last_spoken[text] = current_time

        return True