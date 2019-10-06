#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vishay VEML6075: UV-A/B light sensor.
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
    uva     = 0x07
    uvb     = 0x09
    uvcomp1 = 0x0A
    uvcomp2 = 0x0B
    id      = 0x0C


class VEML6075(SMBus):
    # max 16-bit value
    overflow = (1 << 16) - 1
    # auto-ranging: underflow with some margin. 80% of half value
    underflow = (1 << 15) * 4 // 5

    MAX_IT = 4  # max integration time

    def __init__(self, bus: Union[int, str] = 1, device_addr: int = 0x10) -> None:
        """Initialize Object.

        :param bus: I2C bus identification number or a filesystem name like `/dev/i2c-something`
        :param device_addr: I2C device address, normally 0x10
        """
        SMBus.__init__(self, bus, force=True)
        self.device_addr = device_addr

        self._integration_time = None
        self.uvab = None
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
        """update UV values and adjust the integration time as needed"""
        _dir = 0

        while True:
            # set integration time ... and automatic mode with enabled color sensor
            self._integration_time += _dir
            self.update_integration_time()

            #
            self.uvab = [
                self.read_word_data(reg)
                for reg in (Reg.uva, Reg.uvb, Reg.uvcomp1, Reg.uvcomp2)
            ]

            # auto range algorithm
            # overflow?
            if max(self.uvab) == self.overflow:
                if self._integration_time > 0:
                    _LOG.debug('Overflow occurred')
                    _dir = -1
                    continue

            # underflow?
            elif dir != -1 and max(self.uvab) < self.underflow:
                if self._integration_time < self.MAX_IT:
                    _LOG.debug('Underflow occurred')
                    _dir = 1
                    continue

            return

    def update_integration_time(self):
        """Updates the integration time."""
        integration_time = (self.control >> 4) & 0x7
        _LOG.info('Integration time: {}'.format(integration_time))

        if self._integration_time is None:
            self._integration_time = min(self.MAX_IT, integration_time)
        assert 0 <= self._integration_time <= self.MAX_IT

        if self._integration_time != integration_time:
            # configure control register
            # 50ms integration, no trigger, auto mode, uv sensor on
            self.control = self._integration_time << 4
            time.sleep(0.055 * 2 ** self._integration_time)

    @property
    def control(self) -> int:
        return self.read_word_data(Reg.control)

    @control.setter
    def control(self, value):
        self.write_word_data(Reg.control, value)

    @property
    def uva(self) -> int:
        """20-bit ADC value of UV-A channel"""
        return self.uvab[0] * 2 ** (self.MAX_IT - self._integration_time)

    @property
    def uvb(self) -> int:
        """20-bit ADC value of UV-B channel"""
        return self.uvab[1] * 2 ** (self.MAX_IT - self._integration_time)

    @property
    def uvcomp1(self) -> int:
        """20-bit ADC value of UV Comp1 channel"""
        return self.uvab[2] * 2 ** (self.MAX_IT - self._integration_time)

    @property
    def uvcomp2(self) -> int:
        """20-bit ADC value of UV Comp2 channel"""
        return self.uvab[3] * 2 ** (self.MAX_IT - self._integration_time)

    @property
    def id(self) -> int:
        return self.read_word_data(Reg.id)

    @property
    def uva_calc(self) -> int:
        a = 2.22
        b = 1.33
        return max(0, round(self.uva - a * self.uvcomp1 - b * self.uvcomp2))

    @property
    def uvb_calc(self) -> int:
        c = 2.95
        d = 1.74
        return max(0, round(self.uvb - c * self.uvcomp1 - d * self.uvcomp2))

    @property
    def uva_index(self) -> float:
        """UV-A Index"""
        responsivity = 0.001461 * 2 ** (1 - self.MAX_IT) # sensitivity @ IT=100ms
        return responsivity * (self.uva_calc)

    @property
    def uvb_index(self) -> float:
        """UV-B Index"""
        responsivity = 0.002591 * 2 ** (1 - self.MAX_IT)  # sensitivity @ IT=100ms
        return responsivity * (self.uvb_calc)

    @property
    def uv_index(self) -> float:
        """UV Index"""
        return (self.uva_index + self.uvb_index) / 2

    @property
    def uva_intensity(self) -> float:
        """UV-A W/m^2"""
        responsivity = 0.93e-2 * 2 ** -self.MAX_IT  # sensitivity @ IT=50ms
        return responsivity * (self.uva_calc)

    @property
    def uvb_intensity(self) -> float:
        """UV-B W/m^2"""
        responsivity = 2.1e-2 * 2 ** - self.MAX_IT  # sensitivity @ IT=50ms
        return responsivity * (self.uvb_calc)


def example():
    # Output data to screen
    with VEML6075() as uv_sensor:
        print ('ID      : {:04X}'.format(uv_sensor.id))

        uv_sensor.update()
        print ('UV-A    : {}'.format(uv_sensor.uva))
        print ('UV-B    : {}'.format(uv_sensor.uvb))
        print ('UVcomp1 : {}'.format(uv_sensor.uvcomp1))
        print ('UVcomp2 : {}'.format(uv_sensor.uvcomp2))

        print ('UV-A W/m^2: {:.3f}'.format(uv_sensor.uva_intensity))
        print ('UV-B W/m^2: {:.3f}'.format(uv_sensor.uvb_intensity))

        print ('UV-A Index: {:.3f}'.format(uv_sensor.uva_index))
        print ('UV-B Index: {:.3f}'.format(uv_sensor.uvb_index))
        print ('UV Index: {:.3f}'.format(uv_sensor.uv_index))


if __name__ == '__main__':
    example()
