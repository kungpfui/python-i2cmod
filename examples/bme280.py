#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Bosch Sensortec BME280 pressure, temperature and humidity sensor.

`BME280 Datasheet <https://ae-bst.resource.bosch.com/media/_tech/media/datasheets/BST-BME280_DS001-12.pdf>`
"""

from i2cmod import BME280

def example():
    """ Output data to screen """
    with BME280(altitude=414.0) as sensor:
        print("Chip ID:       {:02X}".format(sensor.id))
        sensor.update()
        print("Pressure:      {:.2f} hPa ".format(sensor.pressure))
        print("Pressure NN:   {:.2f} hPa ".format(sensor.pressure_sea_level))
        print("Temperature:   {:.2f} C".format(sensor.centigrade))
        print("Humidity:      {:.2f} %".format(sensor.humidity))


if __name__ == '__main__':
    example()
