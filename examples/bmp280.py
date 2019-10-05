#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Bosch Sensortec BMP280 pressure and temperature sensor.

`BMP280 Datasheet <https://ae-bst.resource.bosch.com/media/_tech/media/datasheets/BST-BMP280-DS001-19.pdf>`
"""

from i2cmod import BMP280

def example():
    """ Output data to screen """
    with BMP280(altitude=414.0) as sensor:
        print("Chip ID:       {:02X}".format(sensor.id))
        sensor.update()
        print("Pressure:      {:.2f} hPa ".format(sensor.pressure))
        print("Pressure NN:   {:.2f} hPa ".format(sensor.pressure_sea_level))
        print("Temperature:   {:.2f} °C".format(sensor.centigrade))


if __name__ == '__main__':
    example()
