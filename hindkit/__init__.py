#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, sys, functools, shutil, errno

def relative_to_interpreter(path):
    return os.path.join(os.path.dirname(sys.executable), path)

def relative_to_package(path):
    return os.path.join(__path__[0], path)

def relative_to_cwd(path):
    return os.path.join(os.getcwdu(), path)

def memoize(obj):
    memoized = {}
    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        k = str(args) + str(kwargs)
        if k not in memoized:
            memoized[k] = obj(*args, **kwargs)
        return memoized[k]
    return memoizer

def remove(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except OSError as e:
        if e.errno == errno.ENOENT:
            pass
        else:
            raise


def makedirs(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def copy(src, dst):
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy(src, src)

from hindkit.constants import styles, clients, misc
from hindkit.objects.base import BaseObject
from hindkit.objects.family import Family
from hindkit.objects.font import Master, Style, Product
from hindkit.objects.glyphdata import GlyphData
from hindkit.objects.builder import Builder

from hindkit import scripts
