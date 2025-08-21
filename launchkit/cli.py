import questionary
import names

user_identity = ["Yes, Sure", "Keep it Anonymous"]
tech_stacks = ["Node.js", "Flask", "React", "MERN Stack"]
options = ["Initialize Git and GitHub", "Add Docker Support", "Generate Kubernetes Files"]

def main():
    """Main Function to run the Launch KIT"""

    print("\n\n")
    print("Welcome to LaunchKIT!")
    print("---------------------------------------------")

    """Identity"""
    identity_user = questionary.select(
        "Would you mind sharing your name with us",
        choices=user_identity,
    ).ask()

    user_name = names.get_first_name()

    if "Yes" in identity_user:
        user_name = input("What is your first name? ")
        print("Your name is " + user_name)
    else:
        print(f"That's totally fine, we name you {user_name}")
        print("\nHope you like it!")

    print(f"\nSo Once Again ----- WELCOME TO LAUNCHKIT {user_name.upper()} ------")

    """User choice"""
    tech_stack_chosen_by_user = questionary.select(
        "Which Technical Stack would you like to use?",
        choices=tech_stacks,
    ).ask()

    print(f"Technical Stack: {tech_stack_chosen_by_user}")

    """What User Want"""
    action_chosen_by_user = questionary.select(
        "Which Action would you like to do?",
        choices=options,
    ).ask()

    print(f"User chose {action_chosen_by_user}")

    if "Initialize Git and GitHub" in action_chosen_by_user:
        print("\nInitializing Git and GitHub")

    if "Add Docker Support" in action_chosen_by_user:
        print("\nAdding Docker Support")

    if "Generate Kubernetes Files" in action_chosen_by_user:
        print("\nGenerating Kubernetes Files")

    print("\nSetup complete!")

if __name__ == "__main__":
    main()
