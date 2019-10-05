#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CRC routine used by I2C sensor ICs.
"""

import logging
import struct
import time
import unittest
from typing import ByteString

_log = logging.getLogger(__name__)

class CRC8:
    @staticmethod
    def msbf_bitwise(data: ByteString, crc: int = 0, polynom: int = 0x131) -> int:
        """Calculates CRC checksum of data

        It's CRC8 most-significant-bit-first calculation.
        When `data` is inclusive CRC the result is 0. That's CRC magic.

        :param data: data bytes
        :param crc: initial crc value, normally 0
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
    def msbf_math_x131(data: ByteString, crc: int = 0) -> int:
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


class TestMethods(unittest.TestCase):
    """Very basic unittest"""
    def setUp(self):
        logging.basicConfig(level=logging.INFO)

    def test_crc_sht3x_datasheet(self):
        """SHT3x datasheet example"""
        self.assertEqual(CRC8.msbf_bitwise(b'\xBE\xEF', 0xFF), 0x92)
        self.assertEqual(CRC8.msbf_bitwise(b'\xBE\xEF\x92', 0xFF), 0)

    def test_crc(self):
        for crc_init in (0, 0xff):
            """Check all possible 2-byte streams."""
            for i in range(1 << 16):
                input = struct.pack('>H', i)

                crc_bitwise = CRC8.msbf_bitwise(input, crc_init)
                crc_math = CRC8.msbf_math_x131(input, crc_init)
                self.assertEqual(crc_bitwise, crc_math)

                # check CRC `zero` magic as well
                self.assertEqual(CRC8.msbf_bitwise(bytes((crc_bitwise,)), crc_bitwise), 0)
                self.assertEqual(CRC8.msbf_math_x131(bytes((crc_math,)), crc_math), 0)

    def test_crc_performance(self):
        """A CRC performance test. Bitwise is slower by factor ~3."""
        crc_result_target = 123

        t0 = time.time()
        result = 0
        for i in range(5000):
            result = CRC8.msbf_math_x131(bytes(range(256)), result)
        self.assertEqual(result, crc_result_target)
        tproc_math = time.time() - t0
        _log.info("msbf_math(): {:.3f}s".format(tproc_math))

        t0 = time.time()
        result = 0
        for i in range(5000):
            result = CRC8.msbf_bitwise(bytes(range(256)), result)
        self.assertEqual(result, crc_result_target)
        tproc_bitwise = time.time() - t0
        _log.info("msbf_bitwise(): {:.3f}s".format(tproc_bitwise))

        # well, result depense on cpu utilisation. No that good ... but
        self.assertLess(tproc_math, tproc_bitwise)
