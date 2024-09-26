from CapacitiveSoilSensor import get_sensor_percent_wet
from Pump import start_pump, stop_pump, stop_all_pumps, seconds_for_pump
from log import log_initialize, log_add_entry
from time import sleep, time
from helpers import print_enviro
import os
import os.path
from gpiozero import CPUTemperature
import signal
import sys
import atexit

cpu = CPUTemperature()

Containers = ["A1", "A2", "A3", "B1", "B2", "B3"]
target_threshold = {"A": 0.8, "B": 0.4}
ml_to_add_each_time = 10
time_between_checks_seconds = 5

local_filepath_log = "/home/pi/Irrigation/log/log.csv"
seconds_between_logs = 60 * 10

# initialize

log_pump_ml_added = {container_id: 0 for container_id in Containers}
log_previous_time = -9999


def humidify_slightly(container_id, ml_to_add):
    global log_pump_ml_added

    start_time = time()
    start_pump(container_id)
    seconds_this_pump = seconds_for_pump(container_id, ml_to_add)
    while time() - start_time < seconds_this_pump:
        sleep(0.1)
    stop_pump(container_id)

    log_pump_ml_added[container_id] += ml_to_add


def main():
    print("Script is running. Press Ctrl+C to stop.")

    if not os.path.isfile(local_filepath_log):
        log_initialize(Containers, local_filepath_log)

    global log_previous_time
    try:
        while True:
            try:
                print_enviro(cpu)
                current_time = time()
                if current_time > log_previous_time + seconds_between_logs:
                    log_previous_time = current_time
                    log_add_entry(Containers, cpu, local_filepath_log)
                for container_id in Containers:
                    print("container", container_id)
                    sensor_percent_wet = get_sensor_percent_wet(container_id)
                    target_too_dry = target_threshold[container_id[0]]
                    if sensor_percent_wet < target_too_dry:
                        print("Container", container_id,
                              "(", sensor_percent_wet, ") too dry - humidifying")
                        humidify_slightly(container_id, ml_to_add_each_time)
                    else:
                        print("Container", container_id,
                              "(", sensor_percent_wet, ") OK")

                sleep(time_between_checks_seconds)
            except Exception as e:
                print("Error")
                print(e)
                stop_all_pumps()
    except KeyboardInterrupt:
        print("KeyboardInterrupt caught. Exiting...")
    except SystemExit:
        # Handle
        pass


def cleanup():
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
