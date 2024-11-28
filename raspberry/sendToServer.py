import requests
import json
from TemperatureHumidity import getTemperatureHumiditySHT40
from Pressure import getTemperaturePressureBMP280
from helpers import get_datetime_utc_string


# Global API configuration
# Replace with your actual API URL and key
api = {"url": 'https://irrigationmars.com/api/api_store_short_term_data.php',
       "key": 'hiufew8GQRYHW%W651#!!&79uojjbho89gRWpio'}


def send_data_to_server(values, cpu, log_pump_ml_added, Containers):
    global api
    cpuTempC = round(cpu.temperature, 1)
    roomTempC_SHT40, roomHumiditySHT40 = getTemperatureHumiditySHT40()
    roomTempC_BMP280, roomPressureBMP280 = getTemperaturePressureBMP280()

    # Limit the values to 1 digit after the comma
    roomTempC_SHT40 = round(roomTempC_SHT40, 1)
    roomTempC_BMP280 = round(roomTempC_BMP280, 1)
    roomHumiditySHT40 = round(roomHumiditySHT40, 1)
    roomPressureBMP280 = round(roomPressureBMP280, 1)

    # Get the current datetime in the correct format
    datetime = get_datetime_utc_string()  # This should return a formatted timestamp

    # Gather dynamic sensor values
    sensor_data = []

    for container_id in Containers:
        # Calculate total pump ml added from log_pump_ml_added
        # Sum ml added entries
        pump_ml_added = sum(entry["ml"]
                            for entry in log_pump_ml_added[container_id])
        data = {
            'container_id': container_id,
            'humidity_raw': values[container_id]['raw'],
            'humidity_pct': values[container_id]['pct'],
            'pump_ml_added': pump_ml_added
        }

        # Append a dictionary with the sensor values to the list
        sensor_data.append(data)

    # Create the payload for the API request
    payload = {
        "api_key": api["key"],
        "date_time": datetime,
        "cpu_temp": cpuTempC,
        "room_temp_SHT40": roomTempC_SHT40,
        "room_temp_BMP280": roomTempC_BMP280,
        "room_humidity_SHT40": roomHumiditySHT40,
        "room_pressure_BMP280": roomPressureBMP280,
        "containers": sensor_data
    }

    # Send the data to the server
    print("sending to server")
    headers = {'Content-Type': 'application/json'}
    response = requests.post(api["url"], headers=headers, json=payload)

    if response.status_code == 200:
        print("Data sent successfully:", response.json())
    else:
        print("Failed to send data:", response.status_code, response.json())
