#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Maxim Integrated MAX44009 ambient light sensor I2C driver.

MAX44009 is a very low power ambient light sensor which is
mostly SMBus compatible.

`MAX44009 Datasheet <https://datasheets.maximintegrated.com/en/ds/MAX44009.pdf>`
"""

from i2cmod import MAX44009


def example():
    """Output data to screen"""
    with MAX44009() as ambient_sensor:
        print('Ambient light luminance : {:.2f} lux'.format(ambient_sensor.luminance))


if __name__ == '__main__':
    example()
