import os.path

import questionary
import names
import json

user_identity = ["Yes, Sure", "Keep it Anonymous"]

def welcome_user():
    print("\n\n")

    msg = "Welcome to LaunchKIT!"
    width = len(msg) + 6

    print("\n╔" + "═" * width + "╗")
    print("║" + msg.center(width) + "║")
    print("╚" + "═" * width + "╝\n")

    data = {}

    if os.path.exists("data.json"):
        with open("data.json", "r") as file:
            data = json.load(file)
        return data
    else:

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

        with open("data.json", "w") as file:
            json.dump(data, file)

        data["user_name"] = user_name
        with open("data.json", "w") as file:
            json.dump(data, file)

        print("\nWe Created one text file to keep your project information for you only\n")
        print("\nPlease make sure to don't delete it")

        return data

def add_selected_folder_in_data(data):

        if not os.path.isdir(data["selected_folder"]):
            return False

        with open("data.json", "w") as file:
            json.dump(data, file, indent=4)

        return True