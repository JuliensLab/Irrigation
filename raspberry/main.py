import json
from CapacitiveSoilSensor import get_sensor_percent_wet
from Pump import start_pump, stop_pump, stop_all_pumps, seconds_for_pump
from log import log_initialize, log_add_entry
from time import sleep, time
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
ml_to_add_each_time = 10
max_ml_per_container = 100  # Maximum ml allowed to add per container over time

local_filepath_log = "/home/pi/Irrigation/raspberry/log/log.csv"
# Path for saving cooldowns
cooldown_file_path = "/home/pi/Irrigation/raspberry/log/cooldown.json"
# Path for saving ml added
pump_ml_log_file_path = "/home/pi/Irrigation/raspberry/log/pump_ml_log.json"
seconds_between_logs = 60 * 2

# Initialize
log_previous_time = -9999
upload_lock = threading.Lock()  # To avoid race conditions on uploading
# Track watering cooldown
watering_cooldown = {container_id: 0 for container_id in Containers}
log_pump_ml_added = {
    container_id: 0 for container_id in Containers}  # Track ml added


def load_cooldown():
    global watering_cooldown
    if os.path.isfile(cooldown_file_path):
        with open(cooldown_file_path, 'r') as f:
            watering_cooldown = json.load(f)


def save_cooldown():
    with open(cooldown_file_path, 'w') as f:
        json.dump(watering_cooldown, f)


def load_log_pump_ml_added():
    global log_pump_ml_added
    if os.path.isfile(pump_ml_log_file_path):
        with open(pump_ml_log_file_path, 'r') as f:
            log_pump_ml_added = json.load(f)


def save_log_pump_ml_added():
    with open(pump_ml_log_file_path, 'w') as f:
        json.dump(log_pump_ml_added, f)


def humidify_slightly(container_id, ml_to_add):
    global log_pump_ml_added
    start_time = time()

    # Start the pump
    start_pump(container_id)
    seconds_this_pump = seconds_for_pump(container_id, ml_to_add)

    # Wait for the pump to finish
    while time() - start_time < seconds_this_pump:
        sleep(0.1)

    # Stop the pump
    stop_pump(container_id)
    log_pump_ml_added[container_id] += ml_to_add
    # Set cooldown for 1 hour after watering
    watering_cooldown[container_id] = time() + 3600
    save_cooldown()  # Save cooldown after watering
    save_log_pump_ml_added()  # Save log of ml added after watering


def can_water(container_id):
    # Check if the container is in the cooldown period and return False if it is
    if time() < watering_cooldown[container_id]:
        return False
    return log_pump_ml_added[container_id] < max_ml_per_container


def log_and_upload(cpu, log_pump_ml_added, Containers):
    global log_previous_time
    current_time = time()

    # Log the data if enough time has passed
    if current_time > log_previous_time + seconds_between_logs:
        log_previous_time = current_time
        log_add_entry(Containers, cpu, local_filepath_log, log_pump_ml_added)

    # Attempt to send data to the server
    with upload_lock:
        send_data_to_server(cpu, log_pump_ml_added, Containers)


def check_and_water(container_id):
    sensor_percent_wet = get_sensor_percent_wet(container_id)
    target_percent_wet = target_threshold[container_id[0]]

    if can_water(container_id) and sensor_percent_wet < target_percent_wet:
        print(
            f"Container {container_id} ({sensor_percent_wet}) too dry - humidifying")
        threading.Thread(target=humidify_slightly, args=(
            container_id, ml_to_add_each_time)).start()
    elif sensor_percent_wet > target_percent_wet + 0.03:
        print(
            f"Container {container_id} ({sensor_percent_wet}) too wet - oops! waiting it out")
    else:
        print(f"Container {container_id} ({sensor_percent_wet}) OK")


def main():
    print("Script is running. Press Ctrl+C to stop.")

    if not os.path.isfile(local_filepath_log):
        log_initialize(Containers, local_filepath_log)

    load_cooldown()  # Load cooldown data from file
    load_log_pump_ml_added()  # Load ml added data from file

    try:
        while True:
            # Get current time
            current_time = time()
            current_seconds = int(current_time % 60)

            # Check if we're at the top of a 10-second interval (00, 10, 20, ...)
            if current_seconds % 10 == 0:
                print_enviro(cpu)

                # Start logging and uploading data in a separate thread
                threading.Thread(target=log_and_upload, args=(
                    cpu, log_pump_ml_added, Containers)).start()

                for container_id in Containers:
                    if container_id == "A1":
                        continue

                    check_and_water(container_id)

                # Sleep for 9 seconds to align with the next 10-second mark
                # Sleep for 9 seconds to avoid checking multiple times within the same minute
                sleep(9)
            else:
                # Sleep for the remaining time to the next 10-second interval
                sleep(1)  # Check every second if we are not at the top of the minute
    except KeyboardInterrupt:
        print("KeyboardInterrupt caught. Exiting...")
    except SystemExit:
        pass


def cleanup():
    save_cooldown()  # Save cooldown data before exiting
    save_log_pump_ml_added()  # Save ml added data before exiting
    stop_all_pumps()


# Register the cleanup function with atexit
atexit.register(cleanup)


def signal_handler(sig, frame):
    print("Signal received:", sig)
    cleanup()
    sys.exit(0)  # Exit the program


# Register the signal handler for termination signals
signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Handle kill command

if __name__ == "__main__":
    main()
