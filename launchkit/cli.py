import questionary
import tkinter as tk
from tkinter import filedialog

from launchkit.utils.display_utils import exiting_program

root = tk.Tk()
root.withdraw()

from launchkit.utils.user_utils import welcome_user

tech_stacks = ["Node.js", "Flask", "React", "MERN Stack"]
options = ["Initialize Git and GitHub", "Add Docker Support", "Generate Kubernetes Files"]

def main():
    """Main Function to run the Launch KIT"""

    user_name = welcome_user()

    print(f"\nSo Once Again ----- WELCOME TO LAUNCHKIT {user_name.upper()} ------\n\n")

    """User will choose a folder from file explorer"""
    selected_folder = filedialog.askdirectory(title="Please choose a Folder for your project")

    if selected_folder:
        print(f"\nSelected Folder: {selected_folder}\n")
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
