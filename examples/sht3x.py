#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sensirion SHT3x humidity sensor.

Drives SHT30, SHT31 and SHT35 humidity and temperature sensors.
Sensirion `SHT3x Datasheets <https://www.sensirion.com/en/environmental-sensors/humidity-sensors/humidity-temperature-sensor-sht3x-digital-i2c-accurate/>`
"""

from i2cmod import SHT2X

def example():
    with SHT3X() as sensor:
        #~ print("Identification: 0x{:016X}".format(sensor.serial_number))

        for repeatablity in ('low', 'medium', 'high'):
            print("-" * 79)
            print("Repeatablity:   {}".format(repeatablity))
            sensor.update(repeatablity)
            print("Temperature:    {:.2f} C".format(sensor.centigrade))
            print("Temperature:    {:.2f} F".format(sensor.fahrenheit))
            print("Humidity:       {:.2f} % ".format(sensor.humidity))
            print("Status:         0x{:02X}".format(sensor.status))


if __name__ == '__main__':
    example()
