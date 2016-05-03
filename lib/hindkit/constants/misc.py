#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, collections

import hindkit as kit

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

SCRIPTS = [
    kit.Script(
        name = 'Devanagari',
        abbreviation = 'dv',
        tags = ['dev2', 'deva'],
        is_indic = True,
        sample_text = 'सभी मनुष्यों को गौरव और अधिकारों के मामले में जन्मजात स्वतन्त्रता और समानता प्राप्त है।',
    ),
    kit.Script(
        name = 'Gujarati',
        abbreviation = 'gj',
        tags = ['gjr2', 'gujr'],
        is_indic = True,
        sample_text = 'પ્રતિષ્ઠા અને અધિકારોની દૃષ્ટિએ સર્વ માનવો જન્મથી સ્વતંત્ર અને સમાન હોય છે.',
    ),
    kit.Script(
        name = 'Gurmukhi',
        abbreviation = 'gr',
        tags = ['gur2', 'guru'],
        is_indic = True,
        sample_text = 'ਸਾਰਾ ਮਨੁੱਖੀ ਪਰਿਵਾਰ ਆਪਣੀ ਮਹਿਮਾ, ਸ਼ਾਨ ਅਤੇ ਹੱਕਾਂ ਦੇ ਪੱਖੋਂ ਜਨਮ ਤੋਂ ਹੀ ਆਜ਼ਾਦ ਹੈ ਅਤੇ ਸੁਤੇ ਸਿੱਧ ਸਾਰੇ ਲੋਕ ਬਰਾਬਰ ਹਨ।',
    ),
    kit.Script(
        name = 'Bangla',
        abbreviation = 'bn',
        tags = ['bng2', 'beng'],
        aliases = ['Bengali'],
        is_indic = True,
        sample_text = 'সমস্ত মানুষ স্বাধীনভাবে সমান মর্যাদা এবং অধিকার নিয়ে জন্মগ্রহণ করে।',
    ),
    kit.Script(
        name = 'Odia',
        abbreviation = 'od',
        tags = ['ory2', 'orya'],
        aliases = ['Oriya'],
        is_indic = True,
        sample_text = 'ସବୁ ମନୁଷ୍ଯ ଜନ୍ମକାଳରୁ ସ୍ବାଧୀନ. ସେମାନଙ୍କର ମର୍ଯ୍ଯାଦା ଓ ଅଧିକାର ସମାନ.',
    ),
    kit.Script(
        name = 'Telugu',
        abbreviation = 'tl',
        tags = ['tel2', 'telu'],
        is_indic = True,
        sample_text = 'ప్రతిపత్తిస్వత్వముల విషయమున మానవులెల్లరును జన్మతః స్వతంత్రులును సమానులును నగుదురు.',
    ),
    kit.Script(
        name = 'Kannada',
        abbreviation = 'kn',
        tags = ['knd2', 'knda'],
        is_indic = True,
        sample_text = 'ಎಲ್ಲಾ ಮಾನವರೂ ಸ್ವತಂತ್ರರಾಗಿಯೇ ಜನಿಸಿದ್ಧಾರೆ. ಹಾಗೂ ಘನತೆ ಮತ್ತು ಹಕ್ಕುಗಳಲ್ಲಿ ಸಮಾನರಾಗಿದ್ದಾರೆ.',
    ),
    kit.Script(
        name = 'Malayalam',
        abbreviation = 'ml',
        tags = ['mlm2', 'mlym'],
        is_indic = True,
        sample_text = 'മനുഷ്യരെല്ലാവരും തുല്യാവകാശങ്ങളോടും അന്തസ്സോടും സ്വാതന്ത്ര്യത്തോടുംകൂടി ജനിച്ചിട്ടുള്ളവരാണ്‌.',
    ),
    kit.Script(
        name = 'Tamil',
        abbreviation = 'tm',
        tags = ['tml2', 'taml'],
        is_indic = True,
        sample_text = 'மனிதப் பிறிவியினர் சகலரும் சுதந்திரமாகவே பிறக்கின்றனர்; அவர்கள் மதிப்பிலும், உரிமைகளிலும் சமமானவர்கள், அவர்கள் நியாயத்தையும் மனச்சாட்சியையும் இயற்பண்பாகப் பெற்றவர்கள்.',
    ),
    kit.Script(
        name = 'Sinhala',
        abbreviation = 'si',
        tags = ['sinh'],
        aliases = ['Sinhalese'],
        is_indic = True,
        sample_text = 'සියලු මනුෂ්‍යයෝ නිදහස්ව උපත ලබා ඇත. ගරුත්වයෙන් හා අයිතිවාසිකම්වලින් සමාන වෙති.',
    ),
    kit.Script(
        name = 'Ol Chiki',
        abbreviation = 'ol',
        tags = ['olck'],
    ),
    kit.Script(
        name = 'Arabic',
        abbreviation = 'ar',
        tags = ['arab'],
    ),
]

SCRIPT_NAMES_TO_SCRIPTS = {}
for script in SCRIPTS:
    SCRIPT_NAMES_TO_SCRIPTS[script.name] = script
    for alias in script.aliases:
        SCRIPT_NAMES_TO_SCRIPTS[alias] = script

@kit.memoize
def get_u_scalar_to_u_name():
    u_scalar_to_u_name = {}
    with open(kit.relative_to_package('data/UnicodeData.txt')) as f:
        for line in f:
            u_scalar, u_name, rest = line.split(';', 2)
            if not u_name.startswith('<'):
                u_scalar_to_u_name[u_scalar] = u_name
    return u_scalar_to_u_name

@kit.memoize
def get_glyph_list(filename):
    glyph_list = collections.OrderedDict()
    with open(kit.relative_to_package('data/' + filename)) as f:
        for line in f:
            line_without_comment = line.partition('#')[0].strip()
            if line_without_comment:
                u_scalar, glyph_name, u_name = line_without_comment.split(';')
                glyph_list[glyph_name] = u_name
    return glyph_list

@kit.memoize
def get_adobe_latin(number, get_combined=False):
    adobe_latin = collections.OrderedDict()
    suffix = str(number)
    if number > 3:
        suffix = suffix + ('-combined' if get_combined else '-precomposed')
    with open(
        kit.relative_to_package('data/adobe-latin-{}.txt'.format(suffix))
    ) as f:
        f.next()
        for line in f:
            parts = line.strip().split('\t')[:4]
            u_scalar, u_character, production_name, u_name = parts
            adobe_latin[production_name] = u_name
    return adobe_latin
