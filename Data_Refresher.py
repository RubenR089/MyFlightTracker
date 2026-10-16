import threading
import time

from Base_logic import get_states_all

current_live_flights = []
is_running = True

def flight_refresher(interval_seconds=10):

    global current_live_flights
    print("Flight Refresher läuft")

    while is_running:
        new_data = get_states_all("all")

        if new_data:
            current_live_flights = new_data
