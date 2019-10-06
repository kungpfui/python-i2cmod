#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Solomon Systech SSD1306: OLED display controller
"""
import os
import enum
from typing import Iterable
from smbus2 import SMBus
from PIL import Image, ImageDraw, ImageFont


# i2c registers
class Reg(enum.IntEnum):
    # fundamental commands
    contrast            = 0x81  # range(0, 256), default 0x7F
    displayallon_resume = 0xa4
    displayallon        = 0xa5
    normal_display      = 0xa6
    invert_display      = 0xa7
    display_off         = 0xae
    display_on          = 0xaf

    # scrolling commands
    cont_right_horizontal_scroll              = 0x26
    cont_left_horizontal_scroll               = 0x27
    cont_vertical_and_right_horizontal_scroll = 0x29
    cont_vertical_and_left_horizontal_scroll  = 0x2a
    deactivate_scroll                         = 0x2e
    activate_scroll                           = 0x2f
    vertical_scroll_area                      = 0xA3

    # addressing setting commands
    low_column          = 0x00  # 00 - 0F
    high_column         = 0x10  # 10 - 1F
    memory_addr_mode    = 0x20  # 0 = horizontal, 1 = vertical, 2 = page address (default)
    column_addr         = 0x21
    page_addr           = 0x22
    page_start_addr     = 0xB0  # B0 - B7

    # Hardware Configuration (Panel resolution & layout related) Commands
    start_line          = 0x40   # range(40, 80)
    segment_remap       = 0xA0
    multiplex_ratio     = 0xA8   # range(15, 64), default 63 => heigth of display minus 1
    com_out_scandir_inc = 0xC0   # range(0, 64), default 0
    com_out_scandir_dec = 0xC8
    display_offset      = 0xD3
    com_pins            = 0xDA

    # Timing & Driving Scheme Setting Commands
    clock_div_ratio_osc_freq  = 0xD5   # default 0x80
    precharge_period          = 0xD9   # default 0x22
    vcomh_deselect_level      = 0xDB   # default 0x20 = 0.77 x Vcc
    nop                       = 0xE3   # no operation

    # Charge Pump Command
    charge_pump          = 0x8D  # 0x10 disable, 0x14 enable


class SSD1306(SMBus):
    """
    """
    def __init__(self, bus: int = 1, device_addr: int = 0x3c, font_size:int = 16, contrast: int = 0x7F):
        """
        :param bus:         I2C bus identfier
        :param device_addr: I2C device address
        :param font_size:
        :param contrast:
        """
        SMBus.__init__(self, bus, force=True)
        self.device_addr = device_addr

        self.width = 128
        self.height = 32

        # display controller specific stuff
        self._pages = self.height // 8
        self.buffer = bytearray(self.width * self._pages)

        # PIL objects
        self.image = Image.new('1', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        self.set_font(os.path.join(os.path.abspath(os.path.dirname(__file__)), "fonts/isocpeur.ttf"), font_size)
        # isocpeur.ttf looks betters than the default font of PIL
        # self.font = ImageFont.load_default()

        self._contrast = contrast

        self._configure()
        self.update(0) # clean

    def set_font(self, font, size) -> None:
        self.font = ImageFont.truetype(font, size)

    def _configure(self, charge_pump: bool = True) -> None:
        self.command(Reg.display_off)
        self.command(Reg.clock_div_ratio_osc_freq, 0x80)   # the suggested ratio 0x80
        self.command(Reg.multiplex_ratio, self.height - 1)
        self.command(Reg.display_offset, 0)
        self.command(Reg.start_line + 0)
        self.command(Reg.charge_pump, 0x14 if charge_pump else 0x10)
        self.command(Reg.memory_addr_mode, 0)  # 0 means: act like ks0108
        self.command(Reg.segment_remap + 1)
        self.command(Reg.com_out_scandir_dec)
        self.command(Reg.com_pins, 2)
        self.contrast = self._contrast
        self.command(Reg.precharge_period, 0xF2 if charge_pump else 0x22)
        self.command(Reg.vcomh_deselect_level, 0x40)
        self.command(Reg.displayallon_resume)
        self.command(Reg.normal_display)
        self.command(Reg.display_on)

    def write_i2c_block_data(self, register: int, data: Iterable) -> None:
        """ allows additional parameter types

        :param register: register address/command
        :param data: data to write
        """
        if isinstance(data, int):
            data = bytes(data,)
        elif not isinstance(data, bytes):
            data = bytes(data)
        SMBus.write_i2c_block_data(self, self.device_addr, register, data)

    def command(self, *data) -> None:
        """short-cut for command register 0."""
        self.write_i2c_block_data(0x00, data)

    @property
    def contrast(self) -> int:
        """last used contrast value"""
        return self._contrast

    @contrast.setter
    def contrast(self, value: int):
        """
        Sets the contrast of the display.
        Contrast should be a value between 0 and 255.
        """
        assert 0 <= value <= 255
        self._contrast = value
        self.command(Reg.contrast, self._contrast)

    def clear(self) -> None:
        # Draw a black filled box to clear the image.
        self.draw.rectangle((0, 0) + self.image.size, outline=0, fill=0)

    def update(self, buffer=None) -> None:
        """Write display buffer to physical display.
        :param buffer:  None: buffer is filled by PIL object `self.image`
                       0: cleared buffer is used
                       bytearray, list, tuple: use that data
        """
        if buffer is None:
            self._update_from_image()
            return

        if isinstance(buffer, int) and buffer == 0:
            buffer = bytearray(self.width * self._pages)  # all zeros

        # Column start address. (0 = reset), Column end address.
        self.command(Reg.column_addr, 0, self.width - 1)
        # Page start address. (0 = reset)
        # Page end address.
        self.command(Reg.page_addr, 0, self._pages - 1)

        # Write buffer data.
        for i in range(0, len(buffer), 16):
            self.write_i2c_block_data(0x40, buffer[i:i + 16])

    def _update_from_image(self) -> None:
        """Set buffer to value of PIL image.  The image should
        be in 1 bit mode and a size equal to the display size.
        """
        idx = 0
        bits = tuple(range(8))
        buffer = bytearray(self.width * self._pages)

        # Grab all the pixels from the image, faster than getpixel.
        pix = self.image.load()

        # Iterate through the memory pages
        for page in range(self._pages):
            # Iterate through all x axis columns.
            for x in range(self.width):
                # Set the bits for the column of pixels at the current position.
                bv = 0
                for bit in bits:
                    bv |= bool(pix[x, page * 8 + bit]) << bit
                buffer[idx] = bv
                idx += 1

        self.update(buffer)
