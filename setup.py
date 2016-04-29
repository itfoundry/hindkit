#!/usr/bin/env AFDKOPython

import setuptools

setuptools.setup(
    name = 'hindkit',
    version = '1.0.0',
    url = "https://github.com/itfoundry/hindkit",
    author = 'Liang Hai',
    author_email = 'lianghai@gmail.com',
    license='MIT',
    packages = [
        'hindkit',
        'hindkit.constants',
        'hindkit.objects',
    ],
    py_modules = ['sstruct', 'xmlWriter'],
    package_data = {
        'hindkit': ['data/*'],
    },
)
