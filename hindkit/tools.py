#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import subprocess, os, argparse, collections, shutil

import fontTools.ttLib, mutatorMath.ufo.document
import WriteFeaturesKernFDK, WriteFeaturesMarkFDK

import hindkit as kit

def sort_glyphs(glyph_order, glyph_names):
    sorted_glyphs = (
        [i for i in glyph_order if i in glyph_names] +
        [i for i in glyph_names if i not in glyph_order]
    )
    return sorted_glyphs

def compose_glyph_class_def_lines(class_name, glyph_names):
    if glyph_names:
        glyph_class_def_lines = (
            ['@{} = ['.format(class_name)] +
            ['  {}'.format(glyph_name) for glyph_name in glyph_names] +
            ['];', '']
        )
    else:
        glyph_class_def_lines = ['# @{} = [];'.format(class_name), '']
    return glyph_class_def_lines

def glyph_filter_marks(family, glyph):
    has_mark_anchor = False
    for anchor in glyph.anchors:
        if anchor.name:
            if anchor.name.startswith('_'):
                has_mark_anchor = True
                break
    return has_mark_anchor

# ---

def remove_files(path):
    subprocess.call(['rm', '-fR', path])

def make_dir(path):
    subprocess.call(['mkdir', '-p', path])

def reset_dir(path):
    remove_files(path)
    make_dir(path)

def copy(src, dst):
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy(src, src)

# ---

def overriding(abstract_path):
    return abstract_path

def temp(abstract_path):
    if abstract_path:
        temp_path = os.path.join(kit.constants.paths.TEMP, abstract_path)
    else:
        temp_path = None
    return temp_path
