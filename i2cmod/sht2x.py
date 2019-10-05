#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sensirion SHT2x humidity sensor I2C driver.

Drives SHT20, SHT21 and SHT25 humidity and temperature sensors.
Sensirion `SHT2x Datasheets <https://www.sensirion.com/en/environmental-sensors/humidity-sensors/humidity-temperature-sensor-sht2x-digital-i2c-accurate/>`
"""

import time
import enum
import struct
import logging
import unittest
from typing import Union, ByteString, Optional
from smbus2 import SMBus, i2c_msg


_log = logging.getLogger(__name__)


class Reg(enum.IntEnum):
    temperature = 0xF3   # measure - no hold master
    humidity = 0xF5      # measure - no hold master
    write_user_register = 0xE6
    read_user_register = 0xE7
    soft_reset = 0xFE


class SHT2X(SMBus):
    """humidity-temperature sensors SHT20, SHT21 and SHT25."""
    def __init__(self, bus: Union[int, str] = 1, device_addr: int = 0x40) -> None:
        """Initialize

        :param bus: I2C bus identification number or a filesystem name like `/dev/i2c-something`
        :param device_addr: I2C device address, normally 0x40
        """
        SMBus.__init__(self, bus, force=True)
        self.crc8 = SHT2X.crc8_msbf_math  # CRC method to use

        self.device_addr = device_addr
        self._configure()

    def i2c_read_write(self, write: Union[int, ByteString], read: int = 0, rdelay: Optional[float] = None) -> Union[ByteString, int]:
        """ Generic I2C read/write operation.

        :param write: stream to send
        :param read: number of bytes to read
        :param rdelay: read delay
        :return: read bytes if final operation is read else int with number of bytes written
        """
        if isinstance(write, int):
            write = bytes((write,))

        messages = [i2c_msg.write(self.device_addr, write)]
        if rdelay is not None:
            # write it already and wait afterwards
            self.i2c_rdwr(*messages)
            messages.clear()
            time.sleep(rdelay)

        if read > 0:
            # append read message and execute
            rd_msg = i2c_msg.read(self.device_addr, read)
            messages.append(rd_msg)
            self.i2c_rdwr(*messages)
            messages.clear()
            return bytes(tuple(rd_msg))

        if messages:
            self.i2c_rdwr(*messages)
            messages.clear()
        return len(write)

    def _configure(self) -> None:
        """Initial device configuration."""
        # just do a soft-reset -> ADC-T_res=14bit ADC-RH_res=12bit which are the highest resolutions
        self.soft_reset()

    def soft_reset(self):
        """Soft reset"""
        self.i2c_read_write(Reg.soft_reset, 0, 0.050)

    @property
    def user_register(self) -> int:
        """read user register"""
        return self.i2c_read_write(Reg.read_user_register, 1)[0]

    @user_register.setter
    def user_register(self, value: int):
        """write to user register.

        :param value: byte to write into `user register`
        """
        # datasheet states: do not change bits 3, 4, 5 -> so read-modify this register
        usr_reg = (self.user_register & 0x38 | value)
        self.i2c_read_write([Reg.write_user_register, usr_reg])

    @property
    def centigrade(self) -> Optional[float]:
        """Celsius temperature measurement (no hold master), blocking for max 85ms.

        :return: temperature or None on error
        """

        # wait, typ=66ms, max=85ms @ 14Bit resolution
        data = self.i2c_read_write(Reg.temperature, 3, 0.086)

        if self.crc8(data) == 0:
            t = struct.unpack('>Hx', data)[0] & 0xFFFC  # set status bits to zero
            return -46.82 + ((t * 175.72) * 2.0**-16)

    @property
    def fahrenheit(self) -> Optional[float]:
        """Fahrenheit temperature measurment.

        :return: temperature or None on error
        """
        temperature = self.centigrade
        if temperature is not None:
            return temperature * 1.8 + 32.0

    @property
    def humidity(self) -> Optional[float]:
        """RH measurement (no hold master), blocking for max 32ms

        :return: relative humidity as % or None on error
        """
        # wait, typ=22ms, max=29ms @ 12Bit resolution
        data = self.i2c_read_write(Reg.humidity, 3, 0.030)

        if self.crc8(data) == 0:
            rh = struct.unpack('>Hx', data)[0] & 0xFFFC  # zero the status bits
            rh = -6.0 + ((125.0 * rh) * 2.0**-16)
            return max(0.0, min(rh, 100.0))

    @property
    def serial_number(self) -> Optional[int]:
        """Read the serial number of the chip.

        :return: serial number as int or None on error.
        """
        sn_0 = self.i2c_read_write(b'\xFA\x0F', 8)
        sn_1 = self.i2c_read_write(b'\xFC\xC9', 6)

        # check all crc's
        crc_result = True
        for data in (sn_0[:2], sn_0[2:4], sn_0[4:6], sn_0[6:], sn_1[:3], sn_1[3:]):
            crc_result &= self.crc8(data) == 0

        if crc_result:
            return struct.unpack('>Q', sn_1[3:5] + sn_0[0:8:2] + sn_1[0:2])[0]

    @staticmethod
    def crc8_msbf_bitwise(data: ByteString, crc: int = 0, polynom: int = 0x131) -> int:
        """Calculates CRC checksum of data

        It's CRC8 most-significant-bit-first calculation.
        When `data` is inclusive CRC the result is 0. That's CRC magic.

        :param data: data bytes
        :param crc: inital crc value, normally 0
        :param polynom: polynom to use, normally 0x131 = x^8 + x^5 + x^4 + 1
        :return: CRC value.
        """
        for d in data:
            crc ^= d

            for bit in range(8):
                crc <<= 1
                if crc & 0x100:
                    crc ^= polynom

        return crc

    @staticmethod
    def crc8_msbf_math(data: ByteString, crc: int = 0) -> int:
        """Calculates CRC checksum of data with Polynom x^8 + x^5 + x^4 + 1

        It's CRC8 most-significant-bit-first calculation with optimized mathematics.
        It's inlined and normally ~3x faster than :method:`crc8_msbf_bitwise`

        :param data: data bytes
        :param crc: inital crc value, normally 0
        :return: CRC value
        """
        for d in data:
            crc ^= d
            crc ^= ((crc >> 3) ^ (crc >> 4) ^ (crc >> 6))
            crc ^= ((crc << 4) ^ (crc << 5)) & 0xFF
        return crc


def example():
    """Output data to screen"""

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
            print("Humidity:       {:.2f} % ".format(sensor.humidity))
            print("User Register:  0x{:02X}".format(sensor.user_register))



class TestSHT2XMethods(unittest.TestCase):
    """Very basic unittest"""
    def setUp(self):
        logging.basicConfig(level=logging.INFO)

    def test_crc(self):
        """Check all possible 2-byte streams."""
        for i in range(1<<16):
            input = struct.pack('>H', i)

            crc_bitwise = SHT2X.crc8_msbf_bitwise(input)
            crc_math = SHT2X.crc8_msbf_math(input)
            self.assertEqual(crc_bitwise, crc_math)

            # check CRC `zero` magic as well
            self.assertEqual(SHT2X.crc8_msbf_bitwise(bytes((crc_bitwise,)), crc_bitwise), 0)
            self.assertEqual(SHT2X.crc8_msbf_math(bytes((crc_math,)), crc_math), 0)

    def test_crc_performance(self):
        """A CRC performance test. Bitwise is slower by factor ~3."""
        crc_result_target = 123

        t0 = time.time()
        result = 0
        for i in range(5000):
            result = SHT2X.crc8_msbf_math(bytes(range(256)), result)
        self.assertEqual(result, crc_result_target)
        tproc_math = time.time() - t0
        _log.info("crc8_msbf_math(): {:.3f}s".format(tproc_math))

        t0 = time.time()
        result = 0
        for i in range(5000):
            result = SHT2X.crc8_msbf_bitwise(bytes(range(256)), result)
        self.assertEqual(result, crc_result_target)
        tproc_bitwise = time.time() - t0
        _log.info("crc8_msbf_bitwise(): {:.3f}s".format(tproc_bitwise))

        # well, result depence on cpu utilisation. No that good ... but
        self.assertLess(tproc_math, tproc_bitwise)


if __name__ == '__main__':
    example()

    # because I forget it sometimes
    # run the example
    # >python3 -m module.sht2x

    # run the unittest
    # >python3 -m unittest module.sht2x


