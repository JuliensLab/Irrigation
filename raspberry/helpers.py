from TemperatureHumidity import getTemperatureHumiditySHT40
from Pressure import getTemperaturePressureBMP280
from datetime import datetime, timezone
from time import strftime


def print_enviro(cpu):
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


def get_datetime_string():
    return strftime("%Y-%m-%d %H:%M:%S")


def get_datetime_utc_string():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
