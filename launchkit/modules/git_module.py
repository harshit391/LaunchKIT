import os
import subprocess

def initialize_git_repo(project_path):
    """Initialize the git repository."""

    try:
        print("Initializing git repository...")
        subprocess.run(["git", "init"], cwd=project_path, check=True)
        print("Local Git repository initialized successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to initialize git repository: {e}")
        return False
    return True


def create_initial_commit(project_path, msg="Initial commit"):
    """Create initial commit."""

    try:
        print("Creating Initial commit..")

        subprocess.run(["git", "add", "."], cwd=project_path, check=True)

        subprocess.run(["git", "commit", "-m", msg], cwd=project_path, check=True)

        print("Initial commit created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create initial commit: {e}")
        return False

    return True

def add_git_ignore_file(project_path):

    """Adds a basic gitignore files"""

    gitignore_content = """Sample Git Ignore File"""

    gitignore_path = os.path.join(project_path, ".gitignore")
    with open(gitignore_path, "w") as f:
        f.write(gitignore_content)

    print(".gitignore file created successfully.")
