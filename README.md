# Ctool: C++ Terminal Trainer

A terminal coding platform for learning beginner C++ with real code execution, XP,
lesson unlocks, weak-topic tracking, and AI-style compiler feedback.

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python cpp_terminal_trainer.py
```

## Requirements

- Python 3.10+
- `g++` for real C++ execution in Code Mode

On macOS, install the compiler with:

```bash
xcode-select --install
```

## Features

- Terminal-style interface with Rich
- Beginner lessons for variables, output, conditions, and loops
- User profile saved in `progress.json`
- XP, streaks, streak bonuses, achievements, and reset command
- Hints after the first wrong answer
- Smart validators for beginner C++ code structure
- Multi-line Code Mode for coding challenges
- Real C++ compile/run support through `g++`
- AI-style compiler feedback for common mistakes
- Weak-topic tracking based on wrong attempts
- Sequential lesson unlocks

Progress is saved in `progress.json` after you start using the trainer.
