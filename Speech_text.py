import speech_recognition as sr
import pyttsx3
import threading

recognizer = sr.Recognizer()
engine = None
speech_thread = None
stop_flag = threading.Event()

def speak(text):
    global engine, speech_thread

    def run_speech():
        global engine
        try:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[ERROR in speak()]: {e}")
        finally:
            engine = None

    stop_flag.clear()
    speech_thread = threading.Thread(target=run_speech)
    speech_thread.start()

def stop_speaking():
    global engine, speech_thread
    stop_flag.set()
    if engine:
        try:
            engine.stop()
        except Exception as e:
            print(f"[ERROR in stop_speaking()]: {e}")
        engine = None
    if speech_thread and speech_thread.is_alive():
        speech_thread.join(timeout=1)

def listen_to_user():
    with sr.Microphone() as mic:
        recognizer.adjust_for_ambient_noise(mic, duration=0.2)
        print("Listening...")
        audio = recognizer.listen(mic)
        try:
            text = recognizer.recognize_google(audio).lower()
            print(f"Recognized: {text}")
            return text
        except sr.UnknownValueError:
            return "Sorry, I didn't catch that."
        except sr.RequestError:
            return "Sorry, speech recognition is not available."

