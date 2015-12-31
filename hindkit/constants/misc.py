#!/usr/bin/env AFDKOPython

from __future__ import division, absolute_import, print_function, unicode_literals

import os, collections
import hindkit

DEFAULT_CLIENT = 'googlefonts'

from . import styles
CLIENTS = {
    'itf': {
        'style_scheme': styles.STANDARD,
    },
    'googlefonts': {
        'style_scheme': styles.STANDARD_CamelCase,
    },
}

DERIVING_MAP = {
    'CR': 'space',
    'uni00A0': 'space',
    'NULL': None,
    'uni200B': None,
}

CONSONANT_STEMS = '''
K KH G GH NG
C CH J JH NY
TT TTH DD DDH NN
T TH D DH N
P PH B BH M
Y R L V
SH SS S H
TTT NNN YY RR RRR LL LLL
TS DZ W ZH
'''.split()

VOWEL_STEMS = '''
AA I II U UU vR vRR vL vLL
E EE AI O OO AU
'''.split()

INDIC_SCRIPTS = {

    'devanagari': {
        'abbreviation': 'dv',
        'indic1 tag': 'deva',
        'indic2 tag': 'dev2',
    },

    'bangla': {
        'abbreviation': 'bn',
        'indic1 tag': 'beng',
        'indic2 tag': 'bng2',
        'alternative name': 'Bengali',
    },

    'gurmukhi': {
        'abbreviation': 'gr',
        'indic1 tag': 'guru',
        'indic2 tag': 'gur2',
    },

    'gujarati': {
        'abbreviation': 'gj',
        'indic1 tag': 'gujr',
        'indic2 tag': 'gjr2',
    },

    'odia': {
        'abbreviation': 'od',
        'indic1 tag': 'orya',
        'indic2 tag': 'ory2',
        'alternative name': 'Oriya',
    },

    'tamil': {
        'abbreviation': 'tm',
        'indic1 tag': 'taml',
        'indic2 tag': 'tml2',
    },

    'telugu': {
        'abbreviation': 'tl',
        'indic1 tag': 'telu',
        'indic2 tag': 'tel2',
    },

    'kannada': {
        'abbreviation': 'kn',
        'indic1 tag': 'knda',
        'indic2 tag': 'knd2',
    },

    'malayalam': {
        'abbreviation': 'ml',
        'indic1 tag': 'mlym',
        'indic2 tag': 'mlm2',
    },

    'sinhala': {
        'abbreviation': 'si',
        'tag': 'sinh',
    },
}

def memoize(f):
    memo = {}
    def decorator():
        if f not in memo:
            memo[f] = f()
        return memo[f]
    return decorator

@memoize
def get_unicode_scalar_to_unicode_name_map():
    scalar_to_name_map = {}
    with open(hindkit._unwrap_path_relative_to_package_dir('resources/UnicodeData.txt')) as f:
        for line in f:
            scalar, name, rest = line.split(';', 2)
            scalar_to_name_map[scalar] = name
    return scalar_to_name_map

@memoize
def get_aglfn():
    aglfn = collections.OrderedDict()
    with open(hindkit._unwrap_path_relative_to_package_dir('resources/aglfn.txt')) as f:
        for line in f.read().splitlines():
            if not line.startswith('#'):
                unicode_scalar, glyph_name, unicode_name = line.split(';')
                aglfn[glyph_name] = (unicode_scalar, unicode_name)
