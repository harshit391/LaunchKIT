def exiting_program():
    print("Exiting Program....")

    msg = "Thanks for Visiting!"
    width = len(msg) + 6

    print("\n╔" + "═" * width + "╗")
    print("║" + msg.center(width) + "║")
    print("╚" + "═" * width + "╝\n")

def boxed_message(msg: str):
    border = "─" * (len(msg) + 4)
    print(f"\n┌{border}┐")
    print(f"│  {msg}  │")
    print(f"└{border}┘\n")

def arrow_message(step: str):
    print(f"\n➡️  {step}\n")

import sys
import time

def progress_message(msg: str):
    sys.stdout.write(f"{msg}")
    sys.stdout.flush()
    for _ in range(3):
        time.sleep(0.5)
        sys.stdout.write(".")
        sys.stdout.flush()
    print(" Done!")

from rich.console import Console
from rich.panel import Panel

console = Console()

def rich_message(msg: str, style="bold green", show: bool = True):
    console.print(Panel(f"{"You chose: " if show else ""}{msg}", style=style, expand=False))

# Example
def status_message(task: str, success=True):
    symbol = "✔" if success else "✖"
    color = "\033[92m" if success else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{symbol} {task}{reset}")