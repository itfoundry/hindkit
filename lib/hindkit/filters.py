#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import hindkit as kit

def glyph_filter_matra_i_alts(family, glyph):
    match = re.match(
        family.script.abbreviation + MATRA_I_NAME_STEM + r'\d\d$',
        glyph.name,
    )
    return bool(match)

def glyph_filter_bases_for_matra_i(family, glyph):
    return glyph_filter_bases_alive(family, glyph)

def get_end(family, glyph):
    name = glyph.name
    end = ''
    if name.startswith(family.script.abbreviation):
        main, sep, suffix = name[2:].partition('.')
        end = main.split('_')[-1]
        if end.endswith('xA'):
            end = end[:-2] + 'A'
        elif end.endswith('x'):
            end = end[:-1]
    return end

def glyph_filter_bases_alive(family, glyph):
    return get_end(family, glyph) in ALIVE_CONSONANTS

def glyph_filter_bases_dead(family, glyph):
    return get_end(family, glyph) in DEAD_CONSONANTS

POTENTIAL_BASES_FOR_WIDE_MATRA_II = '''
KA PHA KxA PHxA K_RA PH_RA Kx_RA PHx_RA
J_KA K_KA K_PHA Kx_KxA Kx_PHA Kx_PHxA L_KA L_PHA
N_KA N_PHA N_PH_RA PH_PHA PHx_PHxA P_PHA SH_KA SH_KxA
SS_KA SS_K_RA SS_PHA S_KA S_K_RA S_PHA T_KA T_K_RA T_PHA
K_TA.traditional
'''.split()

def glyph_filter_bases_for_wide_matra_ii(family, glyph):
    name = glyph.name
    if name.startswith(
        kit.constants.SCRIPT_NAMES_TO_SCRIPTS['Devanagari'].abbreviation
    ):
        name = name[2:]
    return name in POTENTIAL_BASES_FOR_WIDE_MATRA_II
