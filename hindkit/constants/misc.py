#!/usr/bin/env AFDKOPython

from __future__ import division, absolute_import, print_function, unicode_literals

import os, collections
import hindkit

MARKS_CLASS_NAME = 'generated_marks'

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
        'sample text': 'सभी मनुष्यों को गौरव और अधिकारों के मामले में जन्मजात स्वतन्त्रता और समानता प्राप्त है।',
    },

    'bangla': {
        'abbreviation': 'bn',
        'indic1 tag': 'beng',
        'indic2 tag': 'bng2',
        'alternative name': 'Bengali',
        'sample text': 'সমস্ত মানুষ স্বাধীনভাবে সমান মর্যাদা এবং অধিকার নিয়ে জন্মগ্রহণ করে।',
    },

    'gurmukhi': {
        'abbreviation': 'gr',
        'indic1 tag': 'guru',
        'indic2 tag': 'gur2',
        'sample text': 'ਸਾਰਾ ਮਨੁੱਖੀ ਪਰਿਵਾਰ ਆਪਣੀ ਮਹਿਮਾ, ਸ਼ਾਨ ਅਤੇ ਹੱਕਾਂ ਦੇ ਪੱਖੋਂ ਜਨਮ ਤੋਂ ਹੀ ਆਜ਼ਾਦ ਹੈ ਅਤੇ ਸੁਤੇ ਸਿੱਧ ਸਾਰੇ ਲੋਕ ਬਰਾਬਰ ਹਨ।',
    },

    'gujarati': {
        'abbreviation': 'gj',
        'indic1 tag': 'gujr',
        'indic2 tag': 'gjr2',
        'sample text': 'પ્રતિષ્ઠા અને અધિકારોની દૃષ્ટિએ સર્વ માનવો જન્મથી સ્વતંત્ર અને સમાન હોય છે.',
    },

    'odia': {
        'abbreviation': 'od',
        'indic1 tag': 'orya',
        'indic2 tag': 'ory2',
        'alternative name': 'Oriya',
        'sample text': 'ସବୁ ମନୁଷ୍ଯ ଜନ୍ମକାଳରୁ ସ୍ବାଧୀନ. ସେମାନଙ୍କର ମର୍ଯ୍ଯାଦା ଓ ଅଧିକାର ସମାନ.',
    },

    'tamil': {
        'abbreviation': 'tm',
        'indic1 tag': 'taml',
        'indic2 tag': 'tml2',
        'sample text': 'மனிதப் பிறிவியினர் சகலரும் சுதந்திரமாகவே பிறக்கின்றனர்; அவர்கள் மதிப்பிலும், உரிமைகளிலும் சமமானவர்கள், அவர்கள் நியாயத்தையும் மனச்சாட்சியையும் இயற்பண்பாகப் பெற்றவர்கள்.',
    },

    'telugu': {
        'abbreviation': 'tl',
        'indic1 tag': 'telu',
        'indic2 tag': 'tel2',
        'sample text': 'ప్రతిపత్తిస్వత్వముల విషయమున మానవులెల్లరును జన్మతః స్వతంత్రులును సమానులును నగుదురు.',
    },

    'kannada': {
        'abbreviation': 'kn',
        'indic1 tag': 'knda',
        'indic2 tag': 'knd2',
        'sample text': 'ಎಲ್ಲಾ ಮಾನವರೂ ಸ್ವತಂತ್ರರಾಗಿಯೇ ಜನಿಸಿದ್ಧಾರೆ. ಹಾಗೂ ಘನತೆ ಮತ್ತು ಹಕ್ಕುಗಳಲ್ಲಿ ಸಮಾನರಾಗಿದ್ದಾರೆ.',
    },

    'malayalam': {
        'abbreviation': 'ml',
        'indic1 tag': 'mlym',
        'indic2 tag': 'mlm2',
        'sample text': 'മനുഷ്യരെല്ലാവരും തുല്യാവകാശങ്ങളോടും അന്തസ്സോടും സ്വാതന്ത്ര്യത്തോടുംകൂടി ജനിച്ചിട്ടുള്ളവരാണ്‌.',
    },

    'sinhala': {
        'abbreviation': 'si',
        'tag': 'sinh',
        'sample text': 'සියලු මනුෂ්‍යයෝ නිදහස්ව උපත ලබා ඇත. ගරුත්වයෙන් හා අයිතිවාසිකම්වලින් සමාන වෙති.',
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
