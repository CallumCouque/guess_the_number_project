"""
Python Game Development Project: Guess the Number (Themed macOS GUI Version)
Description: An enhanced visual guessing game with dynamic level themes, text graphic designs,
             keyboard binds, centred window positioning, and non-blocking background audio.
Features:    Adaptive voice alerts, rapid visual strobe flash, defensive duplicate guess validation,
             a togglable sliding previous guess drawer, and live performance stats tracking.
"""

import random
import os
import subprocess
import threading
import time
import tkinter as tk
from tkinter import messagebox

# ==============================================================================
# 1. SYSTEM CONFIGURATIONS & COMPATIBILITY LAYER
# ==============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR:
    os.chdir(SCRIPT_DIR)

# ==============================================================================
# 2. GLOBAL STATES & DATA STRUCTURES
# ==============================================================================

TOTAL_GAMES_PLAYED = 0
TOTAL_WINS = 0
BEST_SCORE = float('inf')
WORST_SCORE = 0

CURRENT_LEVEL = 1
SECRET_NUMBER = 0
ATTEMPTS_LEFT = 7
ATTEMPTS_TAKEN = 0

PAST_GUESSES = set()      # Memory set used for anti-cheat validation checks
GUESS_ORDER_LOG = []      # Ordered list tracking the exact sequence of attempts for display
IS_HISTORY_VISIBLE = False # Tracks visibility state of the history display box

IS_MUSIC_PLAYING = True
MUSIC_PROCESS = None

THEMES = {
    1: {
        "graphic": "🌲 ♣ 🌲 ♣ 🌲 ♣ 🌲 ♣ 🌲 ♣ 🌲",
        "bg": "#1E2A22", "title_fg": "#A3E2A6", "text_fg": "#ECEFF1", "accent": "#4E7055", "box_bg": "#141C17"
    },
    2: {
        "graphic": "❄ ✨ ❄ ✨ ❄ ✨ ❄ ✨ ❄ ✨ ❄",
        "bg": "#2A313D", "title_fg": "#A5C6E1", "text_fg": "#F0F4F8", "accent": "#52677B", "box_bg": "#1D232A"
    },
    3: {
        "graphic": "☀️ 🏜️ ☀️ 🏜️ ☀️ 🏜️ ☀️ 🏜️ ☀️ 🏜️ ☀️",
        "bg": "#2E241F", "title_fg": "#EAA872", "text_fg": "#F9F3EB", "accent": "#725643", "box_bg": "#211A16"
    },
    4: {
        "graphic": "🔥 🌋 🔥 🌋 🔥 🌋 🔥 🌋 🔥 🌋 🔥",
        "bg": "#261919", "title_fg": "#F07171", "text_fg": "#FFF0F0", "accent": "#662929", "box_bg": "#1A1010"
    },
    5: {
        "graphic": "⚡ 👾 ⚡ 👾 ⚡ 👾 ⚡ 👾 ⚡ 👾 ⚡",
        "bg": "#1E1A2A", "title_fg": "#E066FF", "text_fg": "#F3EFFF", "accent": "#5E2B8A", "box_bg": "#13101C"
    }
}

# ==============================================================================
# 3. CORE AUDIO SUBSYSTEM
# ==============================================================================

def speak_mac(text):
    """
    Triggers the native macOS speech synthesis engine asynchronously
    via independent subprocess hooks to isolate the Tkinter canvas loop.
    """
    try:
        subprocess.Popen(["say", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def stop_voice_overlays():
    """
    Forcefully terminates any queued speech tasks to avoid overlapping audio.
    """
    try:
        subprocess.Popen(["killall", "say"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def background_music_loop():
    """
    Ambient track background loader. Operates on a separate threading loop
    and forces a low gain volume configuration.
    """
    global MUSIC_PROCESS
    
    possible_files = ["background.mp3", "background.wav", "background.m4a", "background", "background.MP3"]
    music_track = None
    
    for filename in possible_files:
        full_path = os.path.join(SCRIPT_DIR, filename)
        if os.path.exists(full_path):
            music_track = full_path
            break

    while IS_MUSIC_PLAYING:
        if music_track:
            try:
                MUSIC_PROCESS = subprocess.Popen(["afplay", "-v", "0.1", music_track], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                MUSIC_PROCESS.wait()
            except Exception:
                time.sleep(2)
        else:
            fallback = "/System/Library/Sounds/Subtle.afclip"
            if os.path.exists(fallback):
                try:
                    MUSIC_PROCESS = subprocess.Popen(["afplay", "-v", "0.1", fallback], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    MUSIC_PROCESS.wait()
                except Exception:
                    time.sleep(2)
            else:
                time.sleep(2)


def toggle_music():
    """
    Switches the background soundtrack stream on or off at runtime.
    """
    global IS_MUSIC_PLAYING, MUSIC_PROCESS, music_thread
    
    if IS_MUSIC_PLAYING:
        IS_MUSIC_PLAYING = False
        if MUSIC_PROCESS:
            MUSIC_PROCESS.terminate()
        music_button.config(text="🔈 Turn Music On")
    else:
        IS_MUSIC_PLAYING = True
        music_button.config(text="🔊 Mute Music")
        music_thread = threading.Thread(target=background_music_loop, daemon=True)
        music_thread.start()

# ==============================================================================
# 4. AUDIO VISUAL GRAPHICS SUBSYSTEM
# ==============================================================================

def centre_window(window, width, height):
    """
    Calculates display geometry parameters to align the 
    application container directly to the monitor spatial centre.
    """
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    x_coordinate = int((screen_width / 2) - (width / 2))
    y_coordinate = int((screen_height / 2) - (height / 2))
    
    window.geometry(f"{width}x{height}+{x_coordinate}+{y_coordinate}")


def trigger_pulse_flash(count=0):
    """
    Asynchronous recursive colour switcher that produces a multi phase high intensity
    strobe effect spanning across visual blocks for 300 ms.
    """
    theme_id = ((CURRENT_LEVEL - 1) % len(THEMES)) + 1
    theme = THEMES[theme_id]
    
    if count < 4:
        current_bg = theme["title_fg"] if count % 2 == 0 else theme["bg"]
        current_fg = theme["bg"] if count % 2 == 0 else theme["text_fg"]
        
        root.config(bg=current_bg)
        stats_frame.config(bg=current_bg)
        graphic_bg_top.config(bg=current_bg, fg=current_fg)
        graphic_bg_bottom.config(bg=current_bg, fg=current_fg)
        level_label.config(bg=current_bg, fg=current_fg)
        title_label.config(bg=current_bg, fg=current_fg)
        feedback_label.config(bg=current_bg, fg=current_fg)
        attempts_label.config(bg=current_bg, fg=current_fg)
        history_toggle_btn.config(bg=current_bg, fg=current_fg)
        history_display_lbl.config(bg=current_bg, fg=current_fg)
        
        root.after(75, lambda: trigger_pulse_flash(count + 1))
    else:
        reset_visual_theme()


def reset_visual_theme():
    """
    Reestablishes the standard baseline background canvas styles post strobe flash.
    """
    theme_id = ((CURRENT_LEVEL - 1) % len(THEMES)) + 1
    theme = THEMES[theme_id]
    
    root.configure(bg=theme["bg"])
    graphic_bg_top.config(text=theme["graphic"], bg=theme["bg"], fg=theme["accent"])
    graphic_bg_bottom.config(text=theme["graphic"], bg=theme["bg"], fg=theme["accent"])
    
    level_label.config(text=f"Level {CURRENT_LEVEL}", bg=theme["bg"], fg=theme["title_fg"])
    title_label.config(bg=theme["bg"], fg=theme["title_fg"])
    feedback_label.config(bg=theme["bg"], fg=theme["text_fg"])
    attempts_label.config(bg=theme["bg"], fg=theme["text_fg"])
    
    stats_frame.config(bg=theme["bg"], fg=theme["title_fg"], highlightbackground=theme["accent"])
    
    history_toggle_btn.config(bg=theme["bg"], fg=theme["title_fg"])
    history_display_lbl.config(bg=theme["box_bg"], fg=theme["text_fg"])


def toggle_history_drawer():
    """
    TOGGLE LOG FEATURE: Expands or contracts the UI container size smoothly
    to dynamically reveal or mask the live list of previous attempts.
    """
    global IS_HISTORY_VISIBLE
    
    if not IS_HISTORY_VISIBLE:
        IS_HISTORY_VISIBLE = True
        root.geometry(f"420x710")
        history_display_lbl.pack(pady=(0, 10), after=history_toggle_btn)
        history_toggle_btn.config(text="📊 Hide History")
    else:
        IS_HISTORY_VISIBLE = False
        history_display_lbl.pack_forget()
        root.geometry(f"420x650")
        history_toggle_btn.config(text="📊 View History")


def apply_theme():
    """
    Redraws colour profiles, typography variables, and pattern banners across widgets.
    """
    theme_id = ((CURRENT_LEVEL - 1) % len(THEMES)) + 1
    theme = THEMES[theme_id]
    
    root.configure(bg=theme["bg"])
    graphic_bg_top.config(text=theme["graphic"], bg=theme["bg"], fg=theme["accent"])
    graphic_bg_bottom.config(text=theme["graphic"], bg=theme["bg"], fg=theme["accent"])
    
    level_label.config(text=f"Level {CURRENT_LEVEL}", bg=theme["bg"], fg=theme["title_fg"])
    title_label.config(bg=theme["bg"], fg=theme["title_fg"])
    feedback_label.config(bg=theme["bg"], fg=theme["text_fg"])
    attempts_label.config(bg=theme["bg"], fg=theme["text_fg"])
    
    guess_entry.config(bg=theme["box_bg"], fg=theme["text_fg"], highlightbackground=theme["accent"])
    guess_button.config(bg=theme["title_fg"], fg=theme["bg"], activebackground=theme["text_fg"], activeforeground=theme["bg"])
    
    music_button.config(
        bg=theme["accent"], 
        fg="#000000", 
        activebackground=theme["title_fg"], 
        activeforeground="#000000",
        highlightbackground=theme["bg"]
    )
    
    history_toggle_btn.config(bg=theme["bg"], fg=theme["title_fg"])
    history_display_lbl.config(bg=theme["box_bg"], fg=theme["text_fg"], highlightbackground=theme["accent"])
    
    stats_frame.config(bg=theme["bg"], fg=theme["title_fg"], highlightbackground=theme["accent"])
    games_played_label.config(bg=theme["bg"], fg=theme["text_fg"])
    games_won_label.config(bg=theme["bg"], fg=theme["text_fg"])
    win_rate_label.config(bg=theme["bg"], fg=theme["text_fg"])
    best_score_label.config(bg=theme["bg"], fg=theme["text_fg"])
    worst_score_label.config(bg=theme["bg"], fg=theme["text_fg"])

# ==============================================================================
# 5. MATHEMATICAL LOGIC & PERFORMANCE SUBSYSTEM
# ==============================================================================

def update_stats_display():
    """
    Refreshes data visualizations and updates numerical stats labels inside the profile panel.
    """
    games_played_label.config(text=f"Total Games Played: {TOTAL_GAMES_PLAYED}")
    games_won_label.config(text=f"Games Won: {TOTAL_WINS}")
    
    if TOTAL_GAMES_PLAYED > 0:
        win_rate = (TOTAL_WINS / TOTAL_GAMES_PLAYED) * 100
        win_rate_label.config(text=f"Win Rate: {win_rate:.1f}%")
    else:
        win_rate_label.config(text="Win Rate: 0%")
        
    if BEST_SCORE != float('inf'):
        best_score_label.config(text=f"Best Round (Fewest Guesses): {BEST_SCORE}")
    if WORST_SCORE > 0:
        worst_score_label.config(text=f"Worst Round (Most Guesses): {WORST_SCORE}")


def refresh_history_log_label():
    """
    Formats and prints the active level's ordered tracking sequence inside the view panel.
    """
    if not GUESS_ORDER_LOG:
        history_display_lbl.config(text="No guesses recorded yet for this level.")
    else:
        formatted_list = " ➔ ".join(str(g) for g in GUESS_ORDER_LOG)
        history_display_lbl.config(text=f"Sequence: {formatted_list}")

# ==============================================================================
# 6. PRIMARY GAMEPLAY STATE MACHINE
# ==============================================================================

def start_new_round():
    """
    Wipes structural local tracking values and initializes mathematical random targets.
    """
    global SECRET_NUMBER, ATTEMPTS_LEFT, ATTEMPTS_TAKEN, PAST_GUESSES, GUESS_ORDER_LOG
    SECRET_NUMBER = random.randint(1, 100)
    
    ATTEMPTS_LEFT = max(8 - CURRENT_LEVEL, 1)
    ATTEMPTS_TAKEN = 0
    
    PAST_GUESSES.clear()
    GUESS_ORDER_LOG.clear()
    refresh_history_log_label()
    
    apply_theme()
    feedback_label.config(text="I have chosen a number between 1 and 100.")
    attempts_label.config(text=f"Attempts Remaining: {ATTEMPTS_LEFT}")
    guess_entry.delete(0, tk.END)
    guess_entry.focus()


def process_guess(event=None):
    """
    Main evaluation pipeline. Includes duplicate validation and history tracking log.
    """
    global TOTAL_GAMES_PLAYED, TOTAL_WINS, BEST_SCORE, WORST_SCORE, ATTEMPTS_LEFT, ATTEMPTS_TAKEN, CURRENT_LEVEL
    
    user_input = guess_entry.get().strip()
    guess_entry.delete(0, tk.END)
    
    if not user_input.isdigit():
        stop_voice_overlays()
        speak_mac("Invalid input")
        messagebox.showerror("Invalid Input", "❌ Please enter a valid whole number.")
        return
        
    guess = int(user_input)
    
    if not (1 <= guess <= 100):
        stop_voice_overlays()
        speak_mac("Out of bounds")
        messagebox.showerror("Out of Bounds", "❌ Please guess a number between 1 and 100.")
        return
        
    # Structural Anti Cheat Protection Check
    if guess in PAST_GUESSES:
        stop_voice_overlays()
        speak_mac("Already guessed")
        messagebox.showwarning("Duplicate Guess", f"⚠️ You already tried {guess}!\nNo attempts were deducted.")
        return
        
    PAST_GUESSES.add(guess)
    GUESS_ORDER_LOG.append(guess)
    refresh_history_log_label()
        
    ATTEMPTS_LEFT -= 1
    ATTEMPTS_TAKEN += 1
    attempts_label.config(text=f"Attempts Remaining: {ATTEMPTS_LEFT}")
    
    trigger_pulse_flash()
    
    if guess == SECRET_NUMBER:
        TOTAL_GAMES_PLAYED += 1
        TOTAL_WINS += 1
        
        if ATTEMPTS_TAKEN < BEST_SCORE:
            BEST_SCORE = ATTEMPTS_TAKEN
            
        if ATTEMPTS_TAKEN > WORST_SCORE:
            WORST_SCORE = ATTEMPTS_TAKEN
            
        update_stats_display()
        stop_voice_overlays()
        speak_mac("Correct")
        messagebox.showinfo("Winner!", f"🎉 Correct! You won Level {CURRENT_LEVEL} in {ATTEMPTS_TAKEN} attempts.")
        
        CURRENT_LEVEL += 1
        start_new_round()
        return
        
    elif guess < SECRET_NUMBER:
        feedback_label.config(text=f"📉 {guess} is too low! Try a higher number.")
        stop_voice_overlays()
        if ATTEMPTS_LEFT == 1:
            speak_mac("Final chance")
        else:
            speak_mac("Too low")
    else:
        feedback_label.config(text=f"📈 {guess} is too high! Try a lower number.")
        stop_voice_overlays()
        if ATTEMPTS_LEFT == 1:
            speak_mac("Final chance")
        else:
            speak_mac("Too high")
        
    if ATTEMPTS_LEFT == 0:
        TOTAL_GAMES_PLAYED += 1
        update_stats_display()
        stop_voice_overlays()
        speak_mac("Game over")
        messagebox.showinfo("Game Over", f"💥 Out of attempts! The correct number was {SECRET_NUMBER}.\nResetting back to Level 1.")
        
        CURRENT_LEVEL = 1
        start_new_round()


def on_close():
    """
    Intercepts window closure to safely stop background audio.
    """
    global IS_MUSIC_PLAYING, MUSIC_PROCESS
    IS_MUSIC_PLAYING = False
    if MUSIC_PROCESS:
        try:
            MUSIC_PROCESS.terminate()
        except Exception:
            pass
    stop_voice_overlays()
    root.destroy()

# ==============================================================================
# 7. UNIFIED GRAPHICAL INTERFACE SETUP (ENTRY POINT)
# ==============================================================================

root = tk.Tk()
root.title("Guess the Number")
root.protocol("WM_DELETE_WINDOW", on_close)

centre_window(root, 420, 650)

graphic_bg_top = tk.Label(root, font=("Courier", 14, "bold"))
graphic_bg_top.pack(pady=(10, 5))

level_label = tk.Label(root, font=("Segoe UI", 15, "bold"))
level_label.pack(pady=2)

title_label = tk.Label(root, text="Guess the Number", font=("Segoe UI", 18, "bold"))
title_label.pack(pady=(0, 10))

feedback_label = tk.Label(root, font=("Segoe UI", 12))
feedback_label.pack(pady=5)

attempts_label = tk.Label(root, font=("Segoe UI", 11, "italic"))
attempts_label.pack(pady=5)

guess_entry = tk.Entry(root, font=("Segoe UI", 16, "bold"), width=8, justify="center", insertbackground="white", bd=0, highlightthickness=1)
guess_entry.pack(pady=15)

root.bind('<Return>', process_guess)

guess_button = tk.Button(root, text="Submit Guess (or press Enter)", command=process_guess, font=("Segoe UI", 11, "bold"), bd=0, padx=10, pady=5)
guess_button.pack(pady=10)

music_button = tk.Button(
    root, 
    text="🔊 Mute Music", 
    command=toggle_music, 
    font=("Segoe UI", 10, "bold"), 
    bd=0, 
    padx=10, 
    pady=4, 
    fg="#000000",
    activeforeground="#000000",
    highlightthickness=0
)
music_button.pack(pady=5)

history_toggle_btn = tk.Button(
    root, 
    text="📊 View History", 
    command=toggle_history_drawer, 
    font=("Segoe UI", 10, "bold"), 
    bd=0, 
    relief="flat", 
    activebackground="#000000", 
    highlightthickness=0
)
history_toggle_btn.pack(pady=5)

history_display_lbl = tk.Label(
    root, 
    text="No guesses recorded yet for this level.", 
    font=("Segoe UI", 10, "italic"), 
    padx=10, 
    pady=8, 
    bd=0, 
    highlightthickness=1,
    width=40,
    wraplength=320
)

graphic_bg_bottom = tk.Label(root, font=("Courier", 14, "bold"))
graphic_bg_bottom.pack(pady=5)

stats_frame = tk.LabelFrame(root, text=" Performance Dashboard ", font=("Segoe UI", 10, "bold"), padx=15, pady=15, bd=0, highlightthickness=1)
stats_frame.pack(pady=15, fill="both", expand="yes", padx=30)

label_styles = {"font": ("Segoe UI", 11), "anchor": "w"}
games_played_label = tk.Label(stats_frame, text="Total Games Played: 0", **label_styles)
games_played_label.pack(fill="x", pady=2)

games_won_label = tk.Label(stats_frame, text="Games Won: 0", **label_styles)
games_won_label.pack(fill="x", pady=2)

win_rate_label = tk.Label(stats_frame, text="Win Rate: 0%", **label_styles)
win_rate_label.pack(fill="x", pady=2)

best_score_label = tk.Label(stats_frame, text="Best Round: N/A", **label_styles)
best_score_label.pack(fill="x", pady=2)

worst_score_label = tk.Label(stats_frame, text="Worst Round: N/A", **label_styles)
worst_score_label.pack(fill="x", pady=2)

# ==============================================================================
# 8. BACKGROUND INITIALIZATION RUNTIME CHECKS
# ==============================================================================

music_thread = threading.Thread(target=background_music_loop, daemon=True)
music_thread.start()

start_new_round()
root.mainloop()