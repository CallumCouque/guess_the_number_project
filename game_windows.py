import tkinter as tk
from tkinter import messagebox
import random
import subprocess
import ctypes
import os
import winsound

# Audio Subsystem for Windows
def play_background_music(filename="background.mp3"):
    """Plays background MP3 music continuously using Windows Multimedia API."""
    if os.path.exists(filename):
        try:
            alias = "bgm"
            ctypes.windll.winmm.mciSendStringW(f'open "{filename}" type mpegvideo alias {alias}', None, 0, None)
            ctypes.windll.winmm.mciSendStringW(f'play {alias} repeat', None, 0, None)
        except Exception:
            pass

def speak_text(text):
    """Uses Windows PowerShell for asynchronous text to speech alerts."""
    try:
        cmd = f'powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{text}\')"'
        subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception:
        pass

def play_alert_beep():
    """Triggers a native Windows system beep for feedback."""
    try:
        winsound.Beep(1000, 150)
    except Exception:
        pass

# Colour Palettes and Level Configurations
THEMES = {
    1: {"bg": "#1E1E24", "fg": "#FFFFFF", "accent": "#44BBA4", "banner": "LEVEL 1: THE BEGINNING", "attempts": 7},
    2: {"bg": "#1B2A4A", "fg": "#FFFFFF", "accent": "#0090C1", "banner": "LEVEL 2: GETTING WARMER", "attempts": 6},
    3: {"bg": "#321325", "fg": "#FFFFFF", "accent": "#E09F3E", "banner": "LEVEL 3: HEATING UP", "attempts": 5},
    4: {"bg": "#2C0E37", "fg": "#FFFFFF", "accent": "#A100F2", "banner": "LEVEL 4: ADVANCED DEDUCTION", "attempts": 4},
    5: {"bg": "#3F000F", "fg": "#FFFFFF", "accent": "#D62828", "banner": "LEVEL 5: SUDDEN DEATH", "attempts": 3}
}

class GuessTheNumberWindows:
    def __init__(self, root):
        self.root = root
        self.root.title("Guess the Number: Windows Edition")
        self.root.geometry("550x650")
        self.root.resizable(False, False)
        
        # Game State Variables
        self.current_level = 1
        self.secret_number = 0
        self.attempts_left = 0
        self.past_guesses = set()
        self.guess_sequence = []
        self.history_visible = False
        
        # Statistics Tracking
        self.games_played = 0
        self.total_wins = 0
        self.best_round = None
        self.peak_level = 1
        
        self.setup_gui()
        self.start_new_round()
        play_background_music("background.mp3")
        speak_text("Welcome to Guess the Number Windows Edition.")

    def setup_gui(self):
        # Main Container
        self.main_frame = tk.Frame(self.root, bd=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Banner Label
        self.banner_label = tk.Label(self.main_frame, text="", font=("Arial", 16, "bold"), pady=10)
        self.banner_label.pack(fill=tk.X)
        
        # Instruction and Feedback
        self.prompt_label = tk.Label(self.main_frame, text="Guess a number between 1 and 100:", font=("Arial", 12))
        self.prompt_label.pack(pady=10)
        
        self.feedback_label = tk.Label(self.main_frame, text="Good Luck!", font=("Arial", 14, "bold"), height=2)
        self.feedback_label.pack(pady=5)
        
        self.attempts_label = tk.Label(self.main_frame, text="", font=("Arial", 12, "italic"))
        self.attempts_label.pack(pady=5)
        
        # Input Field and Submit Button
        self.entry_box = tk.Entry(self.main_frame, font=("Arial", 16), justify="center", width=10)
        self.entry_box.pack(pady=10)
        self.entry_box.bind("<Return>", lambda event: self.process_guess())
        
        self.submit_btn = tk.Button(self.main_frame, text="SUBMIT GUESS", font=("Arial", 12, "bold"), command=self.process_guess, cursor="hand2")
        self.submit_btn.pack(pady=5)
        
        # Dashboard Panel
        self.stats_frame = tk.LabelFrame(self.main_frame, text=" Performance Dashboard ", font=("Arial", 10, "bold"), padx=10, pady=10)
        self.stats_frame.pack(fill=tk.X, pady=15)
        
        self.stats_label = tk.Label(self.stats_frame, text="", font=("Courier New", 10), justify="left")
        self.stats_label.pack()
        
        # History Drawer Toggle
        self.history_btn = tk.Button(self.main_frame, text="Show History Drawer", font=("Arial", 10), command=self.toggle_history)
        self.history_btn.pack(pady=5)
        
        self.history_listbox = tk.Listbox(self.main_frame, font=("Courier New", 10), height=6)
        
        self.update_dashboard()

    def start_new_round(self):
        theme = THEMES[self.current_level]
        self.secret_number = random.randint(1, 100)
        self.attempts_left = theme["attempts"]
        self.past_guesses.clear()
        self.guess_sequence.clear()
        self.update_history_drawer()
        self.apply_theme(theme)
        self.feedback_label.config(text="Enter your first guess below.")
        self.update_attempts_display()
        self.entry_box.delete(0, tk.END)

    def apply_theme(self, theme):
        self.main_frame.config(bg=theme["bg"])
        self.banner_label.config(text=theme["banner"], bg=theme["accent"], fg="#000000")
        self.prompt_label.config(bg=theme["bg"], fg=theme["fg"])
        self.feedback_label.config(bg=theme["bg"], fg=theme["accent"])
        self.attempts_label.config(bg=theme["bg"], fg=theme["fg"])
        self.stats_frame.config(bg=theme["bg"], fg=theme["accent"])
        self.stats_label.config(bg=theme["bg"], fg=theme["fg"])
        self.history_btn.config(bg=theme["accent"], fg="#000000")

    def update_attempts_display(self):
        self.attempts_label.config(text=f"Attempts Remaining: {self.attempts_left}")

    def update_dashboard(self):
        win_rate = (self.total_wins / self.games_played * 100) if self.games_played > 0 else 0.0
        best_text = f"{self.best_round} attempts" if self.best_round else "N/A"
        grade = self.calculate_grade(win_rate)
        
        stats_text = (
            f"Games Played: {self.games_played:<5} Win Rate: {win_rate:.1f}%\n"
            f"Total Wins:   {self.total_wins:<5} Best Run: {best_text}\n"
            f"Peak Level:   {self.peak_level:<5} Grade:    {grade}"
        )
        self.stats_label.config(text=stats_text)

    def calculate_grade(self, win_rate):
        if self.games_played == 0:
            return "N/A"
        if self.peak_level == 5 and win_rate >= 80:
            return "A+"
        elif win_rate >= 70:
            return "A"
        elif win_rate >= 50:
            return "B"
        elif win_rate >= 30:
            return "C"
        else:
            return "F"

    def toggle_history(self):
        if self.history_visible:
            self.history_listbox.pack_forget()
            self.history_btn.config(text="Show History Drawer")
            self.root.geometry("550x650")
            self.history_visible = False
        else:
            self.history_listbox.pack(fill=tk.X, padx=10, pady=5)
            self.history_btn.config(text="Hide History Drawer")
            self.root.geometry("550x760")
            self.history_visible = True

    def update_history_drawer(self):
        self.history_listbox.delete(0, tk.END)
        for idx, guess in enumerate(self.guess_sequence, 1):
            self.history_listbox.insert(tk.END, f"Attempt {idx}: Guessed {guess}")

    def trigger_strobe_flash(self):
        original_bg = THEMES[self.current_level]["bg"]
        self.main_frame.config(bg="#FFFFFF")
        self.root.after(300, lambda: self.main_frame.config(bg=original_bg))

    def process_guess(self):
        input_val = self.entry_box.get().strip()
        self.entry_box.delete(0, tk.END)
        
        if not input_val.isdigit():
            self.feedback_label.config(text="Error: Please enter a whole number.")
            play_alert_beep()
            speak_text("Please enter a valid number.")
            return
            
        guess = int(input_val)
        if guess < 1 or guess > 100:
            self.feedback_label.config(text="Error: Guess must be between 1 and 100.")
            play_alert_beep()
            speak_text("Number out of range.")
            return
            
        if guess in self.past_guesses:
            self.feedback_label.config(text=f"Warning: You already guessed {guess}!")
            play_alert_beep()
            speak_text("Duplicate guess. Try another number.")
            return

        # Valid new guess processing
        self.past_guesses.add(guess)
        self.guess_sequence.append(guess)
        self.update_history_drawer()
        self.trigger_strobe_flash()
        self.attempts_left -= 1
        self.update_attempts_display()
        
        if guess == self.secret_number:
            self.handle_victory()
        elif self.attempts_left == 0:
            self.handle_defeat()
        elif guess < self.secret_number:
            self.feedback_label.config(text="Too Low! Aim higher.")
            speak_text("Too low.")
        else:
            self.feedback_label.config(text="Too High! Aim lower.")
            speak_text("Too high.")

    def handle_victory(self):
        self.games_played += 1
        self.total_wins += 1
        attempts_used = THEMES[self.current_level]["attempts"] - self.attempts_left
        
        if self.best_round is None or attempts_used < self.best_round:
            self.best_round = attempts_used
            
        speak_text("Correct! You cleared the level.")
        
        if self.current_level == 5:
            self.peak_level = 5
            self.update_dashboard()
            self.show_championship_screen()
        else:
            self.current_level += 1
            if self.current_level > self.peak_level:
                self.peak_level = self.current_level
            self.update_dashboard()
            messagebox.showinfo("Level Cleared", f"Spot on! Advancing to Level {self.current_level}.")
            self.start_new_round()

    def handle_defeat(self):
        self.games_played += 1
        self.update_dashboard()
        speak_text("Out of attempts. Game over.")
        messagebox.showinfo("Game Over", f"You ran out of attempts. The number was {self.secret_number}.\nResetting back to Level 1.")
        self.current_level = 1
        self.start_new_round()

    def show_championship_screen(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        self.main_frame.config(bg="#FFD700")
        title = tk.Label(self.main_frame, text="CHAMPIONSHIP VICTORY!", font=("Arial", 22, "bold"), bg="#FFD700", fg="#000000", pady=20)
        title.pack()
        
        msg = tk.Label(self.main_frame, text="You conquered all 5 levels of Guess the Number!", font=("Arial", 14), bg="#FFD700", fg="#000000", pady=10)
        msg.pack()
        
        speak_text("Congratulations! You are the ultimate champion.")
        
        btn = tk.Button(self.main_frame, text="PLAY AGAIN FROM LEVEL 1", font=("Arial", 12, "bold"), command=self.restart_campaign, bg="#000000", fg="#FFFFFF", padx=10, pady=5)
        btn.pack(pady=30)

    def restart_campaign(self):
        self.current_level = 1
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.setup_gui()
        self.start_new_round()

if __name__ == "__main__":
    root = tk.Tk()
    app = GuessTheNumberWindows(root)
    root.mainloop()