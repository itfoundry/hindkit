#!/usr/bin/env AFDKOPython

from __future__ import division, absolute_import, print_function, unicode_literals

import os

__version__ = '1.0.0'

def _unwrap_path_relative_to_package_dir(relative_path):
    return os.path.join(__path__[0], relative_path)

def _unwrap_path_relative_to_cwd(relative_path):
    return os.path.join(os.path.realpath(os.getcwdu()), relative_path)
