import os
import subprocess
import sys
from pathlib import Path

from launchkit.utils.display_utils import arrow_message, status_message, progress_message, exiting_program
from launchkit.utils.scaffold_utils import cleanup_failed_scaffold


def setup_git(folder: Path):
    """Initialize Git in the project folder."""
    progress_message("Initializing Git and GitHub...")
    add_git_ignore_file(folder)

    if not initialize_git_repo(folder):
        cleanup_failed_scaffold(folder)
        exiting_program()
        sys.exit(1)

    if not create_initial_commit(folder):
        cleanup_failed_scaffold(folder)
        exiting_program()
        sys.exit(1)


def initialize_git_repo(project_path):
    """Initialize the git repository."""

    try:
        arrow_message("Initializing git repository...")
        subprocess.run(["git", "init"], cwd=project_path, check=True)
        status_message("Local Git repository initialized successfully.")
    except subprocess.CalledProcessError as e:
        status_message(f"Failed to initialize git repository: {e}", success=False)
        return False
    return True


def create_initial_commit(project_path, msg="Initial commit"):
    """Create initial commit."""

    try:
        arrow_message("Creating Initial commit..")

        subprocess.run(["git", "add", "."], cwd=project_path, check=True)

        subprocess.run(["git", "commit", "-m", msg], cwd=project_path, check=True)

        status_message("Initial commit created successfully.")
    except subprocess.CalledProcessError as e:
        status_message(f"Failed to create initial commit: {e}", False)
        return False

    return True

def add_git_ignore_file(project_path):

    """Adds a basic gitignore files"""

    gitignore_content = """Sample Git Ignore File"""

    gitignore_path = os.path.join(project_path, ".gitignore")
    with open(gitignore_path, "w") as f:
        f.write(gitignore_content)

    arrow_message(".gitignore file created successfully.")
