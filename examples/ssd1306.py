#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Solomon Systech SSD1306: OLED display controller
"""

import time
from i2cmod import SSD1306


def example():
    """ Output data to screen"""
    with SSD1306(font_size=24) as display:
        display.clear()

        # center on display
        msg = 'Hello World!'
        x, y = display.draw.textsize(msg, font=display.font)
        display.draw.text(((display.width - x) // 2, (display.height - y) // 2), msg, font=display.font, fill=255)

        display.update()

        # test contrast function
        for ct in range(0, 256, 32):
            display.contrast = ct
            time.sleep(0.5)


if __name__ == '__main__':
    example()

