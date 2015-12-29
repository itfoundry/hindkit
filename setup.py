#!/usr/bin/env python

import setuptools
import hindkit as kit

setuptools.setup(
    name = 'hindkit',
    version = kit.__version__,
    author = 'Liang Hai',
    author_email = 'lianghai@gmail.com',
    packages = ['hindkit', 'hindkit.constants', 'hindkit.AFDKOPython'],
)
