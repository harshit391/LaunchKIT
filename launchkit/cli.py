import os.path
import sys

import questionary
import tkinter as tk
from tkinter import filedialog

from launchkit.utils.display_utils import exiting_program
from launchkit.modules import git_module

root = tk.Tk()
root.withdraw()

from launchkit.utils.user_utils import welcome_user, add_selected_folder_in_data

tech_stacks = ["Node.js (Server)", "Flask", "React (Static UI)", "MERN Stack (FullStack)", "PERN Stack (FullStack)"]
options = ["Add Docker Support", "Add Kubernetes Support"]


def main():
    """Main Function to run the Launch KIT"""

    data = welcome_user()

    try:
        user_name = data["user_name"]

        print(f"\nSo Once Again ----- WELCOME TO LAUNCHKIT {user_name.upper()} ------\n\n")

        selected_folder = ""

        selected_folder = data["selected_folder"]
        print(f"\nSelected Folder: {selected_folder}\n")

        if not os.path.exists(selected_folder):
            print(f"Folder {selected_folder} doesn't exist, creating it.")
            os.makedirs(selected_folder)

    except KeyError as e:
        """User will choose a folder from file explorer"""

        defected_key = e.args[0]

        selected_folder = ""

        if defected_key == "user_name":
            print("\nIt seems your data.json is corrupt, Rebuilding the file again.")
            os.remove("data.json")
            data = welcome_user()
            selected_folder = data["selected_folder"]

        if defected_key == "selected_folder":
            selected_folder = filedialog.askdirectory(title="Please choose a Folder for your project")
        else:
            print("\nUnexpected error:", sys.exc_info()[0])
            exiting_program()
            return

        if selected_folder:
            data["selected_folder"] = selected_folder
            if add_selected_folder_in_data(data):
                print(f"\nSelected Folder: {selected_folder}\n")
            else:
                print(f"\nNo Folder Selected: {selected_folder}\n")
                exiting_program()
                return
        else:
            print("\nNo Folder Selected\n")
            exiting_program()
            return

    """User choice"""
    tech_stack_chosen_by_user = questionary.select(
        "Which Technical Stack would you like to use?",
        choices=tech_stacks,
    ).ask()

    if tech_stack_chosen_by_user not in tech_stacks:
        exiting_program()
        return

    print(f"Technical Stack: {tech_stack_chosen_by_user}\n")

    print("\nInitializing Git and GitHub\n")

    git_module.add_git_ignore_file(selected_folder)

    if git_module.initialize_git_repo(selected_folder):
        if not git_module.create_initial_commit(selected_folder):
            exiting_program()
            return
    else:
        exiting_program()
        return

    """What User Want"""
    action_chosen_by_user = questionary.select(
        "Which Action would you like to do?",
        choices=options,
    ).ask()

    if action_chosen_by_user not in options:
        exiting_program()
        return

    if "Add Docker Support" in action_chosen_by_user:
        print("\nAdding Docker Support\n")
    elif "Add Kubernetes Support" in action_chosen_by_user:
        print("\nGenerating Kubernetes Files\n")
    else:
        exiting_program()
        return

    print("\nSetup complete!\n")


if __name__ == "__main__":
    main()
