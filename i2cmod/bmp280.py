#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bosch Sensortec BMP280 pressure and temperature sensor.

`BMP280 Datasheet <https://ae-bst.resource.bosch.com/media/_tech/media/datasheets/BST-BMP280-DS001-19.pdf>`
"""

import enum
import time
import struct
import logging
from typing import Union, Iterable, Optional
from smbus2 import SMBus


class Reg(enum.IntEnum):
    """I2C registers"""
    id          = 0xD0
    reset       = 0xE0
    status      = 0xF3
    control     = 0xF4
    config      = 0xF5
    pressure    = 0xF7  # ... 0xF9
    temperature = 0xFA  # ... 0xFC
    calibration = 0x88  # ... 0xA1


class BMP280(SMBus):
    """
    Bosch Sensortec BMP280 pressure and temperature sensor.
    """

    def __init__(self, bus: Union[int, str]=1, device_addr: int=0x76, altitude: float=500.0):
        """Initialize Object.

        :param bus: I2C bus identification number or a filesystem name like `/dev/i2c-something`
        :param device_addr: I2C address 0x76 or 0x77
        :param altitude:  altitude as meters above sea level
        """
        SMBus.__init__(self, bus, force=True)
        self.device_addr = device_addr
        self.altitude = altitude

        self._temperature = None
        self._pressure = None
        self.t_fine = 0

        modified = self._configure()
        if modified is not None:
            time.sleep(4.0)

    def read_register(self, register: int, length: Union[int, str] = 1) -> Union[int, tuple, bytes]:
        """Read register

        :param register: register address to read
        :param length: bytes to read. Either an :type:int value or a `struct` format string
        :return: bytes if length is int. tuple if length is `struct` format string
        """
        struct_obj = None
        if isinstance(length, str):
            struct_obj = struct.Struct(length)
            length = struct_obj.size

        data = self.read_i2c_block_data(self.device_addr, register, length)
        if struct_obj is None:
            return bytes(data)

        data = struct_obj.unpack(bytes(data))
        return data[0] if len(data) == 1 else data

    def modify_register(self,
                        register: int,
                        set_msk: Union[Iterable, int],
                        clr_msk: Optional[Union[Iterable, int]] = None) -> Optional[int]:
        """read, modify and conditionally write to I2C register(s)

        :param register:  register address/command
        :param set_msk:   bit-mask which defined the bits to set (=1)
        :param clr_msk:   bit-mask which defines the bits to clear (=0). Can be None which means
                          that all bits will be cleared.
        :return: number of bytes modified. None means no modification was needed and therefore
                 not register write operation was done.
        """
        if isinstance(set_msk, int):
            set_msk = bytes((set_msk,))
        if clr_msk is None:
            clr_msk = [0xFF] * len(set_msk)
        if isinstance(clr_msk, int):
            clr_msk = bytes((clr_msk,))

        reg_value = self.read_register(register, len(set_msk))
        value = [(reg & ~_and | _or) & 0xFF for reg, _and, _or in zip(reg_value, clr_msk, set_msk)]

        # already set?
        if bytes(value) == reg_value:
            return None
        self.write_i2c_block_data(self.device_addr, register, value)
        return len(value)

    def _configure(self) -> bool:
        """Setup sensor IC.
        :return: true if any register has been modified else false.
        """
        # read temperature and pressure compensation data
        coeff = self.read_register(Reg.calibration, '<H2hH8h')
        # scale these coefficients already here. The later calculation in :method:update looks much more simple
        binary_exp = [-10, 0, -6,  # temperature coeff
                      0, -34, -53, 4, -13, -29, -4, -19, -35]  # pressure coeff
        scaled_coeff = [coeff * 2.0 ** binexp for coeff, binexp in zip(coeff, binary_exp)]
        self.T = scaled_coeff[:3]
        self.P = scaled_coeff[3:]

        # select configuration register: standby time = 1000 ms
        modified = self.modify_register(Reg.config, (5 << 5) | (2 << 2) | (0 << 0))

        # select control measurement register:  pressure/temperature oversampling rate = 1, normal mode
        modified = self.modify_register(Reg.control, (1 << 5) | (3 << 2) | (3 << 0)) or modified
        return modified

    @property
    def altitude(self) -> float:
        """Altitude in meters."""
        return self._altitude

    @altitude.setter
    def altitude(self, altitude: float):
        """Altitude in meters."""
        self._altitude = altitude

        assert altitude < 11000.0
        g0 = 9.80665
        M = 0.0289644
        R = 8.3144598
        T0 = 288.15
        L0 = -0.0065
        h0 = 0.0
        exponent = (g0 * M) / (R * L0)
        self._pressure_coefficent = (T0 / (T0 + L0 * (altitude - h0))) ** -exponent

    @property
    def id(self):
        return self.read_register(Reg.id)[0]

    def reset(self):
        return self.write_byte_data(self.device_addr, Reg.reset, 0xB6)

    @property
    def status(self):
        return self.read_register(Reg.status)[0]

    @property
    def pressure(self):
        """call update() before"""
        return self._pressure

    @property
    def centigrade(self):
        """call update() before"""
        return self._temperature

    @property
    def fahrenheit(self):
        """call update() before"""
        return self._temperature * 1.8 - 32.0

    @property
    def temperature(self):
        """call update() before"""
        return self._temperature + 273.15

    @property
    def pressure_sea_level(self):
        """normalized pressure - at sea level"""
        return self._pressure * self._pressure_coefficent

    def update(self):
        """Update ADC values and calculates the new values for
        - temperature
        - pressure

        :return: None
        """
        # read ADC values, pressure and temperature at the same time
        data = self.read_register(Reg.pressure, 6)

        # convert pressure and temperature data to 20 bits
        adc_p, adc_t = struct.unpack('>II', b'\0' + data[:3] + b'\0' + data[3:])
        adc_p = 2**20 - (adc_p >> 4)
        adc_t = 2**-14 * (adc_t >> 4)

        # temperature calculations
        temp1 = adc_t - self.T[0]
        self._t_fine = temp1 * (self.T[1] + temp1 * self.T[2])
        # limit temperature to -40 ... +85C
        self._temperature = max(-40.0, min(self._t_fine / 5120.0, +85.0))

        # pressure calculations
        t_press = (self._t_fine * 0.5) - 64000.0

        press1 = t_press * (self.P[1] + t_press * self.P[2])
        press1 *= self.P[0]
        press1 += self.P[0]

        press2 = t_press * (self.P[4] + t_press * self.P[5])
        press2 += self.P[3]

        try:
            press3 = (adc_p - press2) * 6250.0 / press1
            press3 += press3 * (self.P[7] + press3 * self.P[8])
            press3 += self.P[6]

            # limit to range between 300hPa and 1100hPa
            press3 = max(300.0e2, min(press3, 1100.0e2))
            self._pressure = press3 / 100.0  # hecto

        except ZeroDivisionError:
            self._pressure = 0.0


def example():
    """ Output data to screen """
    with BMP280(altitude=414.0) as sensor:
        print("Chip ID: {:02X}".format(sensor.id))
        sensor.update()
        print("Pressure:    {:.2f} hPa ".format(sensor.pressure))
        print("Pressure NN: {:.2f} hPa ".format(sensor.pressure_sea_level))
        print("Temperature: {:.2f} °C".format(sensor.centigrade))


if __name__ == '__main__':
    example()
