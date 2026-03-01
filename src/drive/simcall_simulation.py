import random
import time
import threading
import pyttsx3

# Event types
EVENT_CALL = "call"
EVENT_SMS = "sms"

# --- Helper functions to play TTS in separate engine each time ---

def play_tts(text: str):
    """Play text-to-speech in a separate engine (prevents pyttsx3 only playing once)."""
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def play_tts_async(text: str):
    """Play TTS asynchronously in a thread."""
    thread = threading.Thread(target=play_tts, args=(text,))
    thread.start()
    return thread

# --- Simulate events ---

def simulate_call():
    print("Incoming call!")
    # Play ringtone asynchronously (German example)
    play_tts_async("Anruf! Bitte beantworten Sie den Anruf.")

    # Automatically reject after 5 seconds
    time.sleep(5)
    print("Call automatically rejected.")

    # In real simulator, you can add flags to stop playback if using audio file
    return EVENT_CALL

def simulate_sms():
    print("New SMS received!")
    play_tts_async("Du hast eine neue Nachricht.")  # German: You have received a new message
    return EVENT_SMS

# --- Random event loop ---

def random_event_loop():
    while True:
        # Random wait 5~15 seconds
        time.sleep(random.randint(5, 15))
        event_type = random.choice([EVENT_CALL, EVENT_SMS])
        if event_type == EVENT_CALL:
            simulate_call()
        else:
            simulate_sms()

# --- Start simulation in a background thread ---

def start_simulation():
    thread = threading.Thread(target=random_event_loop, daemon=True)
    thread.start()
    return thread

# --- Test run ---
if __name__ == "__main__":
    print("Starting call/SMS simulation. Press Ctrl+C to stop.")
    start_simulation()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Simulation stopped.")
