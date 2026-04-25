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
- Beautiful in-app upgrade session with `ctool upgrade`
- Graceful Ctrl+C exit screen with session summary
- Full C++ learning roadmap inspired by W3Schools
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

## Learning Roadmap

Inside the app, type:

```text
roadmap
```

The roadmap covers the W3Schools C++ tutorial structure, including basics,
functions, OOP/classes, errors, STL data structures, namespaces, projects,
reference topics, examples, exercises, quiz, challenges, practice problems,
syllabus, and study plan.

Reference: https://www.w3schools.com/cpp/default.asp

## Update From GitHub

Inside the app, type:

```text
ctool upgrade
```

Ctool will check the current Git repository, fetch `origin`, and fast-forward pull
from `origin/main`. If local files have uncommitted changes, the upgrade pauses so
your work is not overwritten.
