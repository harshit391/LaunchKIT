import getpass
import os
import json
import names
import shutil
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from datetime import datetime

from launchkit.utils.display_utils import boxed_message, rich_message, arrow_message, status_message
from launchkit.utils.que import Question

# Possible user choices for identity
user_identity = ["Yes, Sure", "Keep it Anonymous"]


def create_backup(selected_folder: str):
    """Create a timestamped backup of data.json inside launchkit_backup folder."""
    project_path = Path(selected_folder)
    backup_folder = project_path / "launchkit_backup"
    backup_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = backup_folder / f"data-{timestamp}.json"

    shutil.copy("data.json", backup_file)
    arrow_message(f"Backup created: {backup_file}")
    return backup_file


def restore_backup(selected_folder: str):
    """Allow user to select a backup to restore data.json."""
    project_path = Path(selected_folder)
    backup_folder = project_path / "launchkit_backup"

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
    shutil.copy(backup_file, "data.json")

    boxed_message(f"Restored from backup: {backup_file}")
    return "data.json"


def welcome_user():
    """Handles user onboarding (identity + project folder)."""

    print("\n\n")

    msg = "Welcome to LaunchKIT!"
    width = len(msg) + 6

    print("\n╔" + "═" * width + "╗")
    print("║" + msg.center(width) + "║")
    print("╚" + "═" * width + "╝\n")

    data = {}

    # If config already exists, load it
    if os.path.exists("data.json"):
        with open("data.json", "r") as file:
            data = json.load(file)
        return data

    # ========== Step 1: Ask for folder (first, so we can check for backups) ==========
    arrow_message("Now please select a folder for your project setup")

    # Initialize tkinter root (hidden)
    root = tk.Tk()
    root.withdraw()

    selected_folder = filedialog.askdirectory(title="Please choose a Folder for your project")

    if not selected_folder:
        # fallback: manual input if user cancels
        selected_folder = input("No folder selected. Please enter folder path manually: ").strip()

    if not selected_folder or not os.path.isdir(selected_folder):
        rich_message("Invalid folder! Please restart and select a valid directory.", "yellow")
        exit(1)

    # ====== Check if backup folder exists in this directory ======
    backup_folder = Path(selected_folder) / "launchkit_backup"
    if backup_folder.exists() and any(backup_folder.iterdir()):
        arrow_message("Backup folder detected. It seems data.json was deleted.")
        restore_choice = Question(
            "Do you want to restore from a previous backup?",
            ["Yes, restore", "No, start fresh"]
        ).ask()

        if "Yes" in restore_choice:
            restored = restore_backup(selected_folder)
            if restored:
                with open("data.json", "r") as file:
                    data = json.load(file)
                return data

    # ========== Step 2: Ask for identity ==========
    identity_user = Question("Would you mind sharing your name with us?", user_identity).ask()
    user_name = names.get_first_name()  # default anonymous name

    if "Yes" in identity_user:
        user_name = getpass.getuser()
        rich_message("Your name is " + user_name)
    else:
        rich_message(f"That's totally fine, we name you {user_name}")
        arrow_message("Hope you like it!")

    data["user_name"] = user_name
    data["selected_folder"] = selected_folder
    arrow_message(f"Selected Folder: {selected_folder}")

    # ========== Save Data ==========
    with open("data.json", "w") as file:
        json.dump(data, file, indent=4)

    boxed_message("We created a data.json file to keep your project information safe")
    arrow_message("Please make sure not to delete it")

    # ========== Step 3: Create Timestamped Backup ==========
    create_backup(selected_folder)

    return data

def add_selected_folder_in_data(data):
    """Update data.json with selected folder if valid and create a backup."""
    if not os.path.isdir(data.get("selected_folder", "")):
        return False

    with open("data.json", "w") as file:
        json.dump(data, file, indent=4)

    create_backup(data["selected_folder"])
    return True

def add_data_to_db(data: dict, selected_folder: str):
    """Replace the content of data.json with new data and create a backup."""
    try:
        with open("data.json", "w") as file:
            json.dump(data, file, indent=4)

        arrow_message("data.json updated successfully ✅")

        # Create a backup after updating
        create_backup(selected_folder)

        return True
    except Exception as e:
        status_message(f"Failed to update data.json: {e}", False)
        return False
