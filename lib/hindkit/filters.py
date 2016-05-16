#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import re
import hindkit as kit

def marks(family, glyph):
    has_mark_anchor = False
    for anchor in glyph.anchors:
        if anchor.name:
            if anchor.name.startswith('_'):
                has_mark_anchor = True
                break
    return has_mark_anchor

def mI_variants(family, glyph):
    match = re.match(
        family.script.abbr + kit.FeatureMatches.mI_NAME_STEM + r'\d\d$',
        glyph.name,
    )
    return bool(match)

def get_end(family, glyph):
    name = glyph.name
    end = ''
    if name.startswith(family.script.abbr):
        main, sep, suffix = name[2:].partition('.')
        end = main.split('_')[-1]
        if end.endswith('xA'):
            end = end[:-2] + 'A'
        elif end.endswith('x'):
            end = end[:-1]
    return end

def bases_alive(family, glyph):
    return get_end(family, glyph) in kit.FeatureMatches.CONSONANTS_ALIVE

def bases_dead(family, glyph):
    return get_end(family, glyph) in kit.FeatureMatches.CONSONANTS_DEAD

POTENTIAL_BASES_FOR_LONG_mII = '''
KA PHA KxA PHxA K_RA PH_RA Kx_RA PHx_RA
J_KA K_KA K_PHA Kx_KxA Kx_PHA Kx_PHxA L_KA L_PHA
N_KA N_PHA N_PH_RA PH_PHA PHx_PHxA P_PHA SH_KA SH_KxA
SS_KA SS_K_RA SS_PHA S_KA S_K_RA S_PHA T_KA T_K_RA T_PHA
K_TA.traditional
'''.split()

def bases_for_long_mII(family, glyph):
    name = glyph.name
    if name.startswith(
        kit.constants.SCRIPT_NAMES_TO_SCRIPTS['Devanagari'].abbr
    ):
        name = name[2:]
    return name in POTENTIAL_BASES_FOR_LONG_mII
