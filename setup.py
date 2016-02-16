#!/usr/bin/env AFDKOPython

import setuptools

setuptools.setup(
    name = 'hindkit',
    version = '1.0.0',
    author = 'Liang Hai',
    author_email = 'lianghai@gmail.com',
    url = "https://github.com/itfoundry/hindkit",
    packages = [
        'hindkit',
        'hindkit.constants',
    ],
    package_data = {
        'hindkit': ['data/*'],
    },
)
