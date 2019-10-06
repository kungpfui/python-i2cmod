#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vishay VEML6040: red green blue and white light sensor.
"""

import time
import enum
import logging
from typing import Union, List
from smbus2 import SMBus

_LOG = logging.getLogger(__name__)


class Reg(enum.IntEnum):
    """I2C registers"""
    control = 0x00
    red     = 0x08
    green   = 0x09
    blue    = 0x0A
    white   = 0x0B


class VEML6040(SMBus):
    # max 16-bit value
    overflow = (1 << 16) - 1
    # auto-ranging: underflow with some margin. 80% of half value
    underflow = (1 << 15) * 4 // 5

    MAX_IT = 5  # max integration time

    def __init__(self, bus: Union[int, str] = 1, device_addr: int = 0x10) -> None:
        """Initialize Object.

        :param bus: I2C bus identification number or a filesystem name like `/dev/i2c-something`
        :param device_addr: I2C device address, normally 0x10
        """
        SMBus.__init__(self, bus, force=True)
        self.device_addr = device_addr

        self._integration_time = None
        self.rgbw = None
        self._configure()

    def _configure(self):
        """Initial chip configurations."""
        self.update_integration_time()

    def read_word_data(self, *args, **kwargs):
        """Overridden :method:`read_word_data` from :class:`SMBus` without I2C address parameter."""
        return SMBus.read_word_data(self, self.device_addr, *args, **kwargs)

    def write_word_data(self, *args, **kwargs):
        """Overridden :method:`write_word_data` from :class:`SMBus` without I2C address parameter."""
        return SMBus.write_word_data(self, self.device_addr, *args, **kwargs)

    def update(self):
        """measures and update RGBW values and adjust the integration time as needed."""
        _dir = 0

        while True:
            # set integration time ... and automatic mode with enabled color sensor
            self._integration_time += _dir
            self.update_integration_time()

            #
            self.rgbw = [
                self.read_word_data(reg)
                for reg in (Reg.red, Reg.green, Reg.blue, Reg.white)
            ]

            # auto range algorithm
            # overflow?
            if max(self.rgbw) == self.overflow:
                if self._integration_time > 0:
                    _LOG.debug('Overflow occurred')
                    _dir = -1
                    continue

            # underflow?
            elif dir != -1 and max(self.rgbw) < self.underflow:
                if self._integration_time < self.MAX_IT:
                    _LOG.debug('Underflow occurred')
                    _dir = 1
                    continue
            return

    def update_integration_time(self):
        """Updates the integration time."""
        integration_time = (self.control >> 4) & 0x7

        if self._integration_time is None:
            self._integration_time = min(self.MAX_IT, integration_time)
        assert 0 <= self._integration_time <= self.MAX_IT

        if self._integration_time != integration_time:
            # configure control register
            # 40ms integration, no trigger, auto mode, color sensor on
            self.control = self._integration_time << 4
            time.sleep(0.050 * 2 ** self._integration_time)

    @property
    def control(self) -> int:
        return self.read_word_data(Reg.control)

    @control.setter
    def control(self, value):
        self.write_word_data(Reg.control, value)

    @property
    def red(self) -> int:
        """21-bit ADC value of red channel"""
        return self.rgbw[0] * 2 ** (5 - self._integration_time)

    @property
    def green(self) -> int:
        """21-bit ADC value of green channel"""
        return self.rgbw[1] * 2 ** (5 - self._integration_time)

    @property
    def blue(self) -> int:
        """21-bit ADC value of blue channel"""
        return self.rgbw[2] * 2 ** (5 - self._integration_time)

    @property
    def white(self) -> int:
        """21-bit ADC value of white channel"""
        return self.rgbw[3] * 2 ** (5 - self._integration_time)

    @property
    def luminance(self) -> float:
        """Ambient luminance as [Lux]=lx"""
        scale = 16496.0 * (2 ** -5) / (2 ** 16 - 1)
        return scale * self.green

    def _XYZ(self, location: str) -> list:
        """RGB -> XYZ transformation

        :param location: either 'indoor' or 'outdoor'
        :return: RGB -> XYZ color room
        """
        corr_coeff = dict(
            indoor=(
                (-0.023249, 0.291014, -0.364880),
                (-0.042799, 0.272148, -0.279591),
                (-0.155901, 0.251534, -0.076240)
            ),
            outdoor=(
                (0.048403, 0.183633, -0.253589),
                (0.022916, 0.176388, -0.183205),
                (-0.077436, 0.124541, 0.032081)
            )
        )
        mat = corr_coeff[location]
        #~ return mat @ self.rgbw  # py >= 3.7
        return [
            sum([m * rgb for m, rgb in zip(mat[row], self.rgbw)])
            for row in range(3)
        ]

    @property
    def temperature(self, location: str = 'indoor') -> float:
        """ color temperature

        :param location: either 'indoor' or 'outdoor'
        :return: Color temperature in Kelvin.
        """
        XYZ = self._XYZ(location)
        try:
            x = XYZ[0] / sum(XYZ)
            y = XYZ[1] / sum(XYZ)

            # McCamy
            xe = 0.3320
            ye = 0.1858
            n = (x - xe) / (y - ye)
            CCT = -449 * n**3 + 3525 * n**2 - 6823.3 * n + 5520.33
        except ZeroDivisionError:
            return 6500.0

        return max(500.0, min(CCT, 10000.0))


def example():
    # Output data to screen
    with VEML6040() as rgbw_sensor:
        rgbw_sensor.update()
        print('red         : {}'.format(rgbw_sensor.red))
        print('green       : {}'.format(rgbw_sensor.green))
        print('blue        : {}'.format(rgbw_sensor.blue))
        print('white       : {}'.format(rgbw_sensor.white))

        print('luminance   : {:.2f} lux'.format(rgbw_sensor.luminance))
        print('temperature : {} K'.format(int(rgbw_sensor.temperature)))


if __name__ == '__main__':
    example()
