from ADCPi import ADCPi
from time import sleep

adc = ADCPi(0x68, 0x69, 18)

Sensors = {
    "A1": 1,
    "A2": 2,
    "A3": 3,
    "B1": 4,
    "B2": 5,
    "B3": 6
}


SensorCalibration = {"dry": {"A1": 0.911, "A2": 0.747,
                             "A3": 0.774, "B1": 0.836,
                             "B2": 0.645, "B3": 0.799},
                     "wet": {"A1": 0.612, "A2": 0.513,
                             "A3": 0.494, "B1": 0.613,
                             "B2": 0.472, "B3": 0.593}}


print("Sensors initialized")


def get_one_raw_sensor_value(sensor_id):
    return round(adc.read_voltage(Sensors[sensor_id]), 4)


def get_raw_sensor_value(sensor_id):
    total = 0
    num_samples = 10
    successful_attempts = 0

    # Take readings
    for _ in range(num_samples):
        try:
            total += get_one_raw_sensor_value(sensor_id)
            successful_attempts += 1
            sleep(0.2)
        except ADCPi.TimeoutError:  # Correctly reference TimeoutError
            print(
                f"TimeoutError: Could not read sensor {sensor_id}. Retrying...")

    # Avoid division by zero
    if successful_attempts > 0:
        average_value = round(total / successful_attempts, 4)
        print(
            f"Sensor {sensor_id} - Successful attempts: {successful_attempts}, Average value: {average_value}")
        return average_value
    else:
        print(f"Sensor {sensor_id} - No successful attempts. Returning None.")
        return None


def get_sensor_percent_wet(container_id):
    val = get_raw_sensor_value(container_id)
    return get_calibrated_value(container_id, val)


def get_calibrated_value(container_id, sensor_value):
    dry = SensorCalibration['dry'][container_id]
    wet = SensorCalibration['wet'][container_id]
    return round(min(1, max(0, (sensor_value-dry)/(wet-dry))), 2)


def test():
    print(", ".join(Sensors))
    while True:
        sensor_data = []
        for channel_name, pin in Sensors.items():
            sensor_value = get_raw_sensor_value(channel_name)
            sensor_data.append(str(sensor_value))

        for channel_name, pin in Sensors.items():
            sensor_value = get_raw_sensor_value(channel_name)
            sensor_data.append(
                str(get_calibrated_value(channel_name, sensor_value)))

        print(", ".join(sensor_data))

        sleep(1)


if __name__ == "__main__":
    test()
