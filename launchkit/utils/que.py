from questionary import select, Style

from launchkit.utils.display_utils import rich_message


class Question:
    def __init__(self, question, choices):
        self.question = question
        self.choices = choices

    def ask(self):
        user_choice = select(
            self.question, self.choices, style=Style([
            ('qmark', 'fg:#ff9d00 bold'),
            ('question', 'bold'),
            ('answer', 'fg:#ff9d00 bold'),
            ('pointer', 'fg:#ff9d00 bold'),
            ('highlighted', 'fg:#ff9d00 bold'),
            ('selected', 'fg:#cc5454'),
            ('separator', 'fg:#cc5454'),
            ('instruction', ''),
            ('text', ''),
            ('disabled', 'fg:#858585 italic')
        ])).ask()

        rich_message(user_choice)

        return user_choice