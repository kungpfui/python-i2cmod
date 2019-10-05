#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vishay VEML6075: UV-A/B radiation sensor.
"""

from i2cmod import VEML6075


def example():
    # Output data to screen
    with VEML6075() as uv_sensor:
        print('ID:          {:04X}'.format(uv_sensor.id))

        uv_sensor.update()
        print('UV-A:        {}'.format(uv_sensor.uva))
        print('UV-B:        {}'.format(uv_sensor.uvb))
        print('UVcomp1:     {}'.format(uv_sensor.uvcomp1))
        print('UVcomp2:     {}'.format(uv_sensor.uvcomp2))

        print('UV-A W/m^2:  {:.3f}'.format(uv_sensor.uva_intensity))
        print('UV-B W/m^2:  {:.3f}'.format(uv_sensor.uvb_intensity))

        print('UV-A Index:  {:.3f}'.format(uv_sensor.uva_index))
        print('UV-B Index:  {:.3f}'.format(uv_sensor.uvb_index))
        print('UV Index:    {:.3f}'.format(uv_sensor.uv_index))


if __name__ == '__main__':
    example()
