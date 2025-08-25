import tkinter as tk
from tkinter import simpledialog, messagebox
import time
import winsound  # Only on Windows, for sound alert


def start_timer(minutes):
    seconds = int(minutes * 60)
    time.sleep(seconds)  # Wait for given minutes

    # Play a beep sound when time is up
    winsound.Beep(10000, 2000)  # (frequency, duration in ms)

    # Show popup with option to continue
    again = messagebox.askyesno("Completed", "Time is up! Do you want to enter another time?")
    if again:
        get_time()  # Restart cycle
    else:
        root.quit()
        exit(1)


def get_time():
    # Ask for time in minutes
    minutes = simpledialog.askfloat("Timer", "Enter time in minutes:")
    if minutes is None:  # Cancel clicked
        root.quit()
        exit(1)
    else:
        root.withdraw()  # Hide main window
        start_timer(minutes)


# Main Tkinter root window (hidden at start)
root = tk.Tk()
root.withdraw()

# Start the first cycle
get_time()

root.mainloop()
