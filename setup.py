#!/usr/bin/env AFDKOPython

import setuptools
import hindkit

setuptools.setup(
    name = 'hindkit',
    version = hindkit.__version__,
    author = 'Liang Hai',
    author_email = 'lianghai@gmail.com',
    packages = ['hindkit', 'hindkit.constants'],
)
