#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sensirion SHT3x humidity sensor I2C driver.

Drives SHT30, SHT31 and SHT35 humidity and temperature sensors.
Sensirion `SHT3x Datasheets <https://www.sensirion.com/en/environmental-sensors/humidity-sensors/humidity-temperature-sensor-sht3x-digital-i2c-accurate/>`
"""

import time
import collections
import struct
import logging
import unittest
from typing import Union, Optional, ByteString
from smbus2 import SMBus, i2c_msg


_log = logging.getLogger(__name__)


HML = collections.namedtuple('HML', ('high', 'medium', 'low'))

class Cmd(object):
    measure_single = HML(b'\x24\x00', b'\x24\x0B', b'\x24\x16')
    measure_sequence_0_5hz = HML(b'\x20\x32', b'\x20\x24', b'\x20\x2F')
    measure_sequence_1hz = HML(b'\x21\x30', b'\x21\x26', b'\x21\x2D')
    measure_sequence_2hz = HML(b'\x22\x36', b'\x22\x20', b'\x22\x2B')
    measure_sequence_4hz = HML(b'\x23\x34', b'\x23\x22', b'\x23\x29')
    measure_sequence_10hz = HML(b'\x27\x37', b'\x27\x21', b'\x27\x2A')
    measure_sequence_4hz_art = b'\x2B\x32'

    fetch_data = b'\xE0\x00'
    stop_sequence = b'\x30\x93'

    soft_reset = b'\x30\xA2'

    heater_enable = b'\x30\x6D'
    heater_disable = b'\x30\x66'

    read_status = b'\xF3\x2D'
    clear_status = b'\x30\x41'




class SHT3X(SMBus):
    """humidity-temperature sensors SHT30, SHT31 and SHT35."""
    def __init__(self, bus: Union[int, str] = 1, device_addr: int = 0x44) -> None:
        """Initialize

        :param bus: I2C bus identification number or a filesystem name like `/dev/i2c-something`
        :param device_addr: I2C device address, normally 0x44
        """
        SMBus.__init__(self, bus, force=True)
        self.crc8 = SHT3X.crc8_msbf_math  # CRC method to use

        self._temperature = None
        self._humidity = None

        self.device_addr = device_addr
        self._configure()

    def i2c_read_write(self, write: Union[int, ByteString], read: int = 0, rdelay: Optional[float] = None) -> Union[int, ByteString]:
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
        # just do a soft-reset
        self.soft_reset()
        self.status_clear()

    def soft_reset(self):
        """Soft reset"""
        self.i2c_read_write(Cmd.soft_reset, 0, 0.002)

    def update(self, repeatability: str = 'medium') -> None:
        """ update all measurement values
        :param repeatability: low, medium or high
        """
        settings = dict(
            high=(Cmd.measure_single.high, 6, 0.0155),
            medium=(Cmd.measure_single.medium, 6, 0.0065),
            low=(Cmd.measure_single.low, 6, 0.0045),
            )

        data = self.i2c_read_write(*settings[repeatability])
        if self.crc8(data[0:3]) == 0 and self.crc8(data[3:6]) == 0:
            self._temperature, self._humidity = struct.unpack('>HxHx', data)

    @property
    def centigrade(self) -> Optional[float]:
        """Celsius temperature

        :return: temperature or None on error
        """
        if self._temperature is not None:
            return -45.0 + (175.0 * self._temperature) / (2.0**16 - 1.0)

    @property
    def fahrenheit(self) -> Optional[float]:
        """Fahrenheit temperature measurment.

        :return: temperature or None on error
        """
        if self._temperature is not None:
            return -49.0 + (315.0 * self._temperature) / (2.0**16 - 1.0)

    @property
    def humidity(self) -> Optional[float]:
        """RH measurement (no hold master), blocking for max 32ms

        :return: relative humidity as % or None on error
        """
        if self._humidity is not None:
            rh = (100.0 * self._humidity) / (2.0**16 - 1.0)
            return max(0.0, min(rh, 100.0))

    @property
    def status(self):
        data = self.i2c_read_write(Cmd.read_status, 3)
        if self.crc8(data) == 0:
            return struct.unpack('>Hx', data)[0]

    def status_clear(self):
        self.i2c_read_write(Cmd.clear_status)

    @staticmethod
    def crc8_msbf_bitwise(data: ByteString, crc: int = 0xFF, polynom: int = 0x131) -> int:
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
    def crc8_msbf_math(data: ByteString, crc: int=0xFF) -> int:
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

    with SHT3X() as sensor:
        #~ print("Identification: 0x{:016X}".format(sensor.serial_number))

        for repeatablity in ('low', 'medium', 'high'):
            print("-" * 79)
            print("Repeatablity:   {}".format(repeatablity))
            sensor.update(repeatablity)
            print("Temperature:    {:.2f} C".format(sensor.centigrade))
            print("Temperature:    {:.2f} F".format(sensor.fahrenheit))
            print("Humidity:       {:.2f} % ".format(sensor.humidity))
            print("Status:         0x{:02X}".format(sensor.status))


class TestSHT3XMethods(unittest.TestCase):
    """Very basic unittest"""
    def setUp(self):
        logging.basicConfig(level=logging.INFO)

    def test_crc_sht3x_datasheet(self):
        """SHT3x datasheet example"""
        self.assertEqual(SHT3X.crc8_msbf_bitwise(b'\xBE\xEF'), 0x92)
        self.assertEqual(SHT3X.crc8_msbf_bitwise(b'\xBE\xEF\x92'), 0)

    def test_crc(self):
        """Check all possible 2-byte streams."""
        for i in range(1 << 16):
            input = struct.pack('>H', i)

            crc_bitwise = SHT3X.crc8_msbf_bitwise(input)
            crc_math = SHT3X.crc8_msbf_math(input)
            self.assertEqual(crc_bitwise, crc_math)

            # check CRC `zero` magic as well
            self.assertEqual(SHT3X.crc8_msbf_bitwise(bytes((crc_bitwise,)), crc_bitwise), 0)
            self.assertEqual(SHT3X.crc8_msbf_math(bytes((crc_math,)), crc_math), 0)

    @unittest.skip("just a CRC performance test")
    def test_crc_performance(self):
        """A CRC performance test. Bitwise is slower by factor ~3."""
        crc_result_target = 123

        t0 = time.time()
        result = 0
        for i in range(5000):
            result = SHT3X.crc8_msbf_math(bytes(range(256)), result)
        self.assertEqual(result, crc_result_target)
        tproc_math = time.time() - t0
        _log.info("crc8_msbf_math(): {:.3f}s".format(tproc_math))

        t0 = time.time()
        result = 0
        for i in range(5000):
            result = SHT3X.crc8_msbf_bitwise(bytes(range(256)), result)
        self.assertEqual(result, crc_result_target)
        tproc_bitwise = time.time() - t0
        _log.info("crc8_msbf_bitwise(): {:.3f}s".format(tproc_bitwise))

        # well, result depence on cpu utilisation. No that good ... but
        self.assertLess(tproc_math, tproc_bitwise)


if __name__ == '__main__':
    example()

    # because I forget it sometimes
    # run the example
    # >python3 -m module.sht3x

    # run the unittest
    # >python3 -m unittest module.sht3x


