from CapacitiveSoilSensor import get_sensor_value, SensorCalibration, interpretSensor 
from Pump import start_pump, stop_pump, stop_all_pumps, seconds_for_pump
from TemperatureHumidity import getTemperatureHumiditySHT40
from Pressure import getTemperaturePressureBMP280
from time import sleep, time, strftime
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

local_filepath_log = "/home/pi/Irrigation/log.csv"
seconds_between_logs = 60 * 10

# initialize

log_pump_ml_added = {container_id: 0 for container_id in Containers}
log_previous_time = -601

# Pumps / Sensors are accessed with numbers 1, 2 and 3


def interpretSensor(container_id):
    val = get_sensor_value(container_id)
    dry = SensorCalibration['dry'][container_id]
    wet = SensorCalibration['wet'][container_id]
    return round(min(1, max(0, (val-dry)/(wet-dry))), 2)


def get_datetime_string():
    return strftime("%Y-%m-%d %H:%M:%S")


def humidify_slightly(container_id, ml_to_add):
    global log_pump_ml_added

    start_time = time()
    start_pump(container_id)
    seconds_this_pump = seconds_for_pump(container_id, ml_to_add)
    while time() - start_time < seconds_this_pump:
        sleep(0.1)
    elapsed_time = time() - start_time
    stop_pump(container_id)

    log_pump_ml_added[container_id] += ml_to_add


def log_initialize():
    header = "date time,cpu temp C,room temp C (SHT40),room temp C (BMP280),room humidity % (SHT40),room press hPa (BMP280)"

    # Add dynamic columns for humidity values and pump times based on Containers
    for i in range(len(Containers)):
        header += f",{Containers[i]}_humidity"
    for i in range(len(Containers)):
        header += f",{Containers[i]}_pump_ml_since_prev_log"

    with open(local_filepath_log, "a") as log:
        if os.stat(local_filepath_log).st_size == 0:
            log.write(header + "\n")
    print("Log initialized")


def log_add_entry():
    global log_pump_ml_added
    cpuTempC = round(cpu.temperature, 1)
    roomTempC_SHT40, roomHumiditySHT40 = getTemperatureHumiditySHT40()
    roomTempC_BMP280, roomPressureBMP280 = getTemperaturePressureBMP280()

    # Limit the values to 1 digit after the comma
    roomTempC_SHT40 = f"{roomTempC_SHT40:.1f}"
    roomTempC_BMP280 = f"{roomTempC_BMP280:.1f}"
    roomHumiditySHT40 = f"{roomHumiditySHT40:.1f}"
    roomPressureBMP280 = f"{roomPressureBMP280:.1f}"

    # Gather dynamic sensor values
    humidity_values = [str(get_sensor_value(container_id))
                       for container_id in Containers]
    pump_ml_added = [str(f"{log_pump_ml_added[container_id]:.1f}")
                  for container_id in Containers]

    # Construct the log entry
    log_entry = "{0},{1},{2},{3},{4},{5}".format(
        get_datetime_string(),
        cpuTempC,
        roomTempC_SHT40,
        roomTempC_BMP280,
        roomHumiditySHT40,
        roomPressureBMP280
    )

    # Add humidity values and pump times separately
    log_entry += "," + ",".join(humidity_values)
    log_entry += "," + ",".join(pump_ml_added) + "\n"

    # Write the log entry to the file
    with open(local_filepath_log, "a") as log:
        log.write(log_entry)

    # Reset pump times
    log_pump_ml_added = {container_id: 0 for container_id in Containers}

    print("Log entry added")


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


def print_enviro():
    cpuTempC = round(cpu.temperature, 1)
    roomTempC_SHT40, roomHumiditySHT40 = getTemperatureHumiditySHT40()
    roomTempC_BMP280, roomPressureBMP280 = getTemperaturePressureBMP280()

    # Create a formatted print statement
    print_data = (
        f"{get_datetime_string()}, "
        f"CPU: {cpuTempC:.1f}°C, "
        f"SHT40: {roomTempC_SHT40:.1f}°C, "
        f"BMP280: {roomTempC_BMP280:.1f}°C, "
        f"Humidity: {roomHumiditySHT40:.1f}%, "
        f"Pressure: {roomPressureBMP280:.2f}hPa"
    )

    print(print_data)


def main():
    print("Script is running. Press Ctrl+C to stop.")

    if not os.path.isfile(local_filepath_log):
        log_initialize()

    global log_previous_time
    try:
        while True:
            try:
                print_enviro()
                current_time = time()
                if current_time > log_previous_time + seconds_between_logs:
                    log_previous_time = current_time
                    log_add_entry()
                for container_id in Containers:
                    print("container", container_id)
                    sensor_humid_pct = interpretSensor(container_id)
                    target_too_dry = target_threshold[container_id[0]]
                    if sensor_humid_pct < target_too_dry:
                        print("Container", container_id,
                              "(", sensor_humid_pct, ") too dry - humidifying")
                        humidify_slightly(container_id, ml_to_add_each_time)
                    # elif sensor_humid_pct > wet_threshold:
                    #    print("Container", container_id,
                    #          "(", sensor_humid_pct, ") too wet")
                    else:
                        print("Container", container_id,
                              "(", sensor_humid_pct, ") OK")

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


if __name__ == "__main__":
    main()
