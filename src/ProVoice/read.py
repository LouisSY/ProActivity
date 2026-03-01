import pyttsx3
engine = pyttsx3.init()
with open('new.txt', 'r', encoding='utf-8') as f:
    text = f.read()
engine.say(text)
engine.runAndWait()
