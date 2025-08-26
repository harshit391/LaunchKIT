import questionary

from launchkit.utils.display_utils import rich_message


class Question:
    def __init__(self, question, choices):
        self.question = question
        self.choices = choices

    def ask(self):
        user_choice = questionary.select(
            self.question, self.choices).ask()

        rich_message(user_choice)

        return user_choice