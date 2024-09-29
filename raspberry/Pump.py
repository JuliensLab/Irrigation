#!/usr/bin/python
# -*- coding:utf-8 -*-
import RPi.GPIO as GPIO
from time import sleep
import time
import signal
import sys
import atexit

Pumps = {
    "A1": 22,
    "A2": 23,
    "A3": 24,
    "B1": 26,
    "B2": 20,
    "B3": 21
}

PumpsCalibration = {"100ml_seconds": {"A1": 85.3, "A2": 119.3,
                                      "A3": 137.7, "B1": 85.3,
                                      "B2": 107.3, "B3": 98.8}}


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

for channel_id, pin in Pumps.items():
    GPIO.setup(pin, GPIO.OUT)

print("Pumps initialized")

# HIGH = STOP PUMP
# LOW = START PUMP


def start_pump(channel_id):
    GPIO.output(Pumps[channel_id], GPIO.LOW)


def stop_pump(channel_id):
    GPIO.output(Pumps[channel_id], GPIO.HIGH)


def start_all_pumps():
    for channel_id, pin in Pumps.items():
        start_pump(channel_id)
    print("All pumps stopped")


def stop_all_pumps():
    for channel_id, pin in Pumps.items():
        stop_pump(channel_id)
    print("All pumps stopped")


def test_pump(channel_id, seconds):
    start_pump(channel_id)
    sleep(seconds)
    stop_pump(channel_id)


def test_pumps_sequentially():
    for channel_id, pin in Pumps.items():
        test_pump(channel_id, 1)


def test_pumps_simultaneously():
    for channel_id, pin in Pumps.items():
        start_pump(channel_id)
    sleep(99)
    for channel_id, pin in Pumps.items():
        stop_pump(channel_id)


def seconds_for_pump(channel_id, ml):
    seconds_for_100ml = PumpsCalibration["100ml_seconds"][channel_id]
    seconds_required = seconds_for_100ml / 100 * ml
    return seconds_required


def seconds_to_ml(channel_id, seconds):
    seconds_for_100ml = PumpsCalibration["100ml_seconds"][channel_id]
    ml = (seconds / seconds_for_100ml) * 100
    return ml


stop_all_pumps()


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
    #     pass

    try:
        start_time = time.time()
        print("Current time:", time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(start_time)))

        ml = 100

        start_all_pumps()

        for i in range(9999):
            elapsed_time = time.time() - start_time
            print("Elapsed time:", elapsed_time, "seconds")
            time.sleep(0.0999)  # Wait for 0.1 second

            for channel_id in Pumps.keys():
                seconds = seconds_for_pump(channel_id, ml)

                if (elapsed_time > seconds):
                    stop_pump(channel_id)

            if (elapsed_time > 150):
                break

        stop_all_pumps()

    except SystemExit:
        # Handle
        pass


#     test_pump(1, 1) #1
#     test_pump(2, 1) #2
#     test_pump(3, 10) #3
