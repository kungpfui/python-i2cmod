#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from distutils.core import setup
from setuptools.command.install import install as _install

_package = 'i2cmod'


LONG_DESCRIPTION = """
"""

setup(name=_package,
    version='0.0.1',
    author='Stefan Schwendeler',
    author_email='kungpfui@users.noreply.github.com',
    url='https://github.com/kungpfui/python-i2cmod',
    description='A collection of I2C sensor module drivers',
    long_description=LONG_DESCRIPTION,
    license='MIT',

    install_requires = [
        'smbus2',
        ],

    packages=[_package],

    )
