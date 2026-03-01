import pyttsx3
import threading

class VoiceEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.lock = threading.Lock()

    def say(self, text: str):
        with self.lock:
            self.engine.say(text)
            self.engine.runAndWait()

    def say_async(self, text: str):
        thread = threading.Thread(target=self.say, args=(text,))
        thread.start()
        return thread

voice_engine = VoiceEngine()



""""
from voice import voice_engine

voice_engine.say_async("Das ist ein Test")
"""