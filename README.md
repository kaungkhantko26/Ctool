# Ctool: C++ Terminal Trainer

A level 3 Python CLI learning game for beginner C++ concepts.

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python cpp_terminal_trainer.py
```

## Features

- Terminal-style interface with Rich
- Beginner lessons for variables, output, conditions, and loops
- XP, streaks, streak bonuses, completion tracking, and reset command
- Hints after the first wrong answer
- Smart validators for beginner C++ code structure
- Multi-line code mode for coding challenges
- Sequential lesson unlocks

Progress is saved in `progress.json` after you start using the trainer.
