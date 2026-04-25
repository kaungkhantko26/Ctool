from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table


SAVE_FILE = Path("progress.json")

console = Console()


@dataclass(frozen=True)
class Challenge:
    prompt: str
    answer: str | None = None
    contains: tuple[str, ...] = ()
    hint: str = ""
    success: str = "Correct."
    failure: str = "Not quite."
    xp: int = 10

    def check(self, user_answer: str) -> bool:
        normalized = normalize(user_answer)
        if self.answer is not None:
            return normalized == normalize(self.answer)
        return all(token.lower() in normalized for token in self.contains)


@dataclass(frozen=True)
class Lesson:
    key: str
    title: str
    level: str
    concept: str
    example: str
    challenges: tuple[Challenge, ...]


LESSONS: tuple[Lesson, ...] = (
    Lesson(
        key="variables",
        title="Variables",
        level="Beginner",
        concept=(
            "Variables are named boxes for data. In C++, every variable needs a "
            "type before the name."
        ),
        example="int age = 18;\ndouble price = 4.99;\nstring name = \"Mia\";",
        challenges=(
            Challenge(
                prompt="What C++ type stores whole numbers?",
                answer="int",
                hint="It is short for integer.",
                success="Nice. `int` stores whole numbers like 18 or -3.",
            ),
            Challenge(
                prompt="Write a C++ variable named score with the value 100.",
                contains=("int", "score", "=", "100"),
                hint="Use: type name = value;",
                success="Good declaration. You used a type, name, assignment, and value.",
                xp=15,
            ),
        ),
    ),
    Lesson(
        key="output",
        title="Output",
        level="Beginner",
        concept=(
            "C++ prints text with `cout`. The stream operator `<<` sends text "
            "into the output stream."
        ),
        example='#include <iostream>\nusing namespace std;\n\ncout << "Hello";',
        challenges=(
            Challenge(
                prompt="What object is commonly used to print output in C++?",
                answer="cout",
                hint="It starts with c and means console output.",
                success="Right. `cout` is the usual console output object.",
            ),
            Challenge(
                prompt='Write code that prints "Hi".',
                contains=("cout", "<<", '"hi"'),
                hint='Use cout, the << operator, and "Hi" in quotes.',
                success="Clean. That is the core C++ print pattern.",
                xp=15,
            ),
        ),
    ),
    Lesson(
        key="conditions",
        title="If Statements",
        level="Beginner",
        concept=(
            "`if` statements let a program choose what to do. The condition goes "
            "inside parentheses."
        ),
        example='if (age >= 18) {\n    cout << "Adult";\n}',
        challenges=(
            Challenge(
                prompt="What keyword starts a condition in C++?",
                answer="if",
                hint="It is the same word as English: if this, then that.",
                success="Correct. `if` starts conditional logic.",
            ),
            Challenge(
                prompt="Write an if statement that checks if score is greater than 50.",
                contains=("if", "score", ">", "50"),
                hint="Use: if (score > 50) { ... }",
                success="Good. You expressed the condition correctly.",
                xp=20,
            ),
        ),
    ),
    Lesson(
        key="loops",
        title="Loops",
        level="Intermediate",
        concept=(
            "Loops repeat work. A `for` loop is great when you know how many "
            "times to repeat."
        ),
        example="for (int i = 0; i < 5; i++) {\n    cout << i;\n}",
        challenges=(
            Challenge(
                prompt="Which loop is commonly used when you know the repeat count?",
                answer="for",
                hint="It has setup, condition, and update parts.",
                success="Correct. `for` is perfect for counted repetition.",
            ),
            Challenge(
                prompt="Write the start of a loop that creates int i = 0.",
                contains=("for", "int", "i", "=", "0"),
                hint="Start with: for (int i = 0; ...",
                success="Good start. That initializes the loop counter.",
                xp=20,
            ),
        ),
    ),
)


def normalize(text: str) -> str:
    return " ".join(text.strip().lower().replace(";", "").split())


def type_line(text: str, delay: float = 0.01) -> None:
    for char in text:
        console.print(char, end="")
        time.sleep(delay)
    console.print()


def load_progress() -> dict:
    if not SAVE_FILE.exists():
        return {"xp": 0, "streak": 0, "completed": []}

    try:
        data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"xp": 0, "streak": 0, "completed": []}

    return {
        "xp": int(data.get("xp", 0)),
        "streak": int(data.get("streak", 0)),
        "completed": list(data.get("completed", [])),
    }


def save_progress(progress: dict) -> None:
    SAVE_FILE.write_text(json.dumps(progress, indent=2), encoding="utf-8")


def show_header(progress: dict) -> None:
    console.clear()
    console.print(
        Panel.fit(
            "[bold green]C++ Terminal Trainer: Level 2[/bold green]\n"
            "[dim]Interactive lessons, XP, streaks, hints, and code checks[/dim]",
            border_style="green",
        )
    )
    console.print(
        f"[bold]XP:[/bold] {progress['xp']}    "
        f"[bold]Streak:[/bold] {progress['streak']}    "
        f"[bold]Completed:[/bold] {len(progress['completed'])}/{len(LESSONS)}"
    )


def lesson_menu(progress: dict) -> str:
    table = Table(title="Lessons", box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Title", style="bold")
    table.add_column("Level")
    table.add_column("Status")

    completed = set(progress["completed"])
    for index, lesson in enumerate(LESSONS, start=1):
        status = "done" if lesson.key in completed else "open"
        table.add_row(str(index), lesson.title, lesson.level, status)

    console.print(table)
    console.print("[dim]Type a lesson number, `stats`, `reset`, or `exit`.[/dim]")
    return Prompt.ask("trainer").strip().lower()


def run_lesson(lesson: Lesson, progress: dict) -> None:
    show_header(progress)
    console.print(
        Panel(
            f"[bold cyan]{lesson.title}[/bold cyan]\n\n{lesson.concept}",
            title=lesson.level,
            border_style="cyan",
        )
    )
    console.print("[bold yellow]Example[/bold yellow]")
    console.print(lesson.example, style="yellow")
    console.print()

    correct_count = 0
    for challenge in lesson.challenges:
        if ask_challenge(challenge, progress):
            correct_count += 1
        save_progress(progress)

    if correct_count == len(lesson.challenges):
        completed = set(progress["completed"])
        if lesson.key not in completed:
            progress["completed"].append(lesson.key)
            progress["xp"] += 25
            console.print("\n[bold green]Lesson cleared. Bonus +25 XP.[/bold green]")
    else:
        console.print("\n[yellow]Lesson finished. Revisit it for a perfect clear.[/yellow]")

    save_progress(progress)
    Prompt.ask("\nPress Enter to continue", default="")


def ask_challenge(challenge: Challenge, progress: dict) -> bool:
    console.print(Panel(challenge.prompt, border_style="magenta"))
    attempts = 0

    while attempts < 2:
        answer = Prompt.ask("answer")
        attempts += 1

        if challenge.check(answer):
            progress["xp"] += challenge.xp
            progress["streak"] += 1
            console.print(f"[green]{challenge.success} +{challenge.xp} XP[/green]")
            return True

        progress["streak"] = 0
        if attempts == 1 and challenge.hint:
            console.print(f"[yellow]Hint: {challenge.hint}[/yellow]")
        else:
            reveal = challenge.answer or ", ".join(challenge.contains)
            console.print(f"[red]{challenge.failure} Expected: {reveal}[/red]")

    return False


def show_stats(progress: dict) -> None:
    show_header(progress)
    completed = set(progress["completed"])
    locked = [lesson.title for lesson in LESSONS if lesson.key not in completed]

    console.print(Panel("[bold]Stats[/bold]", border_style="blue"))
    console.print(f"Total XP: [bold green]{progress['xp']}[/bold green]")
    console.print(f"Current streak: [bold cyan]{progress['streak']}[/bold cyan]")
    console.print(f"Lessons cleared: [bold]{len(completed)}/{len(LESSONS)}[/bold]")
    if locked:
        console.print("Still to clear: " + ", ".join(locked))
    else:
        console.print("[green]All lessons cleared.[/green]")
    Prompt.ask("\nPress Enter to continue", default="")


def reset_progress() -> dict:
    if not Confirm.ask("Reset all XP, streaks, and lesson progress?"):
        return load_progress()

    progress = {"xp": 0, "streak": 0, "completed": []}
    save_progress(progress)
    console.print("[yellow]Progress reset.[/yellow]")
    time.sleep(0.8)
    return progress


def boot_sequence() -> None:
    console.clear()
    lines = [
        "booting trainer kernel...",
        "loading beginner-safe C++ concepts...",
        "installing confidence module...",
        "ready.",
    ]
    for line in lines:
        type_line(f"> {line}", delay=0.008)
    time.sleep(0.4)


def main() -> None:
    boot_sequence()
    progress = load_progress()

    while True:
        show_header(progress)
        choice = lesson_menu(progress)

        if choice == "exit":
            console.print("[bold red]Session closed.[/bold red]")
            break
        if choice == "stats":
            show_stats(progress)
            continue
        if choice == "reset":
            progress = reset_progress()
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(LESSONS):
            lesson = LESSONS[int(choice) - 1]
            run_lesson(lesson, progress)
            continue

        console.print("[red]Unknown command.[/red]")
        time.sleep(0.8)


if __name__ == "__main__":
    main()
