# Pressure sensor
# BMP280 sensor on ENV IV Board from M5 Stack (https://docs.m5stack.com/en/unit/ENV%E2%85%A3%20Unit)
# I2C Channel 0x76
# Adafruit CircuitPython library

import time
import board
# import digitalio # For use with SPI
import adafruit_bmp280

i2c_channel = 0x76

# Create sensor object, communicating over the board's default I2C bus
i2c = board.I2C()   # uses board.SCL and board.SDA
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, i2c_channel)

# OR Create sensor object, communicating over the board's default SPI bus
# spi = board.SPI()
# bmp_cs = digitalio.DigitalInOut(board.D10)
# bmp280 = adafruit_bmp280.Adafruit_BMP280_SPI(spi, bmp_cs)

# change this to match the location's pressure (hPa) at sea level
bmp280.sea_level_pressure = 1013.25

def getTemperaturePressureBMP280():
    temperature = bmp280.temperature
    pressure = bmp280.pressure
    return temperature, pressure

def test():
    while True:
        print("\nTemperature: %0.1f C" % bmp280.temperature)
        print("Pressure: %0.1f hPa" % bmp280.pressure)
        print("Altitude = %0.2f meters" % bmp280.altitude)
        time.sleep(2)        

if __name__ == "__main__":
    test()
