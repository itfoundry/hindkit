#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import collections

consonant_name_sequences = [
    'K KA',
    'G GA',
]

base_name_sequences = [
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
        self.abvm_position = get_stem_position(
            self.object, style.abvm_right_margin
        )

mI_table = []
matches_too_long = []

for base_name_sequence in base_name_sequences:

    base = [
        Glyph(font, name) for base_name in base_name_sequence.split()
    ]

    base.position = 0
    for glyph in base:
        if base.alive:
            base.position += glyph.abvm_position
        else:
            base.position += glyph.width

    if base.position <= mI_table[0].position:
        decision = mI_table[0]
    elif base.position < mI_table[-1].position:
        i = 0
        while mI_table[i].position < base.position:
            mI_short = mI_table[i]
            i += 1
        mI_enough = mI_table[i]
        if (
            abs(mI_enough.position - base.position) <=
            abs(mI_short.position - base.position)
        ):
            decision = mI_enough
        else:
            decision = mI_short
    elif base.position <= mI_table[-1].position + tolerance:
        decision = mI_table[-1]
    else:
        decision = matches_too_long

    decision.matches.append(base)
