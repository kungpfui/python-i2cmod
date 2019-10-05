#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sensirion SHT2x humidity sensor.

Drives SHT20, SHT21 and SHT25 humidity and temperature sensors.
Sensirion `SHT2x Datasheets <https://www.sensirion.com/en/environmental-sensors/humidity-sensors/humidity-temperature-sensor-sht2x-digital-i2c-accurate/>`
"""

from i2cmod import SHT2X

def example():
    with SHT2X() as sensor:
        print("Identification: 0x{:016X}".format(sensor.serial_number))

        for adc_res, reg_value in (
                ('12/14', 0x02),
                (' 8/10', 0x03),
                ('10/13', 0x82),
                ('11/11', 0x83)):
            sensor.user_register = reg_value
            print("-" * 79)
            print("Resolution:     {}-bit (rh/T)".format(adc_res))
            print("Temperature:    {:.2f} C".format(sensor.centigrade))
            print("Temperature:    {:.2f} F".format(sensor.fahrenheit))
            print("Humidity:       {:.2f} % ".format(sensor.humidity))
            print("User Register:  0x{:02X}".format(sensor.user_register))


if __name__ == '__main__':
    example()
