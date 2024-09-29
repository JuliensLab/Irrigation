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


def watering_allowed_ml(container_id, add_ml_requested):
    # Remove entries older than 24 hours
    cutoff_time = datetime.now() - timedelta(days=1)
    log_pump_ml_added[container_id] = [
        entry for entry in log_pump_ml_added[container_id]
        if datetime.fromisoformat(entry["time"]) > cutoff_time
    ]

    # Calculate total ml added in the last 24 hours
    ml_added_last_24h = sum(entry["ml"]
                            for entry in log_pump_ml_added[container_id])

    # Determine how much water can be added
    remaining_ml_allowed = max_ml_per_24h - ml_added_last_24h

    # Return the allowed amount, capped at the remaining amount
    return min(add_ml_requested, remaining_ml_allowed) if remaining_ml_allowed > 0 else 0


def log_and_upload(cpu, log_pump_ml_added, Containers):
    # try:
    # Log data to file
    log_add_entry(Containers, cpu, local_filepath_log, log_pump_ml_added)

    # Attempt to send data to the server
    with upload_lock:
        send_data_to_server(cpu, log_pump_ml_added, Containers)
    # except Exception as e:
    #     print(f"Error logging and uploading data: {e}")


# Create an instance of the PID controller
# parameters set for a check every 60 seconds
pid_controller = PID.PIDController(Kp=5.0, Ki=0.05, Kd=2000.0)


def check_and_water(container_id):
    sensor_percent_wet = get_sensor_percent_wet(container_id)
    target_percent_wet = target_threshold[container_id[0]]  # 'A' or 'B'

    if sensor_percent_wet > target_percent_wet + 0.03:
        print(
            f"Container {container_id} ({sensor_percent_wet * 100:.1f}%) too wet - waiting it out")
    elif sensor_percent_wet > target_percent_wet:
        print(f"Container {container_id} ({sensor_percent_wet * 100:.1f}%) OK")
    else:
        # Use the PID controller to determine the amount of water to add
        ml_to_add_PID = round(pid_controller.compute(
            target_percent_wet, sensor_percent_wet))

        # Calculate the allowed water based on 24-hour limit
        ml_to_add_allowed = watering_allowed_ml(container_id, ml_to_add_PID)

        # Limit to 40 seconds to have enough time until next check
        max_ml_within_loop_cycle = seconds_to_ml(container_id, 40)
        ml_to_add = min(ml_to_add_allowed, max_ml_within_loop_cycle)

        print(container_id, sensor_percent_wet, target_percent_wet,
              max_ml_within_loop_cycle, ml_to_add_PID, ml_to_add_allowed, ml_to_add)

        if ml_to_add > 0:
            global log_pump_ml_added
            # Log ml added with timestamp
            current_time = datetime.now()
            log_pump_ml_added[container_id].append(
                {"time": current_time.isoformat(), "ml": ml_to_add})
            save_log_pump_ml_added()  # Save log of ml added
            print(
                f"Container {container_id} ({sensor_percent_wet * 100:.1f}%) too dry - humidifying with {ml_to_add:.0f} ml (PID)")

            # Create and track pump thread
            pump_thread = threading.Thread(
                target=add_ml_to_container, args=(container_id, ml_to_add))
            pump_threads.append(pump_thread)
            pump_thread.start()
        else:
            print(
                f"Container {container_id} ({sensor_percent_wet * 100:.1f}%) no watering needed at this time (PID)")


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
                threading.Thread(target=log_and_upload, args=(
                    cpu, log_pump_ml_added, Containers)).start()

                for container_id in Containers:
                    check_and_water(container_id)

                sleep_duration = 60 - datetime.now().second
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
