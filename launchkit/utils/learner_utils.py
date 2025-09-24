import os
import platform
import tempfile
from pathlib import Path

from launchkit.utils.display_utils import status_message, boxed_message
from launchkit.utils.que import Question


class LearnerModeManager:
    def __init__(self):
        self.learner_file_name = "launchkit_learner_mode.tmp"
        self.learner_file_path = self._get_learner_file_path()

    def _get_learner_file_path(self):
        """Get the appropriate path for the learner mode file based on OS"""
        system = platform.system().lower()

        if system == "windows":
            # Use AppData/Local for Windows
            app_data = os.getenv('LOCALAPPDATA')
            if app_data:
                learner_dir = Path(app_data) / "LaunchKIT"
            else:
                learner_dir = Path(tempfile.gettempdir()) / "LaunchKIT"
        elif system in ["darwin", "linux"]:
            # Use ~/.local/share for Linux/macOS
            home = Path.home()
            learner_dir = home / ".local" / "share" / "LaunchKIT"
        else:
            # Fallback to temp directory
            learner_dir = Path(tempfile.gettempdir()) / "LaunchKIT"

        # Create directory if it doesn't exist
        learner_dir.mkdir(parents=True, exist_ok=True)

        return learner_dir / self.learner_file_name

    def is_learner_mode_enabled(self):
        """Check if learner mode is currently enabled"""
        return self.learner_file_path.exists()

    def enable_learner_mode(self):
        """Enable learner mode by creating the temp file"""
        try:
            with open(self.learner_file_path, 'w') as f:
                f.write("learner_mode_enabled\n")
            status_message("Learner Mode enabled! 📚")
            return True
        except Exception as e:
            status_message(f"Failed to enable learner mode: {e}", False)
            return False

    def disable_learner_mode(self):
        """Disable learner mode by removing the temp file"""
        try:
            if self.learner_file_path.exists():
                self.learner_file_path.unlink()
                status_message("Learner Mode disabled! 🎓")
            return True
        except Exception as e:
            status_message(f"Failed to disable learner mode: {e}", False)
            return False

    def show_first_time_learner_prompt(self):
        """Show the initial learner mode prompt for first-time users"""
        boxed_message("Learner Mode Available!")

        print("If you choose Yes, then each command will be written as a description on console")
        print(
            "and you have to write the command itself after that rather than just choose and the command will execute\n")

        learning_choice = Question("Do you want to Learn/Practice the commands?", ["Yes", "No"]).ask()

        if learning_choice == "Yes":
            if self.enable_learner_mode():
                status_message("Learner Mode is now ON! 🎯")
                print("\nNext time you open LaunchKIT, you'll have the option to continue or disable learner mode.\n")
                return True

        return False

    def show_returning_user_learner_prompt(self):
        """Show learner mode options for returning users who have it enabled"""
        boxed_message("Learner Mode Status")

        print("You currently have Learner Mode enabled.")
        print("In Learner Mode, commands are described and you practice writing them yourself.\n")

        choice = Question(
            "What would you like to do?",
            ["Continue with Learner Mode", "Disable Learner Mode"]
        ).ask()

        if choice == "Continue with Learner Mode":
            status_message("Continuing with Learner Mode! 📚")
            return True
        else:
            if self.disable_learner_mode():
                print(
                    "You can re-enable Learner Mode anytime by deleting your project config and restarting LaunchKIT.\n")
            return False

    def handle_learner_mode_setup(self, is_first_time=True):
        """
        Main method to handle learner mode setup

        Args:
            is_first_time (bool): Whether this is the user's first time using LaunchKIT

        Returns:
            bool: True if learner mode is enabled, False otherwise
        """
        if is_first_time:
            # First time user - show initial prompt
            return self.show_first_time_learner_prompt()
        else:
            # Check if learner mode is already enabled
            if self.is_learner_mode_enabled():
                return self.show_returning_user_learner_prompt()
            else:
                # User had disabled learner mode previously, don't show prompts
                return False

    def get_learner_file_location(self):
        """Get the location of the learner mode file for debugging"""
        return str(self.learner_file_path)


# Convenience functions for easy importing
def is_learner_mode_on():
    """Quick check if learner mode is enabled"""
    manager = LearnerModeManager()
    return manager.is_learner_mode_enabled()


def setup_learner_mode(is_first_time=True):
    """Setup learner mode based on user's status"""
    manager = LearnerModeManager()
    return manager.handle_learner_mode_setup(is_first_time)


def manage_learner_mode_settings():
    """Allow users to manually manage learner mode settings"""
    manager = LearnerModeManager()
    return manager.show_returning_user_learner_prompt()


def disable_learner_mode():
    """Disable learner mode"""
    manager = LearnerModeManager()
    return manager.disable_learner_mode()


def enable_learner_mode():
    """Enable learner mode"""
    manager = LearnerModeManager()
    return manager.enable_learner_mode()


def get_learner_status_info():
    """Get information about learner mode status and file location"""
    manager = LearnerModeManager()
    return {
        'enabled': manager.is_learner_mode_enabled(),
        'file_path': manager.get_learner_file_location()
    }