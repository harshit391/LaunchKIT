from launchkit.modules.project_management import handle_existing_project, setup_new_project
from launchkit.modules.server_management import cleanup_processes
from launchkit.nlp.main import nlp_main
from launchkit.utils.display_utils import progress_message, rich_message, status_message
from launchkit.utils.que import Question
from launchkit.utils.user_utils import handle_user_data
from launchkit.utils.learner_utils import setup_learner_mode, is_learner_mode_on


def main():
    try:
        progress_message("Launching LaunchKIT... 🚀")

        print("\n\n")
        msg = "Welcome to LaunchKIT!"
        width = len(msg) + 6
        print("\n╔" + "═" * width + "╗")
        print("║" + msg.center(width) + "║")
        print("╚" + "═" * width + "╝\n")

        user_choice = Question("How do you want to Proceed?", ["Command Line", "Options"]).ask()

        # Handle learner mode setup right after choice - this is global for all LaunchKIT usage
        if not is_learner_mode_on():
            # Check if learner mode file exists - if not, this is first time for learner mode
            setup_learner_mode(is_first_time=True)
        else:
            # Returning user with learner mode - ask if they want to continue or disable
            setup_learner_mode(is_first_time=False)

        if user_choice == "Command Line":
            nlp_main()
        else:
            data, folder = handle_user_data()

            # Check if project is already configured
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


def main_for_cli():
    try:
        # Handle learner mode for CLI users as well
        if not is_learner_mode_on():
            # First time for learner mode - show prompt
            setup_learner_mode(is_first_time=True)
        else:
            # Returning user with learner mode - ask if they want to continue or disable
            setup_learner_mode(is_first_time=False)

        data, folder = handle_user_data()

        # Check if project is already configured
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