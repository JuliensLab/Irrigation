from datetime import timedelta
import PID
import json
from CapacitiveSoilSensor import get_sensor_percent_wet
from Pump import start_pump, stop_pump, stop_all_pumps, seconds_for_pump, seconds_to_ml
from log import log_initialize, log_add_entry
from time import sleep, time
from datetime import datetime, timedelta
from helpers import print_enviro
from sendToServer import send_data_to_server
import os
import os.path
from gpiozero import CPUTemperature
import signal
import sys
import atexit
import threading

cpu = CPUTemperature()

Containers = ["A1", "A2", "A3", "B1", "B2", "B3"]
target_threshold = {"A": 0.8, "B": 0.4}

# Max ml allowed per container within 24 hours
max_ml_per_24h = 1000

local_filepath_log = "/home/pi/Irrigation/raspberry/log/log.csv"
# Path for saving ml added
pump_ml_log_file_path = "/home/pi/Irrigation/raspberry/log/pump_ml_log.json"
# To avoid race conditions on uploading
upload_lock = threading.Lock()
# Modified log to track water added with timestamps
log_pump_ml_added = {container_id: [] for container_id in Containers}

# Track pump threads for graceful stop
pump_threads = []
pump_thread_stop_event = threading.Event()


def load_log_pump_ml_added():
    global log_pump_ml_added
    if os.path.isfile(pump_ml_log_file_path):
        try:
            with open(pump_ml_log_file_path, 'r') as f:
                log_pump_ml_added = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading pump ml log file: {e}")
            # Use an empty log if the file couldn't be loaded
            log_pump_ml_added = {container_id: []
                                 for container_id in Containers}


def save_log_pump_ml_added():
    try:
        with open(pump_ml_log_file_path, 'w') as f:
            json.dump(log_pump_ml_added, f)
    except IOError as e:
        print(f"Error saving pump ml log file: {e}")


def add_ml_to_container(container_id, ml_to_add):
    start_time = time()
    seconds_this_pump = seconds_for_pump(container_id, ml_to_add)
    start_pump(container_id)
    print('thread for' + container_id + '+' + str(ml_to_add) +
          'ml (' + str(seconds_this_pump) + 'sec')

    try:
        # Wait for the pump to finish or until stop event is set
        while time() - start_time < seconds_this_pump:
            if pump_thread_stop_event.is_set():
                break
            sleep(0.2)
    finally:
        # Stop the pump in case of interruption or completion
        stop_pump(container_id)


# Update watering thresholds
max_ml_per_12h = 500
max_ml_per_6h = 300
max_ml_per_3h = 200


def watering_allowed_ml_time_based(container_id, add_ml_requested):
    # Remove entries older than 12, 6, and 3 hours
    cutoff_time_12h = datetime.now() - timedelta(hours=12)
    cutoff_time_6h = datetime.now() - timedelta(hours=6)
    cutoff_time_3h = datetime.now() - timedelta(hours=3)

    # Calculate total ml added in each time period
    ml_added_last_12h = sum(entry["ml"]
                            for entry in log_pump_ml_added[container_id]
                            if datetime.fromisoformat(entry["time"]) > cutoff_time_12h)

    ml_added_last_6h = sum(entry["ml"]
                           for entry in log_pump_ml_added[container_id]
                           if datetime.fromisoformat(entry["time"]) > cutoff_time_6h)

    ml_added_last_3h = sum(entry["ml"]
                           for entry in log_pump_ml_added[container_id]
                           if datetime.fromisoformat(entry["time"]) > cutoff_time_3h)

    # Determine the allowed amount based on the smallest restriction window
    remaining_ml_12h = max_ml_per_12h - ml_added_last_12h
    remaining_ml_6h = max_ml_per_6h - ml_added_last_6h
    remaining_ml_3h = max_ml_per_3h - ml_added_last_3h

    remaining_ml_allowed = min(
        remaining_ml_12h, remaining_ml_6h, remaining_ml_3h)

    # Return the allowed amount, capped at the remaining amount
    return min(add_ml_requested, remaining_ml_allowed) if remaining_ml_allowed > 0 else 0


def check_and_water(container_id):
    sensor_percent_wet = get_sensor_percent_wet(container_id)
    target_percent_wet = target_threshold[container_id[0]]  # 'A' or 'B'

    if sensor_percent_wet >= target_percent_wet:
        print(f"Container {container_id} ({sensor_percent_wet * 100:.1f}%) OK")
    else:
        # Calculate the amount of water to add based on humidity difference
        ml_to_add = round((target_percent_wet - sensor_percent_wet) * 10)

        # Calculate the allowed water based on time-based limits
        ml_to_add_allowed = watering_allowed_ml_time_based(
            container_id, ml_to_add)

        print(container_id, sensor_percent_wet,
              target_percent_wet, ml_to_add, ml_to_add_allowed)

        if ml_to_add_allowed > 0:
            global log_pump_ml_added
            # Log ml added with timestamp
            current_time = datetime.now()
            log_pump_ml_added[container_id].append(
                {"time": current_time.isoformat(), "ml": ml_to_add_allowed})
            save_log_pump_ml_added()  # Save log of ml added
            print(
                f"Container {container_id} ({sensor_percent_wet * 100:.1f}%) too dry - humidifying with {ml_to_add_allowed:.0f} ml (Time-based)")

            # Create and track pump thread
            pump_thread = threading.Thread(
                target=add_ml_to_container, args=(container_id, ml_to_add_allowed))
            pump_threads.append(pump_thread)
            pump_thread.start()
        else:
            print(
                f"Container {container_id} ({sensor_percent_wet * 100:.1f}%) no watering needed at this time (Time-based)")


def main():
    print("Script is running. Press Ctrl+C to stop.")

    if not os.path.isfile(local_filepath_log):
        log_initialize(Containers, local_filepath_log)

    load_log_pump_ml_added()  # Load ml added data from file

    try:
        while True:
            current_time = datetime.now()
            current_seconds = current_time.second

            # Check if we're at the top of the minute (00 second)
            if current_seconds == 0:
                print_enviro(cpu)

                # Start logging and uploading data in a separate thread
                threading.Thread(target=log_add_entry, args=(
                    Containers, cpu, local_filepath_log, log_pump_ml_added)).start()

                for container_id in Containers:
                    check_and_water(container_id)

                # Send the data to the server
                threading.Thread(target=send_data_to_server, args=(
                    cpu, log_pump_ml_added, Containers)).start()

                sleep_duration = 60 - datetime.now().second - 2
                sleep(sleep_duration)
            else:
                sleep(0.2)

    except KeyboardInterrupt:
        print("KeyboardInterrupt caught. Exiting...")
    except SystemExit:
        pass


def cleanup():
    print("Performing cleanup...")
    save_log_pump_ml_added()  # Save ml added data before exiting

    # Stop all pump threads gracefully
    pump_thread_stop_event.set()
    for thread in pump_threads:
        thread.join()

    stop_all_pumps()
    print("Cleanup complete.")


# Register the cleanup function with atexit
atexit.register(cleanup)


def signal_handler(sig, frame):
    print(f"Signal received: {sig}")
    cleanup()
    sys.exit(0)


# Register the signal handler for termination signals
signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Handle kill command

if __name__ == "__main__":
    main()
