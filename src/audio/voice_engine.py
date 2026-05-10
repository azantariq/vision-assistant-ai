import pyttsx3
import threading
import queue

class VoiceEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.queue = queue.Queue()

        self.engine.setProperty("rate", 160)

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while True:
            text = self.queue.get()
            if text:
                self.engine.say(text)
                self.engine.runAndWait()

    def speak(self, text):
        self.queue.put(text)