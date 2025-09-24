from launchkit.modules.project_management import handle_existing_project, setup_new_project
from launchkit.modules.server_management import cleanup_processes
from launchkit.utils.display_utils import rich_message, status_message
from launchkit.utils.learner_utils import setup_learner_mode, is_learner_mode_on
from launchkit.utils.user_utils import handle_user_data


def main():
    """The main entry point for the LaunchKIT CLI application."""
    try:
        # Display welcome message once
        print("\n\n")
        msg = "Welcome to LaunchKIT!"
        width = len(msg) + 6
        print("\n╔" + "═" * width + "╗")
        print("║" + msg.center(width) + "║")
        print("╚" + "═" * width + "╝\n")

        # Handle learner mode setup
        if not is_learner_mode_on():
            setup_learner_mode(is_first_time=True)
        else:
            setup_learner_mode(is_first_time=False)

        # Main application loop
        while True:
            # welcome_user() now handles the main menu loop
            data, folder = handle_user_data()

            # If user selects a project, data and folder will be returned
            if data and folder:
                if data.get("setup_complete", False):
                    # For existing projects, enter the project-specific menu
                    handle_existing_project(data, folder)
                else:
                    # For new projects, start the setup process
                    setup_new_project(data, folder)

            # After a project session ends (or if the user exits the selection),
            # the loop continues, showing the main menu again.
            # If welcome_user() returns (None, None), it means the user chose to exit the app.
            if not data and not folder:
                break  # Exit the while loop and the application

    except KeyboardInterrupt:
        cleanup_processes()
        rich_message("\nGoodbye! 👋", style="bold green")
    except Exception as e:
        status_message(f"An unexpected error occurred: {e}", False)
        cleanup_processes()


def main_for_cli():
    try:
        if not is_learner_mode_on():
            setup_learner_mode(is_first_time=True)
        else:
            setup_learner_mode(is_first_time=False)

        data, folder = handle_user_data()

        if data.get("setup_complete", False):
            handle_existing_project(data, folder)
        else:
            setup_new_project(data, folder)

    except KeyboardInterrupt:
        cleanup_processes()
        rich_message("\nGoodbye! 👋", False)
    except Exception as e:
        status_message(f"Unexpected error: {e}", False)
        cleanup_processes()