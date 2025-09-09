from launchkit.modules.project_management import handle_existing_project, setup_new_project
from launchkit.modules.server_management import cleanup_processes
from launchkit.utils.display_utils import progress_message, rich_message, status_message
from launchkit.utils.user_utils import handle_user_data

def main():
    try:
        progress_message("Launching LaunchKIT... 🚀")
        data, folder = handle_user_data()

        # Check if project is already configured
        if data.get("setup_complete", False):
            handle_existing_project(data, folder)
        else:
            setup_new_project(data, folder)
    except KeyboardInterrupt:
        cleanup_processes()
        rich_message("\nGoodbye! 👋")
    except Exception as e:
        status_message(f"Unexpected error: {e}", False)
        cleanup_processes()
