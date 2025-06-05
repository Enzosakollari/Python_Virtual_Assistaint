import re
import tkinter as tk
from tkinter import Entry, Label, Button
from PIL import Image, ImageTk
import cv2
import threading
from Speech_text import listen_to_user, stop_speaking,speak
import webbrowser
import subprocess
import os
import google.generativeai as genai
# Configure Gemini API
genai.configure(api_key="the Api key gotten from Google")
gemini_model = genai.GenerativeModel("gemini-1.5-flash")
gemini_chat = gemini_model.start_chat()

class AIAssistantGUI:

    def play_mic_video(self):
        ret, frame = self.mic_cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (100, 40))
            img = ImageTk.PhotoImage(Image.fromarray(frame))
            self.mic_video_label.imgtk = img
            self.mic_video_label.config(image=img)
        else:
            self.mic_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # loop the video

        self.root.after(33, self.play_mic_video)

    def __init__(self, root):
        self.root = root
        self.root.title("AI Voice Assistant")
        self.root.geometry("1100x600")
        self.root.resizable(False, False)
        self.root.configure(bg="black")

        self.video_paths = ["imag/jarvis4.mp4", "imag/voice_mode.mp4"]
        self.current_video_index = 0
        self.cap = cv2.VideoCapture(self.video_paths[self.current_video_index])

        self.voice_thread = None
        self.stop_flag = threading.Event()

        self.video_label = Label(self.root)
        self.video_label.pack(fill=tk.BOTH, expand=True)

        # self.entry = Entry(self.root, font=("Consolas", 14), bg="#101820", fg="white", insertbackground="white")
        # self.entry.place(relx=0.5, rely=1.0, anchor=tk.S, width=700, height=35)
        # self.entry.bind("<Return>", self.handle_input)
        self.entry_frame = tk.Frame(self.root, bg="black")
        self.entry_frame.place(relx=0.45, rely=0.98, anchor=tk.S, width=710, height=45)

        self.entry = Entry(
            self.entry_frame,
            font=("Consolas", 14),
            bg="#1a1a1a",
            fg="white",
            insertbackground="white",
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#333",
            highlightcolor="#555",
            bd=0
        )
        self.entry.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.entry.bind("<Return>", self.handle_input)

        self.response_label = Label(self.root, text="", font=("Consolas", 14), fg="white", bg="black",
                                    wraplength=700, justify="center")
        self.response_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.response_label.lower()

        try:
            mic_img = Image.open("imag/mic.jpg").resize((35, 35), Image.Resampling.LANCZOS)
            self.mic_icon = ImageTk.PhotoImage(mic_img)
        except Exception as e:
            print(f"Mic image error: {e}")
            self.mic_icon = None
        try:
            stop_img = Image.open("imag/stop1.png").resize((70,70), Image.Resampling.LANCZOS)
            self.stop_icon = ImageTk.PhotoImage(stop_img)
        except Exception as e:
            print(f"Stop image error: {e}")
            self.stop_icon = None

        # self.mic_button = Button(self.root, image=self.mic_icon if self.mic_icon else None, text="🎙️" if not self.mic_icon else "",
        #                          font=("Consolas", 14), command=self.start_voice_thread,
        #                          bg="black", fg="white", activebackground="#101820", activeforeground="white",
        #                          relief=tk.FLAT, borderwidth=1)
        # self.mic_button.place(x=900, y=565, width=50, height=35)
        self.mic_cap = cv2.VideoCapture("imag/mic2.mp4")  # put your mic video path here
        self.mic_video_label = Label(self.root, bg="black", cursor="hand2")
        self.mic_video_label.place(x=850, y=540, width=110, height=50)
        self.mic_video_label.bind("<Button-1>", lambda e: self.start_voice_thread())

        self.play_mic_video()  # start playing the video

        self.stop_button = Button(
            self.root,
            image=self.stop_icon if self.stop_icon else None,
            text="⏹" if not self.stop_icon else "",
            font=("Consolas", 14),
            command=self.stop_processing,
            bg="black",
            fg="white",
            activebackground="darkred",
            activeforeground="white",
            relief=tk.FLAT,
            borderwidth=1
        )
        self.stop_button.place(x=960, y=545, width=50, height=35)

        self.play_video()

    def start_voice_thread(self):
        if self.voice_thread is None or not self.voice_thread.is_alive():
            self.stop_flag.clear()
            self.voice_thread = threading.Thread(target=self.voice_to_ai)
            self.voice_thread.start()

    def stop_processing(self):
        self.stop_flag.set()

        # Stop voice output
        stop_speaking()

        self.clear_response()
        self.switch_video(0)

    def play_video(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            win_width = self.root.winfo_width()
            win_height = self.root.winfo_height()
            frame = cv2.resize(frame, (win_width, win_height))
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        self.root.after(25, self.play_video)

    def switch_video(self, index):
        if 0 <= index < len(self.video_paths):
            self.current_video_index = index
            self.cap.release()
            self.cap = cv2.VideoCapture(self.video_paths[self.current_video_index])

      # Add this at the top of your file if not already imported

    def get_ai_response(self, prompt):
        if self.stop_flag.is_set():
            return "Processing stopped."
        try:
            response = gemini_chat.send_message(prompt)
            raw_text = response.text.strip()

            # Remove Markdown asterisks like *, **, bullet points, etc.
            cleaned_text = re.sub(r"\*+", "", raw_text)

            return cleaned_text
        except Exception as e:
            return f"Error: {e}"

    def fade_in_text(self, text):
        self.response_label.config(text=text)
        self.response_label.lift()

        for i in range(0, 21):
            if self.stop_flag.is_set():
                return
            brightness = int((i / 20) * 255)
            color = f"#{brightness:02x}{brightness:02x}{brightness:02x}"
            self.response_label.config(fg=color)
            self.root.update()
            self.root.after(30)

        self.root.after(3000, self.fade_out_text)

    def fade_out_text(self):
        for i in range(20, -1, -1):
            if self.stop_flag.is_set():
                return
            brightness = int((i / 20) * 255)
            color = f"#{brightness:02x}{brightness:02x}{brightness:02x}"
            self.response_label.config(fg=color)
            self.root.update()
            self.root.after(30)
        self.clear_response()

    def clear_response(self):
        self.response_label.config(text="")
        self.response_label.lower()

    def process_prompt(self, prompt):
        if self.stop_flag.is_set():
            return
        command_response = self.open_command_handler(prompt)
        if command_response:
            if not self.stop_flag.is_set():
                self.fade_in_text(command_response)
                speak(command_response)
        else:
            response = self.get_ai_response(prompt)
            if not self.stop_flag.is_set():
                self.fade_in_text(response)
                speak(response)

    def handle_input(self, event=None):
        user_input = self.entry.get()
        self.entry.delete(0, tk.END)
        self.clear_response()
        self.stop_flag.clear()
        threading.Thread(target=self.process_prompt, args=(user_input,)).start()

    def voice_to_ai(self):
        self.switch_video(1)
        if self.stop_flag.is_set():
            return
        user_input = listen_to_user()
        if self.stop_flag.is_set():
            return
        self.switch_video(0)
        self.clear_response()
        response = self.get_ai_response(user_input)
        if not self.stop_flag.is_set():
            self.fade_in_text(response)
            speak(response)

    def open_command_handler(self, command):
        command = command.lower()

        if "open brave" in command:
            brave_path = r"C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
            try:
                subprocess.Popen([brave_path])
                return "Opening Brave browser..."
            except Exception as e:
                return f"Failed to open Brave: {e}"

        elif "open youtube" in command:
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube..."

        elif "open google" in command:
            webbrowser.open("https://www.google.com")
            return "Opening Google..."

        elif "open chat gpt" in command:
            webbrowser.open("https://chat.openai.com")
            return "Opening ChatGPT..."

        elif "open instagram" in command:
            webbrowser.open("https://www.instagram.com")
            return "Opening Instagram..."

        elif "open pinterest" in command:
            webbrowser.open("https://www.pinterest.com")
            return "Opening Pinterest..."

        elif "open pycharm" in command:
            pycharm_path = r"C:\\Program Files\\JetBrains\\PyCharm 2025\\bin\\pycharm64.exe"
            try:
                subprocess.Popen([pycharm_path])
                return "Opening PyCharm 2025..."
            except Exception as e:
                return f"Failed to open PyCharm: {e}"
        else:
            return None
if __name__ == "__main__":
    root = tk.Tk()
    app = AIAssistantGUI(root)
    root.mainloop()
