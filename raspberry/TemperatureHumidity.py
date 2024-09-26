# Temperature and Humidity sensor
# SHT40 sensor on ENV IV Board from M5 Stack (https://docs.m5stack.com/en/unit/ENV%E2%85%A3%20Unit)
# I2C Channel 0x44
# Adafruit CircuitPython library

import time
import board
import adafruit_sht4x

i2c = board.I2C()   # uses board.SCL and board.SDA
sht = adafruit_sht4x.SHT4x(i2c)
print("Found SHT4x with serial number", hex(sht.serial_number))

sht.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION
# Can also set the mode to enable heater
# sht.mode = adafruit_sht4x.Mode.LOWHEAT_100MS
print("Current mode is: ", adafruit_sht4x.Mode.string[sht.mode])


def getTemperatureHumiditySHT40():
    temperature, relative_humidity = sht.measurements
    return temperature, relative_humidity

def test():
    while True:
        temperature, relative_humidity = sht.measurements
        print("Temperature: %0.1f°C" % temperature, "Humidity: %0.1f %%" % relative_humidity)
        time.sleep(1)

if __name__ == "__main__":
    test()