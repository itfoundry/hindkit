#!/usr/bin/env AFDKOPython

from __future__ import division, absolute_import, print_function, unicode_literals

import os
import hindkit

def memoize(f):
    memo = {}
    def decorator():
        if f not in memo:
            memo[f] = f()
        return memo[f]
    return decorator

@memoize
def get_scalar_to_name_map():
    scalar_to_name_map = {}
    with open(hindkit._unwrap_path_relative_to_package_dir('constants/UnicodeData.txt')) as f:
        for line in f:
            scalar, name, rest = line.split(';', 2)
            scalar_to_name_map[scalar] = name
    return scalar_to_name_map
