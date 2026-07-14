"""
Python Game Development Project: Guess the Number (Themed macOS GUI Version)
Description: A baseline visual guessing game with dynamic level themes, text graphic designs,
             and basic session performance stats tracking.
"""

import random
import os
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
# 3. CORE WINDOW GEOMETRY
# ==============================================================================

def centre_window(window, width, height):
    """
    Calculates display geometry parameters to align the 
    application container directly to the monitor spatial center.
    """
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    x_coordinate = int((screen_width / 2) - (width / 2))
    y_coordinate = int((screen_height / 2) - (height / 2))
    
    window.geometry(f"{width}x{height}+{x_coordinate}+{y_coordinate}")


def apply_theme():
    """
    Redraws color profiles, typography variables, and pattern banners across widgets.
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
    
    stats_frame.config(bg=theme["bg"], fg=theme["title_fg"], highlightbackground=theme["accent"])
    games_played_label.config(bg=theme["bg"], fg=theme["text_fg"])
    games_won_label.config(bg=theme["bg"], fg=theme["text_fg"])
    win_rate_label.config(bg=theme["bg"], fg=theme["text_fg"])
    best_score_label.config(bg=theme["bg"], fg=theme["text_fg"])
    worst_score_label.config(bg=theme["bg"], fg=theme["text_fg"])

# ==============================================================================
# 4. MATHEMATICAL LOGIC & PERFORMANCE SUBSYSTEM
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

# ==============================================================================
# 5. PRIMARY GAMEPLAY STATE MACHINE
# ==============================================================================

def start_new_round():
    """
    Wipes structural local tracking values and initializes mathematical random targets.
    """
    global SECRET_NUMBER, ATTEMPTS_LEFT, ATTEMPTS_TAKEN
    SECRET_NUMBER = random.randint(1, 100)
    
    ATTEMPTS_LEFT = max(8 - CURRENT_LEVEL, 1)
    ATTEMPTS_TAKEN = 0
    
    apply_theme()
    feedback_label.config(text="I have chosen a number between 1 and 100.")
    attempts_label.config(text=f"Attempts Remaining: {ATTEMPTS_LEFT}")
    guess_entry.delete(0, tk.END)
    guess_entry.focus()


def process_guess(event=None):
    """
    Core input validation and comparison loop. Tracks wins, losses,
    and updates stats upon completion of a round.
    """
    global TOTAL_GAMES_PLAYED, TOTAL_WINS, BEST_SCORE, WORST_SCORE, ATTEMPTS_LEFT, ATTEMPTS_TAKEN, CURRENT_LEVEL
    
    user_input = guess_entry.get().strip()
    guess_entry.delete(0, tk.END)
    
    # Simple Numerical Type Verification
    if not user_input.isdigit():
        messagebox.showerror("Invalid Input", "❌ Please enter a valid whole number.")
        return
        
    guess = int(user_input)
    
    # Standard Range Constraint Verification
    if not (1 <= guess <= 100):
        messagebox.showerror("Out of Bounds", "❌ Please guess a number between 1 and 100.")
        return
        
    ATTEMPTS_LEFT -= 1
    ATTEMPTS_TAKEN += 1
    attempts_label.config(text=f"Attempts Remaining: {ATTEMPTS_LEFT}")
    
    if guess == SECRET_NUMBER:
        TOTAL_GAMES_PLAYED += 1
        TOTAL_WINS += 1
        
        if ATTEMPTS_TAKEN < BEST_SCORE:
            BEST_SCORE = ATTEMPTS_TAKEN
            
        if ATTEMPTS_TAKEN > WORST_SCORE:
            WORST_SCORE = ATTEMPTS_TAKEN
            
        update_stats_display()
        messagebox.showinfo("Winner!", f"🎉 Correct! You won Level {CURRENT_LEVEL} in {ATTEMPTS_TAKEN} attempts.")
        
        # Keep cycling through themes if we exceed dictionary limit
        CURRENT_LEVEL += 1
        start_new_round()
        return
        
    elif guess < SECRET_NUMBER:
        feedback_label.config(text=f"📉 {guess} is too low! Try a higher number.")
    else:
        feedback_label.config(text=f"📈 {guess} is too high! Try a lower number.")
        
    if ATTEMPTS_LEFT == 0:
        TOTAL_GAMES_PLAYED += 1
        update_stats_display()
        messagebox.showinfo("Game Over", f"💥 Out of attempts! The correct number was {SECRET_NUMBER}.\nResetting back to Level 1.")
        
        CURRENT_LEVEL = 1
        start_new_round()

# ==============================================================================
# 6. UNIFIED GRAPHICAL INTERFACE SETUP (ENTRY POINT)
# ==============================================================================

root = tk.Tk()
root.title("Guess the Number")

centre_window(root, 420, 600)

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

start_new_round()
root.mainloop()