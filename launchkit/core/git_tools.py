import os
import subprocess
import sys
from pathlib import Path

from launchkit.utils.display_utils import arrow_message, status_message, progress_message, exiting_program
from launchkit.utils.scaffold_utils import cleanup_failed_scaffold
from launchkit.utils.security_utils import SecurityValidator, CommandBuilder
from launchkit.utils.learning_mode import LearningMode


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

        # Prepare command
        git_init_cmd = CommandBuilder.build_git_command("init")

        # Show learning mode explanation if enabled
        if LearningMode.is_enabled():
            LearningMode.interactive_command_execution(
                git_init_cmd,
                purpose="Initialize a new Git repository to start tracking your project's code changes"
            )

        # SECURITY: Use command array instead of shell=True
        subprocess.run(
            git_init_cmd,
            cwd=project_path,
            check=True,
            shell=False
        )
        status_message("Local Git repository initialized successfully.")
    except subprocess.CalledProcessError as e:
        status_message(f"Failed to initialize git repository: {e}", success=False)
        return False
    except Exception as e:
        status_message(f"Unexpected error initializing git: {e}", success=False)
        return False
    return True


def create_initial_commit(project_path, msg="Initial commit"):
    """Create initial commit."""

    try:
        # Validate commit message
        if not msg or not isinstance(msg, str):
            msg = "Initial commit"

        # Remove potentially dangerous characters from commit message
        msg = SecurityValidator.sanitize_command_arg(msg)

        arrow_message("Creating Initial commit..")

        # Prepare commands
        git_add_cmd = CommandBuilder.build_git_command("add", ".")
        git_commit_cmd = CommandBuilder.build_git_command("commit", "-m", msg)

        # Show learning mode explanations if enabled
        if LearningMode.is_enabled():
            LearningMode.interactive_command_execution(
                git_add_cmd,
                purpose="Stage all files in the current directory to prepare them for commit"
            )

        # SECURITY: Use command arrays instead of shell=True
        subprocess.run(
            git_add_cmd,
            cwd=project_path,
            check=True,
            shell=False
        )

        if LearningMode.is_enabled():
            LearningMode.interactive_command_execution(
                git_commit_cmd,
                purpose=f"Save staged changes to repository history with message: '{msg}'"
            )

        subprocess.run(
            git_commit_cmd,
            cwd=project_path,
            check=True,
            shell=False
        )

        status_message("Initial commit created successfully.")
    except subprocess.CalledProcessError as e:
        status_message(f"Failed to create initial commit: {e}", False)
        return False
    except Exception as e:
        status_message(f"Unexpected error creating commit: {e}", False)
        return False

    return True

def add_git_ignore_file(project_path):

    """Adds a basic gitignore file with common patterns."""

    gitignore_content = """# Dependencies
node_modules/
venv/
env/
.venv/
__pycache__/
*.py[cod]
*$py.class

# Environment variables
.env
.env.local
.env.*.local

# Build outputs
build/
dist/
.next/
out/
*.egg-info/

# IDE and editor files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Testing
coverage/
.coverage
htmlcov/
.pytest_cache/
.nyc_output/

# LaunchKIT
data.json
launchkit_backup/
PROJECT_SUMMARY.md
"""

    gitignore_path = os.path.join(project_path, ".gitignore")
    with open(gitignore_path, "w") as f:
        f.write(gitignore_content)

    arrow_message(".gitignore file created successfully.")
