import getpass
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple

import names

from launchkit.utils.display_utils import boxed_message, rich_message, arrow_message, status_message, exiting_program
from launchkit.utils.que import Question

# Possible user choices for identity
user_identity = ["Yes, Sure", "Keep it Anonymous"]


def get_base_launchkit_folder():
    """Get or create the base launchkit projects folder."""
    base_folder = Path.home() / "launchkit_projects"
    base_folder.mkdir(exist_ok=True)
    return base_folder


def create_backup(project_folder: Path):
    """Create a timestamped backup of data.json inside project's backup folder."""
    backup_folder = project_folder / "launchkit_backup"
    backup_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = backup_folder / f"data-{timestamp}.json"

    data_file = project_folder / "data.json"
    if data_file.exists():
        shutil.copy(data_file, backup_file)
        arrow_message(f"Backup created: {backup_file}")
        return backup_file
    return None


def restore_backup(project_folder: Path):
    """Allow user to select a backup to restore data.json."""
    backup_folder = project_folder / "launchkit_backup"

    if not backup_folder.exists() or not any(backup_folder.iterdir()):
        status_message("No backups found to restore!", False)
        return None

    backups = sorted(backup_folder.glob("data-*.json"))
    backup_choices = [b.name for b in backups]

    # Ask user which backup to restore
    question = Question("Select a backup to restore:", backup_choices)
    selected_backup = question.ask()

    if selected_backup not in backup_choices:
        status_message("Invalid backup selection!", False)
        return None

    backup_file = backup_folder / selected_backup
    data_file = project_folder / "data.json"
    shutil.copy(backup_file, data_file)
    boxed_message(f"Restored from backup: {backup_file}")
    return str(data_file)


def list_existing_projects():
    """List all existing projects in the base launchkit folder."""
    base_folder = get_base_launchkit_folder()
    projects = []

    for item in base_folder.iterdir():
        if item.is_dir() and (item / "data.json").exists():
            projects.append(item.name)

    return projects


def create_new_project():
    """Create a new project with user input."""
    base_folder = get_base_launchkit_folder()

    # Get project name
    while True:
        project_name = input("Enter your new project name: ").strip()
        if not project_name:
            status_message("Project name cannot be empty.", False)
            continue

        # Check if project already exists
        project_folder = base_folder / project_name
        if project_folder.exists():
            overwrite = Question(
                f"Project '{project_name}' already exists. What would you like to do?",
                ["Choose different name", "Continue with existing project"]
            ).ask()

            if "Continue" in overwrite:
                return load_existing_project(project_name)
            else:
                continue
        else:
            break

    # Create project folder
    project_folder = base_folder / project_name
    project_folder.mkdir(parents=True, exist_ok=True)
    boxed_message(f"Created new project folder: {project_folder}")

    # Ask for user identity
    identity_user = Question("Would you mind sharing your name with us?", user_identity).ask()
    user_name = names.get_first_name()  # default anonymous

    if "Yes" in identity_user:
        user_name = getpass.getuser()
        rich_message(f"Your name is {user_name}")
    else:
        rich_message(f"That's totally fine, we name you {user_name}")
        arrow_message("Hope you like it!")

    # Create initial data structure
    # In user_utils.py - update the data structure in create_new_project()
    data = {
        "user_name": user_name,
        "project_name": project_name,
        "selected_folder": str(project_folder),
        "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project_status": "new",  # States: new, configured, ready
        "setup_complete": False,
        # Add these fields when setup is complete
        "project_type": None,
        "project_stack": None,
        "addons": [],
        "git_setup": False,
        "stack_scaffolding": False,
        "addons_scaffolding": False
    }

    # Save data.json in project folder
    data_file = project_folder / "data.json"
    with open(data_file, "w") as f:
        json.dump(data, f, indent=4)

    boxed_message("Project data.json created to keep your project information safe")
    arrow_message("Please make sure not to delete it")

    # Create initial backup
    create_backup(project_folder)

    return data


def load_existing_project(project_name):
    """Load an existing project's data."""
    base_folder = get_base_launchkit_folder()
    project_folder = base_folder / project_name
    data_file = project_folder / "data.json"

    if not data_file.exists():
        status_message(f"data.json not found for project '{project_name}'", False)
        return None

    try:
        with open(data_file, "r") as f:
            data = json.load(f)

        # Update selected_folder to current project folder path
        data["selected_folder"] = str(project_folder)

        boxed_message(f"Loaded existing project: {project_name}")
        arrow_message(f"Welcome back, {data.get('user_name', 'Unknown')}!")

        # Show current project status
        if data.get("setup_complete", False):
            arrow_message("✅ Project setup is complete")
            if data.get("project_type"):
                arrow_message(f"Project Type: {data.get('project_type')}")
            if data.get("project_stack"):
                arrow_message(f"Tech Stack: {data.get('project_stack')}")
            if data.get("addons"):
                arrow_message(f"Add-ons: {', '.join(data.get('addons', []))}")
        else:
            arrow_message("⚠️ Project setup is incomplete")

        return data

    except Exception as e:
        status_message(f"Failed to load project data: {e}", False)
        return None


def welcome_user():
    """Handles user onboarding with project selection (start new or continue)."""
    print("\n\n")
    msg = "Welcome to LaunchKIT!"
    width = len(msg) + 6
    print("\n╔" + "═" * width + "╗")
    print("║" + msg.center(width) + "║")
    print("╚" + "═" * width + "╝\n")

    # Check if there are existing projects
    existing_projects = list_existing_projects()

    if existing_projects:
        # Ask user: start new or continue existing
        project_action = Question(
            "What would you like to do?",
            ["Start New Project", "Continue Existing Project"]
        ).ask()

        if "Continue" in project_action:
            # Show existing projects
            project_choice = Question(
                "Select a project to continue:",
                existing_projects
            ).ask()

            if project_choice in existing_projects:
                return load_existing_project(project_choice)
            else:
                status_message("Invalid project selection.", False)
                exit(1)
        else:
            # Start new project
            return create_new_project()
    else:
        # No existing projects, start new
        rich_message("No existing projects found. Let's create your first project!")
        return create_new_project()


def add_data_to_db(data: dict, selected_folder: str):
    """Update the project's data.json with new data and create a backup."""
    try:
        project_folder = Path(selected_folder)
        data_file = project_folder / "data.json"

        with open(data_file, "w") as f:
            json.dump(data, f, indent=4)

        arrow_message("Project data updated successfully ✅")

        # Create a backup after updating
        create_backup(project_folder)

        return True

    except Exception as e:
        status_message(f"Failed to update project data: {e}", False)
        return False


def add_selected_folder_in_data(data):
    """Update data.json with selected folder if valid and create a backup."""
    selected_folder = data.get("selected_folder", "")
    if not os.path.isdir(selected_folder):
        return False

    return add_data_to_db(data, selected_folder)

def ensure_folder_exists(path: Path):
    """Ensure the project folder exists, create if missing."""
    if not path.exists():
        status_message(f"Folder {path} doesn't exist. Creating it...", False)
        path.mkdir(parents=True, exist_ok=True)


def handle_user_data() -> Tuple[dict, Path]:
    """Fetch user data from welcome_user() and validate it."""
    try:
        data = welcome_user()  # Now returns project data with project-specific folder
        if not data:
            status_message("Failed to load or create project data.", False)
            exiting_program()
            sys.exit(1)

        user_name = data["user_name"]
        project_name = data.get("project_name", "Unknown Project")
        folder = Path(data["selected_folder"])

        boxed_message(f"Welcome to LaunchKIT, {user_name.upper()}!")
        arrow_message(f"Project: {project_name}")
        arrow_message(f"Project Folder: {folder}")

        ensure_folder_exists(folder)

        return data, folder

    except KeyError as e:
        status_message(f"Corrupt project data detected. Missing key: {e.args[0]}", False)
        exiting_program()
        sys.exit(1)
    except Exception as e:
        status_message(f"Unexpected error while loading project data: {e}", False)
        exiting_program()
        sys.exit(1)
