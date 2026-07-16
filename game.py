"""
Python Game Development Project: Guess the Number (Themed macOS GUI Version)
Description: A streamlined, minimal visual guessing game with dynamic level themes,
             centred window positioning, keyboard binds, and non-blocking background audio.
Features:    Adaptive voice alerts, 300ms color strobe flash, school performance grades (A+ to F),
             defensive duplicate guess validation, and a togglable previous guess drawer.
"""

import random
import os
import subprocess
import threading
import time
import tkinter as tk
from tkinter import messagebox

# Set working directory to script location for reliable audio loading
if os.path.dirname(os.path.abspath(__file__)):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ==============================================================================
# 1. GLOBAL STATES & THEMES
# ==============================================================================

# Consolidated session metrics
STATS = {
    "games_played": 0,
    "wins": 0,
    "best_score": float('inf'),
    "worst_score": 0,
    "highest_level": 1
}

CURRENT_LEVEL = 1
SECRET_NUMBER = 0
ATTEMPTS_LEFT = 7
ATTEMPTS_TAKEN = 0

PAST_GUESSES = set()       # Anti-cheat memory set
GUESS_ORDER_LOG = []       # Sequence history for display
IS_HISTORY_VISIBLE = False # UI drawer state
HAS_WON_GAME = False       # Campaign completion flag
IS_MUSIC_PLAYING = True
MUSIC_PROCESS = None

THEMES = {
    1: {"graphic": "🌲 ♣ 🌲 ♣ 🌲 ♣ 🌲 ♣ 🌲 ♣ 🌲", "bg": "#1E2A22", "title": "#A3E2A6", "text": "#ECEFF1", "accent": "#4E7055", "box": "#141C17"},
    2: {"graphic": "❄ ✨ ❄ ✨ ❄ ✨ ❄ ✨ ❄ ✨ ❄", "bg": "#2A313D", "title": "#A5C6E1", "text": "#F0F4F8", "accent": "#52677B", "box": "#1D232A"},
    3: {"graphic": "☀️ 🏜️ ☀️ 🏜️ ☀️ 🏜️ ☀️ 🏜️ ☀️ 🏜️ ☀️", "bg": "#2E241F", "title": "#EAA872", "text": "#F9F3EB", "accent": "#725643", "box": "#211A16"},
    4: {"graphic": "🔥 🌋 🔥 🌋 🔥 🌋 🔥 🌋 🔥 🌋 🔥", "bg": "#261919", "title": "#F07171", "text": "#FFF0F0", "accent": "#662929", "box": "#1A1010"},
    5: {"graphic": "⚡ 👾 ⚡ 👾 ⚡ 👾 ⚡ 👾 ⚡ 👾 ⚡", "bg": "#1E1A2A", "title": "#E066FF", "text": "#F3EFFF", "accent": "#5E2B8A", "box": "#13101C"}
}

# ==============================================================================
# 2. AUDIO SUBSYSTEM
# ==============================================================================

def speak_mac(text):
    """Asynchronous macOS text-to-speech output using system shell."""
    try:
        cmd = f"say {text}"
        subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def stop_voice_overlays():
    """Terminates active speech to prevent overlapping vocal alerts."""
    try:
        subprocess.Popen(["killall", "say"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def background_music_loop():
    """Searches for local audio files and loops background music at 10% volume."""
    global MUSIC_PROCESS
    possible_files = ["background.mp3", "background.wav", "background.m4a", "background", "background.MP3"]
    music_track = next((os.path.join(os.getcwd(), f) for f in possible_files if os.path.exists(f)), None)

    while IS_MUSIC_PLAYING:
        try:
            track = music_track if music_track else "/System/Library/Sounds/Subtle.afclip"
            if os.path.exists(track):
                MUSIC_PROCESS = subprocess.Popen(["afplay", "-v", "0.1", track], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                MUSIC_PROCESS.wait()
            else:
                time.sleep(2)
        except Exception:
            time.sleep(2)

def toggle_music():
    """Toggles background audio loop on or off at runtime."""
    global IS_MUSIC_PLAYING, MUSIC_PROCESS
    IS_MUSIC_PLAYING = not IS_MUSIC_PLAYING
    music_btn.config(text="🔈 Turn Music On" if not IS_MUSIC_PLAYING else "🔊 Mute Music")
    
    if not IS_MUSIC_PLAYING and MUSIC_PROCESS:
        MUSIC_PROCESS.terminate()
    elif IS_MUSIC_PLAYING:
        threading.Thread(target=background_music_loop, daemon=True).start()

# ==============================================================================
# 3. VISUAL & UI SUBSYSTEM
# ==============================================================================

def centre_window(win, width, height):
    """Centers the Tkinter window on the display monitor."""
    x = int((win.winfo_screenwidth() / 2) - (width / 2))
    y = int((win.winfo_screenheight() / 2) - (height / 2))
    win.geometry(f"{width}x{height}+{x}+{y}")

def apply_theme():
    """Updates colors and graphics across all UI widgets based on the current level."""
    if HAS_WON_GAME:
        return
    
    t = THEMES[((CURRENT_LEVEL - 1) % len(THEMES)) + 1]
    root.configure(bg=t["bg"])
    
    # Streamlined bulk styling for standard text labels
    for lbl in [level_lbl, title_lbl, stats_frame]:
        lbl.config(bg=t["bg"], fg=t["title"])
    for lbl in [feedback_lbl, attempts_lbl, games_played_lbl, games_won_lbl, win_rate_lbl, best_score_lbl, worst_score_lbl, highest_level_lbl]:
        lbl.config(bg=t["bg"], fg=t["text"])
    
    graphic_top.config(text=t["graphic"], bg=t["bg"], fg=t["accent"])
    graphic_bottom.config(text=t["graphic"], bg=t["bg"], fg=t["accent"])
    
    guess_entry.config(bg=t["box"], fg=t["text"], highlightbackground=t["accent"])
    guess_btn.config(bg=t["title"], fg=t["bg"])
    music_btn.config(bg=t["accent"], fg="#000000")
    history_toggle_btn.config(bg=t["bg"], fg=t["title"])
    history_lbl.config(bg=t["box"], fg=t["text"], highlightbackground=t["accent"])
    stats_frame.config(highlightbackground=t["accent"])
    grade_lbl.config(bg=t["bg"], fg=t["title"])

def trigger_pulse_flash(count=0):
    """Recursively flashes the background colors for 300ms to provide visual feedback."""
    if HAS_WON_GAME:
        return
    
    t = THEMES[((CURRENT_LEVEL - 1) % len(THEMES)) + 1]
    if count < 4:
        bg_col = t["title"] if count % 2 == 0 else t["bg"]
        fg_col = t["bg"] if count % 2 == 0 else t["text"]
        
        root.config(bg=bg_col)
        for widget in [stats_frame, graphic_top, graphic_bottom, level_lbl, title_lbl, feedback_lbl, attempts_lbl, history_toggle_btn, history_lbl]:
            widget.config(bg=bg_col, fg=fg_col)
            
        root.after(75, lambda: trigger_pulse_flash(count + 1))
    else:
        apply_theme()

def toggle_history_drawer():
    """Expands/contracts the UI window to reveal or hide the previous guess log."""
    global IS_HISTORY_VISIBLE
    IS_HISTORY_VISIBLE = not IS_HISTORY_VISIBLE
    
    if IS_HISTORY_VISIBLE:
        root.geometry("420x750")
        history_lbl.pack(pady=(0, 10), after=history_toggle_btn)
        history_toggle_btn.config(text="📊 Hide History")
    else:
        history_lbl.pack_forget()
        root.geometry("420x690")
        history_toggle_btn.config(text="📊 View History")

def show_victory_screen():
    """Transitions the interface to the Level 5 Campaign Cleared victory screen."""
    global HAS_WON_GAME, IS_MUSIC_PLAYING
    HAS_WON_GAME = True
    STATS["highest_level"] = 5
    
    IS_MUSIC_PLAYING = False
    if MUSIC_PROCESS:
        try:
            MUSIC_PROCESS.terminate()
        except Exception:
            pass
            
    root.configure(bg="#0B0C10")
    graphic_top.config(text="🏆 ⭐ 🏆 ⭐ 🏆 ⭐ 🏆 ⭐ 🏆 ⭐ 🏆", bg="#0B0C10", fg="#66FCF1")
    graphic_bottom.config(text="🏆 ⭐ 🏆 ⭐ 🏆 ⭐ 🏆 ⭐ 🏆 ⭐ 🏆", bg="#0B0C10", fg="#66FCF1")
    
    level_lbl.config(text="🏆 CAMPAIGN CLEARED 🏆", bg="#0B0C10", fg="#66FCF1")
    title_lbl.config(text="ULTIMATE VICTORY", bg="#0B0C10", fg="#FFFFFF")
    feedback_lbl.config(text="Congratulations! You beat all 5 Levels of Guess the Number!", bg="#0B0C10", fg="#C5C6C7")
    attempts_lbl.config(text="Check your final ranking on the Dashboard below.", bg="#0B0C10", fg="#66FCF1")
    
    for widget in [guess_entry, guess_btn, history_toggle_btn, history_lbl]:
        widget.pack_forget()
        
    music_btn.config(text="🔄 Play Again", command=reset_entire_campaign, bg="#66FCF1", fg="#000000")
    
    stats_frame.config(bg="#1F2833", fg="#66FCF1", highlightbackground="#45F3FF")
    for lbl in [games_played_lbl, games_won_lbl, win_rate_lbl, best_score_lbl, worst_score_lbl, highest_level_lbl]:
        lbl.config(bg="#1F2833", fg="#FFFFFF")
    grade_lbl.config(bg="#1F2833", fg="#66FCF1")
    
    update_stats_display()
    stop_voice_overlays()
    speak_mac("Incredible work. Campaign Complete. You are the ultimate champion.")

# ==============================================================================
# 4. GAME LOGIC & METRICS
# ==============================================================================

def calculate_performance_grade():
    """Returns an academic school grade (A+ to F) based on win rate and best score."""
    if STATS["games_played"] == 0 or STATS["wins"] == 0:
        return "N/A"
    
    win_pct = (STATS["wins"] / STATS["games_played"]) * 100
    if win_pct >= 90 and STATS["best_score"] <= 3:
        return "A+"
    
    # Streamlined grade threshold evaluation
    thresholds = [(85, "A"), (80, "A-"), (75, "B+"), (70, "B"), (60, "B-"), (55, "C+"), (50, "C"), (40, "C-")]
    for score, grade in thresholds:
        if win_pct >= score:
            return grade
    return "F"

def update_stats_display():
    """Refreshes numerical values on the dashboard."""
    games_played_lbl.config(text=f"Total Games Played: {STATS['games_played']}")
    games_won_lbl.config(text=f"Games Won: {STATS['wins']}")
    
    rate = (STATS["wins"] / STATS["games_played"] * 100) if STATS["games_played"] > 0 else 0
    win_rate_lbl.config(text=f"Win Rate: {rate:.1f}%")
    
    best = STATS["best_score"] if STATS["best_score"] != float('inf') else "N/A"
    best_score_lbl.config(text=f"Best Round: {best}")
    
    worst = STATS["worst_score"] if STATS["worst_score"] > 0 else "N/A"
    worst_score_lbl.config(text=f"Worst Round: {worst}")
    
    highest_level_lbl.config(text=f"Highest Level Achieved: Level {STATS['highest_level']}")
    grade_lbl.config(text=f"Performance Rating: {calculate_performance_grade()}")

def refresh_history_log_label():
    """Updates the sequence string in the history drawer."""
    text = " ➔ ".join(map(str, GUESS_ORDER_LOG)) if GUESS_ORDER_LOG else "No guesses recorded yet for this level."
    history_lbl.config(text=f"Sequence: {text}" if GUESS_ORDER_LOG else text)

def start_new_round():
    """Initializes targets, resets anti-cheat memory, and updates UI for a new round."""
    global SECRET_NUMBER, ATTEMPTS_LEFT, ATTEMPTS_TAKEN
    SECRET_NUMBER = random.randint(1, 100)
    ATTEMPTS_LEFT = max(8 - CURRENT_LEVEL, 1)
    ATTEMPTS_TAKEN = 0
    
    if CURRENT_LEVEL > STATS["highest_level"]:
        STATS["highest_level"] = CURRENT_LEVEL
        
    PAST_GUESSES.clear()
    GUESS_ORDER_LOG.clear()
    refresh_history_log_label()
    
    apply_theme()
    feedback_lbl.config(text="I have chosen a number between 1 and 100.")
    attempts_lbl.config(text=f"Attempts Remaining: {ATTEMPTS_LEFT}")
    guess_entry.delete(0, tk.END)
    root.focus_force()
    root.after(100, guess_entry.focus_set)

def process_guess(event=None):
    """Validates user input, checks anti-cheat rules, triggers feedback, and resolves turn state."""
    global ATTEMPTS_LEFT, ATTEMPTS_TAKEN, CURRENT_LEVEL
    if HAS_WON_GAME:
        return

    val = guess_entry.get().strip()
    guess_entry.delete(0, tk.END)
    
    if not val.isdigit() or not (1 <= int(val) <= 100):
        stop_voice_overlays()
        speak_mac("Invalid input" if not val.isdigit() else "Out of bounds")
        msg = "❌ Please enter a valid whole number." if not val.isdigit() else "❌ Please guess a number between 1 and 100."
        messagebox.showerror("Invalid Input" if not val.isdigit() else "Out of Bounds", msg)
        return
        
    guess = int(val)
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
    attempts_lbl.config(text=f"Attempts Remaining: {ATTEMPTS_LEFT}")
    trigger_pulse_flash()
    
    if guess == SECRET_NUMBER:
        STATS["games_played"] += 1
        STATS["wins"] += 1
        STATS["best_score"] = min(STATS["best_score"], ATTEMPTS_TAKEN)
        STATS["worst_score"] = max(STATS["worst_score"], ATTEMPTS_TAKEN)
        update_stats_display()
        
        if CURRENT_LEVEL == 5:
            show_victory_screen()
            return
            
        stop_voice_overlays()
        speak_mac("Correct")
        messagebox.showinfo("Winner!", f"🎉 Correct! You won Level {CURRENT_LEVEL} in {ATTEMPTS_TAKEN} attempts.")
        CURRENT_LEVEL += 1
        start_new_round()
        return
        
    feedback_lbl.config(text=f"📉 {guess} is too low! Try higher." if guess < SECRET_NUMBER else f"📈 {guess} is too high! Try lower.")
    stop_voice_overlays()
    speak_mac("Final chance" if ATTEMPTS_LEFT == 1 else ("Too low" if guess < SECRET_NUMBER else "Too high"))
        
    if ATTEMPTS_LEFT == 0:
        STATS["games_played"] += 1
        update_stats_display()
        stop_voice_overlays()
        speak_mac("Game over")
        messagebox.showinfo("Game Over", f"💥 Out of attempts! The correct number was {SECRET_NUMBER}.\nResetting back to Level 1.")
        CURRENT_LEVEL = 1
        start_new_round()

def reset_entire_campaign():
    """Resets all metrics and re-launches the campaign from Level 1."""
    global CURRENT_LEVEL, HAS_WON_GAME, IS_MUSIC_PLAYING
    for key in ["games_played", "wins", "worst_score"]:
        STATS[key] = 0
    STATS["best_score"] = float('inf')
    STATS["highest_level"] = 1
    
    CURRENT_LEVEL = 1
    HAS_WON_GAME = False
    
    guess_entry.pack(pady=15, after=attempts_lbl)
    guess_btn.pack(pady=10, after=guess_entry)
    music_btn.config(text="🔊 Mute Music", command=toggle_music)
    history_toggle_btn.pack(pady=5, after=music_btn)
    
    IS_MUSIC_PLAYING = True
    threading.Thread(target=background_music_loop, daemon=True).start()
    start_new_round()

def on_close():
    """Safely terminates audio processes upon window close."""
    global IS_MUSIC_PLAYING
    IS_MUSIC_PLAYING = False
    if MUSIC_PROCESS:
        try:
            MUSIC_PROCESS.terminate()
        except Exception:
            pass
    stop_voice_overlays()
    root.destroy()

# ==============================================================================
# 5. USER INTERFACE SETUP
# ==============================================================================

root = tk.Tk()
root.title("Guess the Number")
root.protocol("WM_DELETE_WINDOW", on_close)
centre_window(root, 420, 690)

# UI Component Initialisation
graphic_top = tk.Label(root, font=("Courier", 14, "bold"))
graphic_top.pack(pady=(10, 5))

level_lbl = tk.Label(root, font=("Segoe UI", 15, "bold"))
level_lbl.pack(pady=2)

title_lbl = tk.Label(root, text="Guess the Number", font=("Segoe UI", 18, "bold"))
title_lbl.pack(pady=(0, 10))

feedback_lbl = tk.Label(root, font=("Segoe UI", 12))
feedback_lbl.pack(pady=5)

attempts_lbl = tk.Label(root, font=("Segoe UI", 11, "italic"))
attempts_lbl.pack(pady=5)

guess_entry = tk.Entry(root, font=("Segoe UI", 16, "bold"), width=8, justify="center", insertbackground="white", bd=0, highlightthickness=1)
guess_entry.pack(pady=15)
root.bind('<Return>', process_guess)

guess_btn = tk.Button(root, text="Submit Guess (or press Enter)", command=process_guess, font=("Segoe UI", 11, "bold"), bd=0, padx=10, pady=5)
guess_btn.pack(pady=10)

music_btn = tk.Button(root, text="🔊 Mute Music", command=toggle_music, font=("Segoe UI", 10, "bold"), bd=0, padx=10, pady=4, highlightthickness=0)
music_btn.pack(pady=5)

history_toggle_btn = tk.Button(root, text="📊 View History", command=toggle_history_drawer, font=("Segoe UI", 10, "bold"), bd=0, relief="flat", highlightthickness=0)
history_toggle_btn.pack(pady=5)

history_lbl = tk.Label(root, font=("Segoe UI", 10, "italic"), padx=10, pady=8, bd=0, highlightthickness=1, width=40, wraplength=320)

graphic_bottom = tk.Label(root, font=("Courier", 14, "bold"))
graphic_bottom.pack(pady=5)

# Dashboard Frame
stats_frame = tk.LabelFrame(root, text=" Performance Dashboard ", font=("Segoe UI", 10, "bold"), padx=15, pady=15, bd=0, highlightthickness=1)
stats_frame.pack(pady=15, fill="both", expand="yes", padx=30)

lbl_style = {"font": ("Segoe UI", 11), "anchor": "w"}
games_played_lbl = tk.Label(stats_frame, text="Total Games Played: 0", **lbl_style)
games_played_lbl.pack(fill="x", pady=2)

games_won_lbl = tk.Label(stats_frame, text="Games Won: 0", **lbl_style)
games_won_lbl.pack(fill="x", pady=2)

win_rate_lbl = tk.Label(stats_frame, text="Win Rate: 0%", **lbl_style)
win_rate_lbl.pack(fill="x", pady=2)

best_score_lbl = tk.Label(stats_frame, text="Best Round: N/A", **lbl_style)
best_score_lbl.pack(fill="x", pady=2)

worst_score_lbl = tk.Label(stats_frame, text="Worst Round: N/A", **lbl_style)
worst_score_lbl.pack(fill="x", pady=2)

highest_level_lbl = tk.Label(stats_frame, text="Highest Level Achieved: Level 1", **lbl_style)
highest_level_lbl.pack(fill="x", pady=2)

grade_lbl = tk.Label(stats_frame, text="Performance Rating: N/A", font=("Segoe UI", 11, "bold"), anchor="w")
grade_lbl.pack(fill="x", pady=(8, 2))

# Launch Application Threads
threading.Thread(target=background_music_loop, daemon=True).start()
start_new_round()
root.mainloop()