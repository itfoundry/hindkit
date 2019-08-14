#!/usr/bin/env AFDKOPython
# encoding: UTF-8


import os, collections

import hindkit as kit

DERIVABLE_GLYPHS = {
    None: ["NULL", ".null", "zerowidthspace", "uni200B"],
    "space": ["CR", "nonmarkingreturn", "uni000D", "nonbreakingspace", "uni00A0"],
    "hyphen": ["softhyphen"],
    "slash": ["divisionslash"],
    "periodcentered": ["bulletoperator"],
    "macron": ["macronmod"],
    "quoteright": ["apostrophemod"],
}

REQUIRED_GLYPHS = [
    [".notdef"],
    ["NULL", "CR"],
    ["zerowidthnonjoiner", "zerowidthjoiner", "dottedcircle"],
    ["zerowidthspace"],
]

STYLES_SINGLE = [
    ("Regular", 0, 400),
]

STYLES_DUAL = [
    ("Regular", 0, 400),
    ("Bold",  100, 700),
]

STYLES_ITF = [
    ("Light",     0, 300),
    ("Regular",  21, 400),
    ("Medium",   44, 500),
    ("Semibold", 70, 600),
    ("Bold",    100, 700),
]

STYLES_ITF_CamelCase = [
    ("Light",     0, 300),
    ("Regular",  21, 400),
    ("Medium",   44, 500),
    ("SemiBold", 70, 600),
    ("Bold",    100, 700),
]

CONSONANT_STEMS = """
K KH G GH NG
C CH J JH NY
TT TTH DD DDH NN
T TH D DH N
P PH B BH M
Y R L V
SH SS S H
TTT NNN YY RR RRR LL LLL
TS DZ W ZH
""".split()

ALPHABET_GURMUKHI = """
Ura Ara Iri S H
K KH G GH NG
C CH J JH NY
TT TTH DD DDH NN
T TH D DH N
P PH B BH M
Y R L V RR
""".split()

VOWEL_STEMS = """
AA I II U UU vR vRR vL vLL
E EE AI O OO AU
""".split()

class Script(object):
    def __init__(
        self,
        name,
        abbr,
        tags,
        aliases = None,
        sample_text = None,
        is_indic = False,
        unicode_range_bits = None,
    ):
        self.name = name
        self.abbr = abbr
        self.tags = tags
        self.aliases = kit.fallback(aliases, [])
        self.sample_text = sample_text
        self.is_indic = is_indic
        self.unicode_range_bits = kit.fallback(unicode_range_bits, [])

SCRIPTS = [
    Script(
        name = "Latin",
        abbr = "lt",
        tags = ["latn"],
        unicode_range_bits = [0],
    ),
    Script(
        name = "Devanagari",
        abbr = "dv",
        tags = ["deva", "dev2"],
        is_indic = True,
        sample_text = "सभी मनुष्यों को गौरव और अधिकारों के मामले में जन्मजात स्वतन्त्रता और समानता प्राप्त है।",
        unicode_range_bits = [15],
    ),
    Script(
        name = "Gujarati",
        abbr = "gj",
        tags = ["gujr", "gjr2"],
        is_indic = True,
        sample_text = "પ્રતિષ્ઠા અને અધિકારોની દૃષ્ટિએ સર્વ માનવો જન્મથી સ્વતંત્ર અને સમાન હોય છે.",
        unicode_range_bits = [18],
    ),
    Script(
        name = "Gurmukhi",
        abbr = "gr",
        tags = ["guru", "gur2"],
        is_indic = True,
        sample_text = "ਸਾਰਾ ਮਨੁੱਖੀ ਪਰਿਵਾਰ ਆਪਣੀ ਮਹਿਮਾ, ਸ਼ਾਨ ਅਤੇ ਹੱਕਾਂ ਦੇ ਪੱਖੋਂ ਜਨਮ ਤੋਂ ਹੀ ਆਜ਼ਾਦ ਹੈ ਅਤੇ ਸੁਤੇ ਸਿੱਧ ਸਾਰੇ ਲੋਕ ਬਰਾਬਰ ਹਨ।",
        unicode_range_bits = [17],
    ),
    Script(
        name = "Bangla",
        abbr = "bn",
        tags = ["beng", "bng2"],
        aliases = ["Bengali"],
        is_indic = True,
        sample_text = "সমস্ত মানুষ স্বাধীনভাবে সমান মর্যাদা এবং অধিকার নিয়ে জন্মগ্রহণ করে।",
        unicode_range_bits = [16],
    ),
    Script(
        name = "Odia",
        abbr = "od",
        tags = ["orya", "ory2"],
        aliases = ["Oriya"],
        is_indic = True,
        sample_text = "ସବୁ ମନୁଷ୍ଯ ଜନ୍ମକାଳରୁ ସ୍ବାଧୀନ. ସେମାନଙ୍କର ମର୍ଯ୍ଯାଦା ଓ ଅଧିକାର ସମାନ.",
        unicode_range_bits = [19],
    ),
    Script(
        name = "Telugu",
        abbr = "tl",
        tags = ["telu", "tel2"],
        is_indic = True,
        sample_text = "ప్రతిపత్తిస్వత్వముల విషయమున మానవులెల్లరును జన్మతః స్వతంత్రులును సమానులును నగుదురు.",
        unicode_range_bits = [21],
    ),
    Script(
        name = "Kannada",
        abbr = "kn",
        tags = ["knda", "knd2"],
        is_indic = True,
        sample_text = "ಎಲ್ಲಾ ಮಾನವರೂ ಸ್ವತಂತ್ರರಾಗಿಯೇ ಜನಿಸಿದ್ಧಾರೆ. ಹಾಗೂ ಘನತೆ ಮತ್ತು ಹಕ್ಕುಗಳಲ್ಲಿ ಸಮಾನರಾಗಿದ್ದಾರೆ.",
        unicode_range_bits = [22],
    ),
    Script(
        name = "Malayalam",
        abbr = "ml",
        tags = ["mlym", "mlm2"],
        is_indic = True,
        sample_text = "മനുഷ്യരെല്ലാവരും തുല്യാവകാശങ്ങളോടും അന്തസ്സോടും സ്വാതന്ത്ര്യത്തോടുംകൂടി ജനിച്ചിട്ടുള്ളവരാണ്‌.",
        unicode_range_bits = [23],
    ),
    Script(
        name = "Tamil",
        abbr = "tm",
        tags = ["taml", "tml2"],
        is_indic = True,
        sample_text = "மனிதப் பிறிவியினர் சகலரும் சுதந்திரமாகவே பிறக்கின்றனர்; அவர்கள் மதிப்பிலும், உரிமைகளிலும் சமமானவர்கள், அவர்கள் நியாயத்தையும் மனச்சாட்சியையும் இயற்பண்பாகப் பெற்றவர்கள்.",
        unicode_range_bits = [20],
    ),
    Script(
        name = "Sinhala",
        abbr = "si",
        tags = ["sinh"],
        aliases = ["Sinhalese"],
        is_indic = True,
        sample_text = "සියලු මනුෂ්‍යයෝ නිදහස්ව උපත ලබා ඇත. ගරුත්වයෙන් හා අයිතිවාසිකම්වලින් සමාන වෙති.",
        unicode_range_bits = [73],
    ),
    Script(
        name = "Ol Chiki",
        abbr = "ol",
        tags = ["olck"],
        unicode_range_bits = [114],
    ),
    Script(
        name = "Arabic",
        abbr = "ar",
        tags = ["arab"],
        unicode_range_bits = [13, 63, 67],
    ),
    Script(
        name = "Hebrew",
        abbr = "hb",
        tags = ["hebr"],
        unicode_range_bits = [11],
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
    with open(kit.relative_to_package("data/UnicodeData.txt")) as f:
        for line in f:
            u_scalar, u_name, rest = line.split(";", 2)
            if not u_name.startswith("<"):
                u_scalar_to_u_name[u_scalar] = u_name
    return u_scalar_to_u_name

@kit.memoize
def get_glyph_list(filename, with_u_scalar=False):
    glyph_list = collections.OrderedDict()
    with open(kit.relative_to_package("data/" + filename)) as f:
        for line in f:
            line_without_comment = line.partition("#")[0].strip()
            if line_without_comment:
                u_scalar, glyph_name, u_name = line_without_comment.split(";")
                if with_u_scalar:
                    glyph_list[glyph_name] = (u_scalar, u_name)
                else:
                    glyph_list[glyph_name] = u_name
    return glyph_list

@kit.memoize
def get_adobe_latin(number, get_combined=False):
    adobe_latin = collections.OrderedDict()
    suffix = str(number)
    if number > 3:
        suffix = suffix + ("-combined" if get_combined else "-precomposed")
    with open(
        kit.relative_to_package("data/adobe-latin-{}.txt".format(suffix))
    ) as f:
        f.next()
        for line in f:
            parts = line.strip().split("\t")[:4]
            u_scalar, u_character, production_name, u_name = parts
            adobe_latin[production_name] = u_scalar
    return adobe_latin

ITF_GENERAL = "exclam quotedbl numbersign dollar percent ampersand quotesingle parenleft parenright asterisk plus comma hyphen period slash zero one two three four five six seven eight nine colon semicolon less equal greater question at bracketleft backslash bracketright asciicircum underscore grave braceleft bar braceright asciitilde cent sterling yen copyright guillemotleft registered degree periodcentered guillemotright endash emdash quoteleft quoteright quotedblleft quotedblright dagger daggerdbl bullet ellipsis guilsinglleft guilsinglright Euro trademark".split()

ITF_GENERAL_DEVELOPMENT = [
    {"guillemotleft": "guillemetleft", "guillemotright": "guillemetright"}.get(i, i)
    for i in ITF_GENERAL
]
