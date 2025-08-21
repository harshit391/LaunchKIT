import os.path

import questionary
import names

user_identity = ["Yes, Sure", "Keep it Anonymous"]

def welcome_user():
    print("\n\n")

    msg = "Welcome to LaunchKIT!"
    width = len(msg) + 6

    print("\n╔" + "═" * width + "╗")
    print("║" + msg.center(width) + "║")
    print("╚" + "═" * width + "╝\n")

    if os.path.exists("../user.txt"):
        user_name_from_file = open("../user.txt", "r")
        return user_name_from_file.read()
    else:
        user_name_from_file = open("../user.txt", "w")

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

        user_name_from_file.write(user_name)

        user_name_from_file.close()

        print("\nWe Created one text file to keep your project information for you only\n")
        print("\nPlease make sure to don't delete it")

        return user_name
