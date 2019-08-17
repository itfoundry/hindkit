import hindkit as k
import functools

ODIA_STEMS = "K KH G GH NG C CH J JH NY TT TTH DD DDH NN T TH D DH N P PH B V BH M Y YY R LL L SH SS S H W".split()

STEMS = k.constants.CONSONANT_STEMS
# STEMS = ODIA_STEMS
STEMS_AKHAND = ["K_SS", "J_NY"]
ORDER = []
for stem in STEMS + STEMS_AKHAND:
    for i in ["A", "", "Ac2"]:
        part = stem + i
        ORDER.append(part)
        if part == "R":
            ORDER.append("Eyelash")

def get_name(rule):
    return rule.split()[-1][:-1]

def get_key(name, akhands=None, reverse=False):
    if akhands is None:
        akhands = []
    main = name[2:]
    main = main.replace("_", " ")
    for akhand in akhands:
        main = main.replace(akhand.replace("_", " "), akhand)
    parts = main.split(" ")
    key_major = []
    key_minor = []
    for part in parts:
        key_major.append(ORDER.index(part.replace("x", "")))
        key_minor.append("x" in part)
    key_minor.reverse()
    if reverse:
        key_major.reverse()
        key_minor.reverse()
    key = [key_major, key_minor]
    return key

RULES = """\
sub mlKA mlVirama mlKA by mlK_KA;
""".splitlines()
NAMES = """\
mlK_KA
""".splitlines()

with open("lab/input.txt") as f:
    names = f.read().splitlines()
names.sort(
    key = functools.partial(
        get_key,
        # akhands = STEMS_AKHAND,
        # reverse = True,
    ),
)
with open("lab/output.txt", "w") as f:
    f.write("\n".join(names))
