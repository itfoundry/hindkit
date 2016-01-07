#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

__version__ = '1.0.0'

import os

def _unwrap_path_relative_to_package_dir(relative_path):
    return os.path.join(__path__[0], relative_path)

def _unwrap_path_relative_to_cwd(relative_path):
    return os.path.join(os.path.realpath(os.getcwdu()), relative_path)

from hindkit.objects import Family, Master, Style
from hindkit.tools import Builder
