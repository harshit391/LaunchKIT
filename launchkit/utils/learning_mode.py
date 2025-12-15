"""
Learning Mode for LaunchKIT
Educational feature that helps users understand commands by showing explanations
and letting them practice typing commands themselves.
"""
import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich import box

console = Console()


class CommandExplainer:
    """Explains commands and their components in an educational way"""

    # Command explanations database
    COMMAND_EXPLANATIONS = {
        # Git commands
        "git": {
            "description": "Version control system to track changes in your code",
            "subcommands": {
                "init": "Initialize a new Git repository in the current directory",
                "add": "Stage files for commit (prepare them to be saved)",
                "commit": "Save staged changes to repository history",
                "push": "Upload local commits to remote repository",
                "pull": "Download changes from remote repository",
                "clone": "Copy a repository from remote to local",
                "status": "Show the working tree status",
                "log": "Show commit history",
                "branch": "List, create, or delete branches",
                "checkout": "Switch branches or restore files",
            },
            "flags": {
                "-m": "Message: Specify commit message inline",
                "-a": "All: Stage all modified files",
                "-b": "Branch: Create a new branch",
                "-f": "Force: Force the operation",
                "--help": "Show help information",
            }
        },
        # NPM commands
        "npm": {
            "description": "Node Package Manager - manages JavaScript dependencies",
            "subcommands": {
                "init": "Create a new package.json file",
                "install": "Install packages from package.json or specified package",
                "start": "Run the start script defined in package.json",
                "run": "Execute a script defined in package.json",
                "test": "Run tests",
                "build": "Build the project for production",
                "update": "Update packages to their latest versions",
            },
            "flags": {
                "-y": "Yes: Accept all defaults without prompting",
                "--save": "Save package to dependencies in package.json",
                "--save-dev": "Save package to devDependencies",
                "-g": "Global: Install package globally",
                "--production": "Install only production dependencies",
            }
        },
        # Docker commands
        "docker": {
            "description": "Container platform to package and run applications",
            "subcommands": {
                "build": "Build a Docker image from Dockerfile",
                "run": "Create and start a container from an image",
                "ps": "List running containers",
                "stop": "Stop running containers",
                "start": "Start stopped containers",
                "rm": "Remove containers",
                "rmi": "Remove images",
                "pull": "Download an image from registry",
                "push": "Upload an image to registry",
                "exec": "Execute command inside running container",
                "logs": "View container logs",
            },
            "flags": {
                "-d": "Detached: Run container in background",
                "-p": "Port: Map container port to host port",
                "-v": "Volume: Mount a volume",
                "-t": "TTY: Allocate a pseudo-TTY",
                "-i": "Interactive: Keep STDIN open",
                "--name": "Name: Assign a name to container",
            }
        },
        # Kubernetes commands
        "kubectl": {
            "description": "Kubernetes command-line tool to manage clusters",
            "subcommands": {
                "get": "Display resources (pods, services, deployments, etc.)",
                "describe": "Show detailed information about a resource",
                "create": "Create a resource from file or stdin",
                "apply": "Apply configuration to resources",
                "delete": "Delete resources",
                "logs": "Print logs from a container in a pod",
                "exec": "Execute command in a container",
                "scale": "Change number of replicas",
                "port-forward": "Forward local port to pod port",
            },
            "flags": {
                "-n": "Namespace: Specify the namespace",
                "-o": "Output: Specify output format (json, yaml, wide)",
                "-f": "File: Specify configuration file",
                "-l": "Label: Filter by label",
                "--all-namespaces": "List resources across all namespaces",
            }
        },
        # Python commands
        "python": {
            "description": "Python interpreter to run Python programs",
            "subcommands": {
                "-m": "Module: Run library module as a script",
                "-c": "Command: Execute Python code from command line",
                "-V": "Version: Show Python version",
            },
            "flags": {
                "-m venv": "Create a virtual environment",
                "-m pip": "Run pip package manager",
            }
        },
        "pip": {
            "description": "Python package installer",
            "subcommands": {
                "install": "Install packages",
                "uninstall": "Uninstall packages",
                "list": "List installed packages",
                "freeze": "Output installed packages in requirements format",
                "show": "Show information about a package",
            },
            "flags": {
                "-r": "Requirements: Install from requirements file",
                "--upgrade": "Upgrade packages to latest version",
            }
        },
        # Other common commands
        "cd": {
            "description": "Change Directory - navigate to a different folder",
            "subcommands": {},
            "flags": {}
        },
        "mkdir": {
            "description": "Make Directory - create a new folder",
            "subcommands": {},
            "flags": {
                "-p": "Parents: Create parent directories if needed",
            }
        },
        "ls": {
            "description": "List - show files and directories",
            "subcommands": {},
            "flags": {
                "-l": "Long: Show detailed information",
                "-a": "All: Show hidden files",
                "-h": "Human-readable: Show sizes in KB, MB, etc.",
            }
        },
    }

    @staticmethod
    def explain_command(command: List[str]) -> Dict[str, Any]:
        """
        Break down and explain a command.

        Args:
            command: Command as list (e.g., ["git", "commit", "-m", "message"])

        Returns:
            Dict with command explanation
        """
        if not command:
            return {"error": "Empty command"}

        base_cmd = command[0]
        explanation = {
            "base_command": base_cmd,
            "full_command": " ".join(command),
            "description": "",
            "breakdown": [],
        }

        # Get base command info
        cmd_info = CommandExplainer.COMMAND_EXPLANATIONS.get(base_cmd, {})
        explanation["description"] = cmd_info.get("description", f"Execute {base_cmd} command")

        # Explain each part
        for i, part in enumerate(command):
            if i == 0:
                # Base command
                explanation["breakdown"].append({
                    "part": part,
                    "type": "command",
                    "explanation": cmd_info.get("description", "Main command")
                })
            elif part.startswith("-"):
                # Flag
                flag_info = cmd_info.get("flags", {}).get(part, "Command option/flag")
                explanation["breakdown"].append({
                    "part": part,
                    "type": "flag",
                    "explanation": flag_info
                })
            elif i > 0 and command[i-1] in cmd_info.get("subcommands", {}):
                # Argument for subcommand
                explanation["breakdown"].append({
                    "part": part,
                    "type": "argument",
                    "explanation": "Argument value"
                })
            elif part in cmd_info.get("subcommands", {}):
                # Subcommand
                sub_info = cmd_info["subcommands"][part]
                explanation["breakdown"].append({
                    "part": part,
                    "type": "subcommand",
                    "explanation": sub_info
                })
            else:
                # Other argument
                explanation["breakdown"].append({
                    "part": part,
                    "type": "argument",
                    "explanation": "Command argument"
                })

        return explanation

    @staticmethod
    def display_command_explanation(command: List[str], purpose: str = ""):
        """
        Display a beautiful explanation of a command.

        Args:
            command: Command as list
            purpose: High-level purpose of this command
        """
        explanation = CommandExplainer.explain_command(command)

        # Create command display
        command_str = " ".join(command)

        console.print()
        console.print(Panel.fit(
            f"[bold cyan]📚 Learning Mode: Understanding Commands[/bold cyan]",
            border_style="cyan"
        ))

        if purpose:
            console.print(f"\n[bold yellow]🎯 Purpose:[/bold yellow] {purpose}\n")

        # Show command with syntax highlighting
        console.print("[bold green]Command to execute:[/bold green]")
        syntax = Syntax(command_str, "bash", theme="monokai", line_numbers=False)
        console.print(Panel(syntax, border_style="green"))

        # Show description
        console.print(f"\n[bold blue]What this command does:[/bold blue]")
        console.print(f"  {explanation['description']}\n")

        # Show breakdown
        console.print("[bold magenta]Command Breakdown:[/bold magenta]")

        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("Part", style="cyan", width=20)
        table.add_column("Type", style="yellow", width=15)
        table.add_column("Explanation", style="white")

        for part in explanation["breakdown"]:
            type_emoji = {
                "command": "🔧",
                "subcommand": "⚙️",
                "flag": "🚩",
                "argument": "📝"
            }.get(part["type"], "•")

            table.add_row(
                part["part"],
                f"{type_emoji} {part['type'].title()}",
                part["explanation"]
            )

        console.print(table)
        console.print()


class LearningMode:
    """Manages learning mode functionality"""

    LEARNING_MODE_FILE = Path.home() / ".launchkit_learning_mode"

    @staticmethod
    def is_enabled() -> bool:
        """Check if learning mode is enabled"""
        return LearningMode.LEARNING_MODE_FILE.exists()

    @staticmethod
    def enable():
        """Enable learning mode"""
        LearningMode.LEARNING_MODE_FILE.touch()
        console.print("\n[bold green]✅ Learning Mode Enabled![/bold green]")
        console.print("[dim]You'll now see explanations and practice commands before execution.[/dim]\n")

    @staticmethod
    def disable():
        """Disable learning mode"""
        if LearningMode.LEARNING_MODE_FILE.exists():
            LearningMode.LEARNING_MODE_FILE.unlink()
        console.print("\n[bold yellow]Learning Mode Disabled[/bold yellow]")
        console.print("[dim]Commands will execute directly without practice.[/dim]\n")

    @staticmethod
    def toggle():
        """Toggle learning mode on/off"""
        if LearningMode.is_enabled():
            LearningMode.disable()
        else:
            LearningMode.enable()

    @staticmethod
    def get_user_command_input(expected_command: str, max_attempts: int = 3) -> bool:
        """
        Let user practice typing the command.

        Args:
            expected_command: The command user should type
            max_attempts: Maximum number of attempts allowed

        Returns:
            bool: True if user typed correctly or skipped, False if failed
        """
        console.print("[bold cyan]✍️  Now it's your turn![/bold cyan]")
        console.print(f"[dim]Type the command above to practice (or type 'skip' to execute automatically)[/dim]\n")

        for attempt in range(1, max_attempts + 1):
            console.print(f"[yellow]Attempt {attempt}/{max_attempts}:[/yellow]")
            user_input = input("$ ").strip()

            if user_input.lower() == 'skip':
                console.print("[dim]⏩ Skipping practice, executing command...[/dim]\n")
                return True

            if user_input == expected_command:
                console.print("[bold green]✅ Perfect! Command is correct.[/bold green]\n")
                time.sleep(0.5)
                return True
            else:
                console.print("[bold red]❌ Not quite right. Try again![/bold red]")

                # Show differences
                console.print(f"[dim]Expected:[/dim] [green]{expected_command}[/green]")
                console.print(f"[dim]You typed:[/dim] [red]{user_input}[/red]\n")

                if attempt < max_attempts:
                    console.print("[dim]💡 Tip: Copy the command carefully, including all spaces and flags.[/dim]\n")

        console.print("[yellow]⚠️  Maximum attempts reached. Executing command anyway...[/yellow]\n")
        return True

    @staticmethod
    def interactive_command_execution(
        command: List[str],
        purpose: str = "",
        auto_execute: bool = True
    ) -> bool:
        """
        Show command explanation and let user practice before execution.

        Args:
            command: Command as list
            purpose: High-level purpose of the command
            auto_execute: Whether to execute after practice

        Returns:
            bool: True if should proceed with execution
        """
        if not LearningMode.is_enabled():
            return True  # If learning mode disabled, just execute

        # Display explanation
        CommandExplainer.display_command_explanation(command, purpose)

        # Let user practice
        command_str = " ".join(command)
        success = LearningMode.get_user_command_input(command_str)

        if success and auto_execute:
            console.print("[bold blue]🚀 Executing command...[/bold blue]\n")
            time.sleep(0.3)

        return success

    @staticmethod
    def show_learning_mode_info():
        """Display information about learning mode"""
        console.print()
        console.print(Panel.fit(
            "[bold cyan]📚 Learning Mode Information[/bold cyan]\n\n"
            "[green]What is Learning Mode?[/green]\n"
            "An educational feature that helps you understand commands by:\n"
            "  • Showing what each command does\n"
            "  • Breaking down command parts and flags\n"
            "  • Letting you practice typing commands\n"
            "  • Explaining the purpose of each operation\n\n"
            "[yellow]How it works:[/yellow]\n"
            "1. Before executing, you'll see the command breakdown\n"
            "2. Type the command yourself to practice\n"
            "3. Get instant feedback on your input\n"
            "4. Type 'skip' anytime to auto-execute\n\n"
            "[blue]Perfect for:[/blue]\n"
            "  • Learning Docker, Kubernetes, Git\n"
            "  • Understanding build tools\n"
            "  • Practicing command-line skills\n"
            "  • Teaching others about DevOps",
            border_style="cyan",
            padding=(1, 2)
        ))
        console.print()

    @staticmethod
    def ask_enable_learning_mode() -> bool:
        """
        Ask user if they want to enable learning mode.

        Returns:
            bool: True if enabled
        """
        console.print()
        console.print("[bold cyan]🎓 Would you like to enable Learning Mode?[/bold cyan]")
        console.print("[dim]Learning mode helps you understand commands by showing explanations")
        console.print("and letting you practice typing them before execution.[/dim]\n")

        response = input("Enable learning mode? (yes/no) [default: no]: ").strip().lower()

        if response in ['yes', 'y']:
            LearningMode.enable()
            return True
        else:
            console.print("[dim]You can enable it later using the project settings.[/dim]\n")
            return False


def demonstrate_learning_mode():
    """Demo function to show learning mode in action"""
    console.print("[bold]🎓 Learning Mode Demo[/bold]\n")

    # Example 1: Git command
    LearningMode.interactive_command_execution(
        ["git", "init"],
        purpose="Initialize a new Git repository to track your code changes"
    )

    # Example 2: Docker command
    LearningMode.interactive_command_execution(
        ["docker", "build", "-t", "myapp:latest", "."],
        purpose="Build a Docker image from the Dockerfile in current directory"
    )

    # Example 3: Kubernetes command
    LearningMode.interactive_command_execution(
        ["kubectl", "get", "pods", "-n", "default"],
        purpose="List all pods running in the default namespace"
    )


if __name__ == "__main__":
    # Test the learning mode
    LearningMode.enable()
    demonstrate_learning_mode()
