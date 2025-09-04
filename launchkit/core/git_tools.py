import os
import subprocess

from launchkit.utils.display_utils import arrow_message, status_message


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
