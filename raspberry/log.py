import os
from TemperatureHumidity import getTemperatureHumiditySHT40
from Pressure import getTemperaturePressureBMP280
from CapacitiveSoilSensor import get_raw_sensor_value, get_calibrated_value
from helpers import get_datetime_string


def log_initialize(Containers, local_filepath_log):
    header = "date time,cpu temp C,room temp C (SHT40),room temp C (BMP280),room humidity % (SHT40),room press hPa (BMP280)"

    # Add dynamic columns for humidity values and pump times based on Containers
    for i in range(len(Containers)):
        header += f",{Containers[i]}_raw_humidity"
    for i in range(len(Containers)):
        header += f",{Containers[i]}_pct_humidity"
    for i in range(len(Containers)):
        header += f",{Containers[i]}_pump_ml_since_prev_entry"

    with open(local_filepath_log, "a") as log:
        if os.stat(local_filepath_log).st_size == 0:
            log.write(header + "\n")
    print("Log initialized")


def log_add_entry(Containers, cpu, local_filepath_log):
    global log_pump_ml_added
    cpuTempC = round(cpu.temperature, 1)
    roomTempC_SHT40, roomHumiditySHT40 = getTemperatureHumiditySHT40()
    roomTempC_BMP280, roomPressureBMP280 = getTemperaturePressureBMP280()

    # Limit the values to 1 digit after the comma
    roomTempC_SHT40 = f"{roomTempC_SHT40:.1f}"
    roomTempC_BMP280 = f"{roomTempC_BMP280:.1f}"
    roomHumiditySHT40 = f"{roomHumiditySHT40:.1f}"
    roomPressureBMP280 = f"{roomPressureBMP280:.1f}"

    # Construct the log entry
    log_entry = "{0},{1},{2},{3},{4},{5}".format(
        get_datetime_string(),
        cpuTempC,
        roomTempC_SHT40,
        roomTempC_BMP280,
        roomHumiditySHT40,
        roomPressureBMP280
    )

    # Gather dynamic sensor values
    sensor_data = []

    for container_id in Containers:
        raw_value = get_raw_sensor_value(container_id)
        calibrated_value = get_calibrated_value(container_id, raw_value)
        pump_ml_added = f"{log_pump_ml_added[container_id]:.1f}"

        # Append a dictionary with the sensor values to the list
        sensor_data.append({
            # 'container_id': container_id,
            'humidity_raw': str(raw_value),
            'humidity_pct': str(calibrated_value),
            'pump_ml_added': str(pump_ml_added)
        })

    # Add humidity values and pump times separately
    humidity_raw_values = [data['humidity_raw'] for data in sensor_data]
    humidity_pct_values = [data['humidity_pct'] for data in sensor_data]
    pump_ml_added = [data['pump_ml_added'] for data in sensor_data]

    log_entry += "," + ",".join(humidity_raw_values)
    log_entry += "," + ",".join(humidity_pct_values)
    log_entry += "," + ",".join(pump_ml_added) + "\n"

    # Write the log entry to the file
    with open(local_filepath_log, "a") as log:
        log.write(log_entry)

    # Reset pump times
    log_pump_ml_added = {container_id: 0 for container_id in Containers}

    print("Log entry added")
