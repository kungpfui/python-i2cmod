#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# $Id: bme280.py 372 2018-11-04 09:31:50Z stefan $

"""
Bosch Sensortec BME280 pressure, temperature and humidity sensor.

`BME280 Datasheet <https://ae-bst.resource.bosch.com/media/_tech/media/datasheets/BST-BME280_DS001-12.pdf>`
"""

import enum
from typing import Union
from .bmp280 import BMP280


class Reg(enum.IntEnum):
    """I2C registers"""
    control       = 0xF2
    calibration25 = 0xA1
    calibration26 = 0xE1  # ... 0xF0
    humidity      = 0xFD  # ... 0xFE


class BME280(BMP280):
    """
    Bosch Sensortec BME280 pressure, temperature and humidity sensor.
    """

    def __init__(self, bus: Union[int, str] = 1, device_addr: int = 0x76, altitude: float = 500.0):
        """Initialize Object.

        :param bus: I2C bus identification number or a filesystem name like `/dev/i2c-something`
        :param device_addr: I2C address 0x76 or 0x77
        :param altitude:  altitude as meters above sea level
        """
        BMP280.__init__(self, bus, device_addr, altitude)
        self._humidity = None

    def _configure(self):
        """Override BMP280's :meth:_configuration"""
        # read out the calibration coefficients
        coeff_h = [self.read_register(Reg.calibration25, '<B')] \
            + list(self.read_register(Reg.calibration26, '<hB3BB'))

        # convert and re-order the calibration coefficients
        coeff_h[3] = (coeff_h[3] << 4) + (coeff_h[4] & 0xF)
        if coeff_h[3] & 0x800:
            coeff_h[3] -= 2**12
        coeff_h[5] = (coeff_h[5] << 4) + (coeff_h[4] >> 4)
        if coeff_h[5] & 0x800:
            coeff_h[5] -= 2**12
        del coeff_h[4]

        # scale the calibration coefficients
        binary_exp = [-19, -16, -26, 6, -14, -26]  # humidity coeff
        self.H = [coeff * 2.0 ** binexp for coeff, binexp in zip(coeff_h, binary_exp)]

        # configure ADC sampling:  4x oversampled humidity
        modified = self.modify_register(Reg.control, (3 << 0))

        return BMP280._configure(self) or modified

    @property
    def humidity(self):
        """ humidty """
        return self._humidity

    def update(self):
        """does the measuremnts"""
        BMP280.update(self)

        # read humidity ADC values
        adc_h = self.read_register(Reg.humidity, '>H')

        # humidity calculations
        h1 = self._t_fine - 76800.0
        h2 = self.H[3] + self.H[4] * h1
        h5 = 1.0 + self.H[2] * h1
        h6 = 1.0 + self.H[5] * h1 * h5
        var_h = (adc_h - h2) * self.H[1] * h5 * h6
        var_h *= (1.0 - self.H[0] * var_h)

        # my Bosch -> Sensirion correction
        # somehow Bosch sensors show a very low humidity percentage. The difference
        # between Sensirion SHT31 and Bosch is very close to 10%
        # var_h += 10.0
        self._humidity = max(0.0, min(var_h, 100.0))


def example():
    """ Output data to screen """
    with BME280(altitude=414.0) as sensor:
        print("Chip ID: {:02X}".format(sensor.id))
        sensor.update()
        print("Pressure:    {:.2f} hPa ".format(sensor.pressure))
        print("Pressure NN: {:.2f} hPa ".format(sensor.pressure_sea_level))
        print("Temperature: {:.2f} C".format(sensor.centigrade))
        print("Humidity:    {:.2f} %".format(sensor.humidity))


if __name__ == '__main__':
    example()
