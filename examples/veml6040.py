#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vishay VEML6040: red green blue and white light sensor.
"""

from i2cmod import VEML6040


def example():
    # Output data to screen
    with VEML6040() as rgbw_sensor:
        rgbw_sensor.update()
        print('red   :       {}'.format(rgbw_sensor.red))
        print('green :       {}'.format(rgbw_sensor.green))
        print('blue  :       {}'.format(rgbw_sensor.blue))
        print('white :       {}'.format(rgbw_sensor.white))

        print('luminance :   {:.2f} lux'.format(rgbw_sensor.luminance))
        print('temperature : {} K'.format(int(rgbw_sensor.temperature)))


if __name__ == '__main__':
    example()
