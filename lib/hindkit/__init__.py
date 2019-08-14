#!/usr/bin/env AFDKOPython
# encoding: UTF-8


import os, sys, functools, shutil, errno

def relative_to_interpreter(path):
    return os.path.join(os.path.dirname(sys.executable), path)

def relative_to_package(path):
    return os.path.join(__path__[0], path)

def relative_to_cwd(path):
    return os.path.join(os.getcwd(), path)

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
        os.remove(path)
    except OSError:
        if not os.path.exists(path):
            pass
        elif os.path.isdir(path):
            try:
                shutil.rmtree(path)
            except OSError as e:
                if e.errno == errno.ENOTEMPTY:
                    shutil.rmtree(path)
                else:
                    raise
        else:
            raise

def makedirs(path):
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise

def copy(src, dst):
    remove(dst)
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy(src, dst)

def fallback(*candidates):
    for i in candidates:
        if i is not None:
            return i

def remove_illegal_chars_for_postscript_name_part(name):
    """
    Conforming The Compact Font Format Specification (version 1.0), section 7 "Name INDEX".
    Also removing "-".
    """
    return name.translate({
        ord(i): None for i in "[](){}<>/%\u0000\u0020\u0009\u000D\u000A\u000C-"
    })

from hindkit import constants
from hindkit import filters
from hindkit import patched

from hindkit.objects.base import BaseFile
from hindkit.objects.family import Family, DesignSpace, Fmndb
from hindkit.objects.font import Master, Style, Product
from hindkit.objects.glyphdata import GlyphData, Goadb
from hindkit.objects.client import Client
from hindkit.objects.feature import FeatureClasses, FeatureTables, FeatureLanguagesystems, FeatureGSUB, FeatureGPOS, FeatureKern, FeatureMark, FeatureOS2Extension, FeatureNameExtension, FeatureMatches, FeatureReferences
from hindkit.objects.project import Project
