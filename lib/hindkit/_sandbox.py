#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import collections

consonant_name_sequences = [
    'K KA',
    'G GA',
]

glyph_name_sequences = [
    'K_KA',
    'G GA',
]

class Glyph(object):
    def __init__(self, font, name):
        self.font = font
        self.name = name
        self.object = font[name]
        self.alive = is_alive(self.name)
        self.width = self.object.width
        self.abvm_position = get_stem_position(glyph, style.abvm_right_margin)

for glyph_name_sequence in glyph_name_sequences:

    glyph_sequence = [
        Glyph(font, name) for glyph_name in glyph_name_sequence.split()
    ]

    position_base = 0
    for glyph in glyph_sequence:
        if glyph.alive:
            position_base += glyph.abvm_position
        else:
            position_base += glyph.width
