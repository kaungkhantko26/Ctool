from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table


SAVE_FILE = Path("progress.json")
GF_MODE = False
UPGRADE_COMMAND = "ctool upgrade"

console = Console()


@dataclass(frozen=True)
class Challenge:
    prompt: str
    topic: str
    answer: str | None = None
    contains: tuple[str, ...] = ()
    validator: Callable[[str], bool] | None = None
    code_mode: bool = False
    run_code: bool = False
    hint: str = ""
    success: str = "Correct."
    failure: str = "Not quite."
    xp: int = 10

    def check(self, user_answer: str) -> bool:
        normalized = normalize(user_answer)
        if self.validator:
            return self.validator(user_answer)
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


def validate_variable_declaration(code: str) -> bool:
    normalized = normalize_code(code)
    return (
        "int " in normalized
        and "=" in normalized
        and ";" in normalized
        and any(name in normalized for name in ("score", "age", "x"))
    )


def validate_output_statement(code: str) -> bool:
    normalized = normalize_code(code)
    return (
        "cout" in normalized
        and "<<" in normalized
        and ";" in normalized
        and ('"hi"' in normalized or "'hi'" in normalized)
    )


def validate_if_statement(code: str) -> bool:
    normalized = normalize_code(code)
    return (
        "if" in normalized
        and "score" in normalized
        and ">" in normalized
        and "50" in normalized
        and "(" in normalized
        and ")" in normalized
        and "{" in normalized
        and "}" in normalized
    )


def validate_loop(code: str) -> bool:
    normalized = normalize_code(code)
    return "for" in normalized and normalized.count(";") >= 2 and "i++" in normalized


def wrap_cpp_snippet(code: str) -> str:
    stripped = code.strip()
    if "int main" in stripped:
        return stripped
    return (
        "#include <iostream>\n"
        "using namespace std;\n\n"
        "int main() {\n"
        f"{stripped}\n"
        "    return 0;\n"
        "}\n"
    )


def run_cpp_code(code: str) -> tuple[bool, str]:
    if shutil.which("g++") is None:
        return False, "g++ was not found. Install Xcode Command Line Tools or GCC."

    with tempfile.TemporaryDirectory(prefix="ctool_cpp_") as tmp_dir:
        cpp_file = Path(tmp_dir) / "main.cpp"
        exe_file = Path(tmp_dir) / "main"
        cpp_file.write_text(wrap_cpp_snippet(code), encoding="utf-8")

        compile_result = subprocess.run(
            ["g++", str(cpp_file), "-o", str(exe_file)],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if compile_result.returncode != 0:
            return False, compile_result.stderr.strip()

        run_result = subprocess.run(
            [str(exe_file)],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if run_result.returncode != 0:
            return False, (run_result.stderr or run_result.stdout).strip()
        return True, run_result.stdout.strip() or "(no output)"


def analyze_error(error: str) -> str:
    normalized = error.lower()
    if "g++ was not found" in normalized:
        return "Install a C++ compiler first. On macOS, run: xcode-select --install"
    if "cout" in normalized and "not declared" in normalized:
        return "Add `using namespace std;` or write `std::cout`."
    if "expected ';'" in normalized or "expected ';' after" in normalized:
        return "Missing semicolon near the line the compiler reported."
    if "undefined reference to" in normalized and "main" in normalized:
        return "C++ programs need `int main() { ... }`."
    if "was not declared" in normalized:
        return "A variable or function is being used before it is declared."
    if "expected" in normalized and ("}" in normalized or "{" in normalized):
        return "Check your braces. Every `{` needs a matching `}`."
    return "Syntax issue. Check spelling, brackets, semicolons, and structure."


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
                topic="variables",
                answer="int",
                hint="It is short for integer.",
                success="Nice. `int` stores whole numbers like 18 or -3.",
            ),
            Challenge(
                prompt="Write a FULL valid variable declaration with a semicolon.",
                topic="variables",
                validator=validate_variable_declaration,
                code_mode=True,
                hint="Example: int score = 100;",
                success="Real code detected. Good declaration.",
                xp=25,
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
                topic="output",
                answer="cout",
                hint="It starts with c and means console output.",
                success="Right. `cout` is the usual console output object.",
            ),
            Challenge(
                prompt='Write a full C++ output statement that prints "Hi".',
                topic="output",
                validator=validate_output_statement,
                code_mode=True,
                run_code=True,
                hint='Example: cout << "Hi";',
                success="Clean. That is a real output statement.",
                xp=25,
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
                topic="conditions",
                answer="if",
                hint="It is the same word as English: if this, then that.",
                success="Correct. `if` starts conditional logic.",
            ),
            Challenge(
                prompt="Write a full if block that checks if score is greater than 50.",
                topic="conditions",
                validator=validate_if_statement,
                code_mode=True,
                hint='Example: if (score > 50) { cout << "Pass"; }',
                success="Good. You wrote a complete if block structure.",
                xp=30,
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
                topic="loops",
                answer="for",
                hint="It has setup, condition, and update parts.",
                success="Correct. `for` is perfect for counted repetition.",
            ),
            Challenge(
                prompt="Write a full for loop that counts with i++.",
                topic="loops",
                validator=validate_loop,
                code_mode=True,
                run_code=True,
                hint="Example: for (int i = 0; i < 5; i++) { cout << i; }",
                success="Loop structure detected. That is real counted repetition.",
                xp=30,
            ),
        ),
    ),
)


def normalize(text: str) -> str:
    return " ".join(text.strip().lower().replace(";", "").split())


def normalize_code(code: str) -> str:
    return " ".join(code.strip().lower().split())


def beep() -> None:
    console.print("\a", end="")


def gf_feedback() -> None:
    if GF_MODE:
        console.print("[magenta]You are doing great. Keep going.[/magenta]")


def type_line(text: str, delay: float = 0.01) -> None:
    for char in text:
        console.print(char, end="")
        time.sleep(delay)
    console.print()


def load_progress() -> dict:
    if not SAVE_FILE.exists():
        name = Prompt.ask("Enter your name", default="Coder")
        return new_progress(name)

    try:
        data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return new_progress("Coder")

    return {
        "name": str(data.get("name", "Coder")),
        "xp": int(data.get("xp", 0)),
        "streak": int(data.get("streak", 0)),
        "completed": list(data.get("completed", [])),
        "weak_topics": dict(data.get("weak_topics", {})),
        "attempts": int(data.get("attempts", 0)),
    }


def new_progress(name: str) -> dict:
    return {
        "name": name,
        "xp": 0,
        "streak": 0,
        "completed": [],
        "weak_topics": {},
        "attempts": 0,
    }


def save_progress(progress: dict) -> None:
    SAVE_FILE.write_text(json.dumps(progress, indent=2), encoding="utf-8")


def show_header(progress: dict) -> None:
    console.clear()
    console.print(
        Panel.fit(
            "[bold green]Ctool: Terminal Coding Platform[/bold green]\n"
            "[dim]C++ execution, AI-style hints, XP, weak-topic tracking[/dim]",
            border_style="green",
        )
    )
    console.print(
        f"[bold]User:[/bold] {progress['name']}    "
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
        unlocked = index == 1 or LESSONS[index - 2].key in completed
        status = "locked" if not unlocked else ("done" if lesson.key in completed else "open")
        table.add_row(str(index), lesson.title, lesson.level, status)

    console.print(table)
    console.print(
        "[dim]Type a lesson number, `stats`, `reset`, `ctool upgrade`, or `exit`.[/dim]"
    )
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
        answer = read_answer(challenge)
        attempts += 1
        progress["attempts"] += 1

        compiled = True
        execution_output = ""
        if challenge.run_code:
            compiled, execution_output = run_cpp_code(answer)
            if compiled:
                console.print("[green]Output:[/green]")
                console.print(execution_output)

        if compiled and challenge.check(answer):
            award_success(challenge, progress)
            return True

        track_weak_topic(challenge, progress)
        progress["streak"] = 0
        if challenge.run_code and not compiled:
            console.print("[red]Compiler feedback:[/red]")
            console.print(execution_output or "No compiler output.")
            console.print(analyze_error(execution_output), style="yellow")
        if attempts == 1 and challenge.hint:
            console.print(f"[yellow]Hint: {challenge.hint}[/yellow]")
        else:
            reveal = challenge.answer or ", ".join(challenge.contains)
            expected = reveal if reveal else "valid code structure"
            console.print(f"[red]{challenge.failure} Expected: {expected}[/red]")

    return False


def award_success(challenge: Challenge, progress: dict) -> None:
    progress["xp"] += challenge.xp
    progress["streak"] += 1
    beep()
    console.print(f"[green]{challenge.success} +{challenge.xp} XP[/green]")
    if progress["streak"] >= 3:
        bonus = 5
        progress["xp"] += bonus
        console.print(f"[cyan]Streak bonus +{bonus} XP[/cyan]")
    gf_feedback()


def track_weak_topic(challenge: Challenge, progress: dict) -> None:
    weak_topics = progress.setdefault("weak_topics", {})
    weak_topics[challenge.topic] = int(weak_topics.get(challenge.topic, 0)) + 1


def read_answer(challenge: Challenge) -> str:
    if not challenge.code_mode:
        return Prompt.ask("answer")

    console.print("[bold cyan]Code Mode[/bold cyan]")
    console.print("[dim]Write C++ code. Type `END` on a new line to finish.[/dim]")
    lines: list[str] = []
    while True:
        line = Prompt.ask(">")
        if line.strip().upper() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def get_achievements(progress: dict) -> list[str]:
    achievements: list[str] = []
    if progress["xp"] >= 100:
        achievements.append("Beginner Master")
    if progress["streak"] >= 5:
        achievements.append("On Fire")
    if len(progress["completed"]) == len(LESSONS):
        achievements.append("All Lessons Cleared")
    if sum(progress.get("weak_topics", {}).values()) > 5:
        achievements.append("Learning Fighter")
    return achievements


def show_stats(progress: dict) -> None:
    show_header(progress)
    completed = set(progress["completed"])
    locked = [lesson.title for lesson in LESSONS if lesson.key not in completed]
    weak_topics = progress.get("weak_topics", {})
    achievements = get_achievements(progress)

    console.print(Panel("[bold]Stats[/bold]", border_style="blue"))
    console.print(f"User: [bold]{progress['name']}[/bold]")
    console.print(f"Total XP: [bold green]{progress['xp']}[/bold green]")
    console.print(f"Current streak: [bold cyan]{progress['streak']}[/bold cyan]")
    console.print(f"Attempts: [bold]{progress['attempts']}[/bold]")
    console.print(f"Lessons cleared: [bold]{len(completed)}/{len(LESSONS)}[/bold]")
    if locked:
        console.print("Still to clear: " + ", ".join(locked))
    else:
        console.print("[green]All lessons cleared.[/green]")

    console.print("\n[bold]Weak Topics[/bold]")
    if weak_topics:
        for topic, count in sorted(weak_topics.items(), key=lambda item: item[1], reverse=True):
            console.print(f"- {topic}: {count} mistake(s)")
    else:
        console.print("[green]No weak topics tracked yet.[/green]")

    console.print("\n[bold]Achievements[/bold]")
    if achievements:
        for achievement in achievements:
            console.print(f"- {achievement}")
    else:
        console.print("[dim]No achievements unlocked yet.[/dim]")
    Prompt.ask("\nPress Enter to continue", default="")


def reset_progress(current_progress: dict) -> dict:
    if not Confirm.ask("Reset all XP, streaks, and lesson progress?"):
        return current_progress

    progress = new_progress(progress_name(current_progress))
    save_progress(progress)
    console.print("[yellow]Progress reset.[/yellow]")
    time.sleep(0.8)
    return progress


def run_shell_command(command: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def git_output(command: list[str], timeout: int = 30) -> tuple[bool, str]:
    try:
        result = run_shell_command(command, timeout=timeout)
    except FileNotFoundError:
        return False, "Git was not found on this system."
    except subprocess.TimeoutExpired:
        return False, f"Command timed out: {' '.join(command)}"

    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    return result.returncode == 0, output or "No output."


def is_git_checkout() -> bool:
    ok, _ = git_output(["git", "rev-parse", "--is-inside-work-tree"], timeout=5)
    return ok


def has_local_changes() -> bool:
    ok, output = git_output(["git", "status", "--porcelain"], timeout=5)
    return ok and bool(output.strip() and output != "No output.")


def run_upgrade() -> None:
    console.clear()
    console.print(
        Panel.fit(
            "[bold green]Ctool Upgrade Session[/bold green]\n"
            "[dim]Syncing the trainer from the GitHub repository[/dim]",
            border_style="green",
        )
    )

    if not is_git_checkout():
        console.print("[red]Upgrade needs to run inside the Ctool Git repository.[/red]")
        Prompt.ask("\nPress Enter to continue", default="")
        return

    if has_local_changes():
        console.print(
            Panel(
                "Local files have uncommitted changes. Commit or stash them before upgrading "
                "so the pull does not overwrite your work.",
                title="Upgrade paused",
                border_style="yellow",
            )
        )
        Prompt.ask("\nPress Enter to continue", default="")
        return

    steps: list[tuple[str, list[str]]] = [
        ("Checking current branch", ["git", "branch", "--show-current"]),
        ("Checking remote", ["git", "remote", "get-url", "origin"]),
        ("Fetching latest code", ["git", "fetch", "origin"]),
        ("Pulling updates", ["git", "pull", "--ff-only", "origin", "main"]),
    ]
    results: list[tuple[str, bool, str]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        for label, command in steps:
            task = progress.add_task(label, total=None)
            ok, output = git_output(command, timeout=60)
            progress.remove_task(task)
            results.append((label, ok, output))
            if not ok:
                break

    table = Table(title="Upgrade Report", box=box.SIMPLE_HEAVY)
    table.add_column("Step", style="bold")
    table.add_column("Status")
    table.add_column("Details", overflow="fold")

    for label, ok, output in results:
        status = "[green]done[/green]" if ok else "[red]failed[/red]"
        table.add_row(label, status, output)

    console.print(table)
    if all(ok for _, ok, _ in results):
        console.print("[bold green]Upgrade complete. Restart Ctool to load new code.[/bold green]")
    else:
        console.print("[bold red]Upgrade stopped. Check the failed step above.[/bold red]")

    Prompt.ask("\nPress Enter to continue", default="")


def boot_sequence() -> None:
    console.clear()
    lines = [
        "booting Ctool platform...",
        "loading C++ lesson engine...",
        "checking compiler bridge...",
        "starting tutor system...",
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
            progress = reset_progress(progress)
            continue
        if choice == UPGRADE_COMMAND:
            run_upgrade()
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(LESSONS):
            lesson_index = int(choice) - 1
            if lesson_index > 0 and LESSONS[lesson_index - 1].key not in progress["completed"]:
                console.print("[red]Complete previous lesson first.[/red]")
                time.sleep(1)
                continue
            lesson = LESSONS[lesson_index]
            run_lesson(lesson, progress)
            continue

        console.print("[red]Unknown command.[/red]")
        time.sleep(0.8)


def progress_name(progress: dict) -> str:
    return str(progress.get("name", "Coder"))


if __name__ == "__main__":
    main()
