import questionary
import tkinter as tk
from tkinter import filedialog

from launchkit.utils.display_utils import exiting_program
from launchkit.modules import git_module

root = tk.Tk()
root.withdraw()

from launchkit.utils.user_utils import welcome_user, add_selected_folder_in_data

tech_stacks = ["Node.js", "Flask", "React", "MERN Stack"]
options = ["Initialize Git and GitHub", "Add Docker Support", "Generate Kubernetes Files"]

def main():
    """Main Function to run the Launch KIT"""

    data = welcome_user()

    user_name = data["user_name"]

    print(f"\nSo Once Again ----- WELCOME TO LAUNCHKIT {user_name.upper()} ------\n\n")

    selected_folder = ""

    try:
        selected_folder = data["selected_folder"]
        print(f"\nSelected Folder: {selected_folder}\n")
    except KeyError:
        """User will choose a folder from file explorer"""
        selected_folder = filedialog.askdirectory(title="Please choose a Folder for your project")

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

    """What User Want"""
    action_chosen_by_user = questionary.select(
        "Which Action would you like to do?",
        choices=options,
    ).ask()

    if action_chosen_by_user not in options:
        exiting_program()
        return

    print(f"User chose {action_chosen_by_user}\n")

    if "Initialize Git and GitHub" in action_chosen_by_user:
        print("\nInitializing Git and GitHub\n")

        git_module.add_git_ignore_file(selected_folder)

        if git_module.initialize_git_repo(selected_folder):
            if not git_module.create_initial_commit(selected_folder):
                exiting_program()
                return
        else:
            exiting_program()
            return

    elif "Add Docker Support" in action_chosen_by_user:
        print("\nAdding Docker Support\n")
    elif "Generate Kubernetes Files" in action_chosen_by_user:
        print("\nGenerating Kubernetes Files\n")
    else:
        exiting_program()
        return

    print("\nSetup complete!\n")

if __name__ == "__main__":
    main()
