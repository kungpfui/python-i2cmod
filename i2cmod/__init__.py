#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A collection of I2C connected sensor ICs
"""

__version__ = '0.0.1'

# humidity / temperature
from .sht2x import SHT2X
from .sht3x import SHT3X

# pressure / temperature
from .bmp280 import BMP280
# pressure / temperature / humidity
from .bme280 import BME280

# daylight sensors
from .max44009 import MAX44009
from .veml6040 import VEML6040

# uv sensors
from .veml6075 import VEML6075

# displays
from .ssd1306 import SSD1306


