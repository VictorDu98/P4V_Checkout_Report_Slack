import time
from src import model

"""
        Make sure to have every class instance .p4tickets generated, so the script is not blocked by waiting user to login.
        Any class instance has .p4tickets of it own expired will not stop the script, it will be skipped and printed error on terminal for debug purpose.
                Try to delete the .p4tickets and run that class instance separately to generate a new one.
                The current script terminal will use the new .p4tickets for the next time class instance is triggered.
        Pass the time into main function to set trigger time.
"""

def main(*args):
    while True:
        current_time = time.strftime("%H:%M")
        for arg in args:
            if current_time == arg:
                RPT = model.Model("RPT")
                RPT.run()
        time.sleep(60)  # Interval trigger time

main("18:30")