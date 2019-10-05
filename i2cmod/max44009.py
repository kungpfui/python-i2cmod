#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# $Id: max44009.py 347 2018-08-12 14:28:16Z Stefan $

"""
Maxim Integrated MAX44009 ambient light sensor I2C driver.

MAX44009 is a very low power ambient light sensor which is
mostly SMBus compatible.

`MAX44009 Datasheet <https://datasheets.maximintegrated.com/en/ds/MAX44009.pdf>`
"""

import enum
import logging
import unittest
from typing import Union
from smbus2 import SMBus, i2c_msg


_LOG = logging.getLogger(__name__)


class Reg(enum.IntEnum):
    """MAX44009 registers."""
    interrupt_status = 0x00
    interrupt_enable = 0x01
    configuration    = 0x02
    luminance_msb    = 0x03
    luminance_lsb    = 0x04
    upper_threshold  = 0x05
    lower_threshold  = 0x06
    threshold_timer  = 0x07


class MAX44009(SMBus):
    def __init__(self, bus: Union[int, str]=1, device_addr: int=0x4A) -> None:
        """ Initialize Object.

        :param bus: I2C bus identification number or a filesystem name like `/dev/i2c-something`
        :param device_addr: I2C device address, normally 0x4A
        """
        SMBus.__init__(self, bus, force=True)

        self.device_addr = device_addr
        self._configure()

    def read_byte_data(self, *args, **kwargs):
        """Overridden :method:`read_byte_data` from :class:`SMBus` without I2C address parameter."""
        return SMBus.read_byte_data(self, self.device_addr, *args, **kwargs)

    def write_byte_data(self, *args, **kwargs):
        """Overridden :method:`write_byte_data` from :class:`SMBus` without I2C address parameter."""
        return SMBus.write_byte_data(self, self.device_addr, *args, **kwargs)

    def _configure(self) -> None:
        """ Initial device configuration.

        Usees continuous mode and automatic ranging.
        """
        reg_data = self.configuration
        conf_data = reg_data & ~0xC0 | 0x80
        # check if already in the right configuration, do not re-configure on and on again
        if reg_data != conf_data:
            self.configuration = conf_data

    @property
    def configuration(self) -> int:
        return self.read_byte_data(Reg.configuration)

    @configuration.setter
    def configuration(self, value: int):
        self.write_byte_data(Reg.configuration, value)

    @property
    def luminance(self) -> float:
        """Get 12-bit luminance value. 8-bit value with 4-bit exponent.

        :meth:`SMBus.read_byte_data` is not able to read two bytes with a
        re-start sequence in between which is needed by MAX44009 for correct results.

        There will be two options:
        1. Just re-read MSB byte and detected changes of MSB which is an indication
           for a new measurement.
        2. use :method:`i2c_rdwr` which is supported by `smbus2` but unluckily does
           not work on Raspi (OSError: [Errno 95] Operation not supported)
        """
        use_option = 1

        if use_option == 1:
            # 1st option
            msb = 0
            msb_2nd = 1
            while msb != msb_2nd:
                msb = self.read_byte_data(Reg.luminance_msb)
                lsb = self.read_byte_data(Reg.luminance_lsb)
                msb_2nd = self.read_byte_data(Reg.luminance_msb)

        elif use_option == 2:
            # 2nd option, which does not work on rpi OSError: [Errno 95] Operation not supported
            wr_msb = i2c_msg.write(self.device_addr, [Reg.luminance_msb])
            rd_msb = i2c_msg.read(self.device_addr, 1)
            wr_lsb = i2c_msg.write(self.device_addr, [Reg.luminance_lsb])
            rd_lsb = i2c_msg.read(self.device_addr, 1)
            self.i2c_rdwr(wr_msb, rd_msb, wr_lsb, rd_lsb)
            msb = ord(rd_msb.data)
            lsb = ord(rd_lsb.data)

        # Convert the data to lux
        exponent = (msb & 0xF0) >> 4
        mantissa = ((msb & 0x0F) << 4) | (lsb & 0x0F)
        return 2.0 ** exponent * mantissa * 0.045


def example():
    """Output data to screen"""
    with MAX44009() as ambient_sensor:
        print('Ambient light luminance : {:.2f} lux'.format(ambient_sensor.luminance))


if __name__ == '__main__':
    example()
