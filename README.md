# Guess the Number: macOS Edition

An interactive guessing game built with Python and Tkinter. The application challenges players to identify a secret number through deduction while navigating five progressively harder levels.

## How the Game Works

* **The Objective:** At the start of each round, the programme generates a random whole number between 1 and 100. The player must guess this secret number.
* **Level Progression:** The campaign spans five distinct levels. Level 1 grants the player 7 attempts. Each time a level is cleared, the player advances to the next stage and the available attempts decrease by one. By Level 5, the player has only 3 attempts to find the correct number.
* **Directional Feedback:** After every submitted attempt, the interface informs the player whether their guess was too high or too low, while audio cues provide spoken updates.
* **Winning the Campaign:** Successfully guessing the number in Level 5 completes the entire campaign and unlocks the victory screen.
* **Losing a Round:** If a player uses all their attempts before guessing correctly, the round ends and the campaign resets back to Level 1.

## Core Features

* **Anti Cheat Protection:** A memory tracking system records all previous guesses during a round. If a player submits a duplicate number, the game issues a warning without deducting an attempt from their remaining pool.
* **Sliding History Drawer:** A toggle button expands the window container to display the exact chronological sequence of attempts made during the round.
* **Dynamic Visual Themes:** Each level features a distinct colour palette, custom text banner, and typography. Submitting a guess triggers a flash across the screen.
* **Asynchronous Audio:** Ambient background music loops at a low volume while native macOS vocal alerts announce game states. These operate on independent subprocesses to ensure the graphical interface never freezes.
* **Performance Dashboard:** A tracking panel displays total games played, total wins, win percentage, best round, and peak level achieved. It also calculates an academic performance rating ranging from A plus down to F.

## Technical Design Decisions

* **Set Data Structure:** Storing previous attempts inside a Python set allows instantaneous lookup speeds when validating user input against duplicate guesses.
* **Subprocess Execution:** Isolating the audio commands onto background threads ensures the visual rendering loop remains completely responsive during gameplay.

## Installation and Setup

1. Ensure your system is running macOS with Python 3 installed.
2. Download or clone the project files to your local machine.
3. Open your terminal and navigate inside the project folder.
4. Launch the application by running the following command:

```bash
python3 game.py