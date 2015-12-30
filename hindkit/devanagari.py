from __future__ import division, absolute_import, print_function, unicode_literals

import re, collections
import hindkit as kit

SCRIPT_PREFIX = 'dv'
MATRA_I_NAME_STEM = 'mI.alt'
MATRA_I_ANCHOR_NAME = 'abvm.i'

STEM_ANCHOR_NAMES = ['abvm.e', 'abvm']

def glyph_filter_matra_i_alts(glyph):
    is_filted = False
    if re.match(
        SCRIPT_PREFIX + MATRA_I_NAME_STEM + r'\d\d$',
        glyph.name,
    ):
        is_filted = True
    return is_filted

def glyph_filter_bases_for_matra_i(glyph):
    name = glyph.name
    is_filted = False
    if name.startswith(SCRIPT_PREFIX):
        name = name[2:]
        if name.endswith('.MAR'):
            name = name[:-4]
        if name.endswith('.traditional'):
            name = name[:-12]
        if name.endswith('.simplified'):
            name = name[:-11]
        is_filted = name in POTENTIAL_BASES_FOR_MATRA_I
    return is_filted

def glyph_filter_bases_for_wide_matra_ii(glyph):
    name = glyph.name
    is_filted = False
    if name.startswith(SCRIPT_PREFIX) and SCRIPT_PREFIX == 'dv':
        name = name[2:]
        is_filted = name in POTENTIAL_BASES_FOR_WIDE_MATRA_II
    return is_filted

def get_stem_position(glyph, stem_right_margin):

    has_stem_anchor = False
    for anchor in glyph.anchors:
        if anchor.name in STEM_ANCHOR_NAMES:
            has_stem_anchor = True
            stem_anchor = anchor
            break

    if has_stem_anchor:
        stem_position = stem_anchor.x
    else:
        stem_position = glyph.width - stem_right_margin

    return stem_position

def restore_abvm_content(abvm_content):

    if re.search(
        r'# lookup MARK_BASE_{} \{{'.format(MATRA_I_ANCHOR_NAME),
        abvm_content
    ):

        abvm_content = re.sub(
            r'(?m)\n\n\n^lookup MARK_BASE_{0} \{{\n(^.+\n)+^\}} MARK_BASE_{0};'.format(MATRA_I_ANCHOR_NAME),
            r'',
            abvm_content
        )

        commented_abvm_lookup = re.search(
            r'(?m)^# lookup MARK_BASE_{0} \{{\n(^# .+\n)+^# \}} MARK_BASE_{0};'.format(MATRA_I_ANCHOR_NAME),
            abvm_content
        ).group()

        uncommented_abvm_lookup = '\n'.join([
            line[2:] for line in commented_abvm_lookup.splitlines()
        ])

        original_abvm_content = abvm_content.replace(
            commented_abvm_lookup,
            uncommented_abvm_lookup
        )

    else:
        original_abvm_content = abvm_content

    return original_abvm_content

def write_mI_matches_to_files(directory, mI_table, long_base_names):

    with open(directory + '/abvm.fea', 'r') as f:
        abvm_content = f.read()

    original_abvm_content = restore_abvm_content(abvm_content)

    original_abvm_lookup = re.search(
        r'(?m)^lookup MARK_BASE_{0} \{{\n(.+\n)+^\}} MARK_BASE_{0};'.format(MATRA_I_ANCHOR_NAME),
        original_abvm_content
    ).group()

    modified_abvm_lookup = original_abvm_lookup.replace(
        'pos base {}{}'.format(SCRIPT_PREFIX, MATRA_I_NAME_STEM),
        'pos base @generated_MATRA_I_BASES_'
    )

    Reph_positioning_offset = mI_table[0].glyph.width

    class_def_lines = []
    class_def_lines.extend(
        kit.builder.compose_glyph_class_def_lines('generated_MATRA_I_BASES_TOO_LONG', long_base_names)
    )

    substitute_rule_lines = []
    lookup_name = 'GENERATED_matra_i_matching'

    substitute_rule_lines.append('lookup {} {{'.format(lookup_name))

    for mI in mI_table:

        mI_number = mI.glyph.name[-2:]
        to_comment_substitute_rule = False

        if not mI.matches:
            print('\t       `%s` is not used.' % mI.glyph.name)
            to_comment_substitute_rule = True

            modified_abvm_lookup = modified_abvm_lookup.replace(
                '\tpos base @generated_MATRA_I_BASES_' + mI_number,
                '#\tpos base @generated_MATRA_I_BASES_' + mI_number
            )

        locator = '@generated_MATRA_I_BASES_%s <anchor ' % mI_number

        search_result = re.search(
            locator + r'\-?\d+',
            modified_abvm_lookup
        )

        if search_result:
            x = search_result.group().split(' ')[-1]
            modified_x = str(int(x) - Reph_positioning_offset)
            modified_abvm_lookup = modified_abvm_lookup.replace(
                locator + x,
                locator + modified_x,
            )

        else:
            print("\t[!] `%s` doesn't have the anchor for Reph." % mI.glyph.name)

        class_def_lines.extend(
            kit.builder.compose_glyph_class_def_lines(
                'generated_MATRA_I_BASES_' + mI_number,
                mI.matches
            )
        )

        substitute_rule_lines.append(
            "{}sub {}mI' @generated_MATRA_I_BASES_{} by {};".format(
                '# ' if to_comment_substitute_rule else '  ',
                SCRIPT_PREFIX,
                mI_number,
                mI.glyph.name
            )
        )

    substitute_rule_lines.append('}} {};'.format(lookup_name))

    commented_original_abvm_lookup = '# ' + original_abvm_lookup.replace('\n', '\n# ')

    modified_abvm_content = original_abvm_content.replace(
        original_abvm_lookup,
        commented_original_abvm_lookup + '\n\n\n' + modified_abvm_lookup
    )

    with open(directory + '/abvm.fea', 'w') as f:
        f.write(modified_abvm_content)

    with open(directory + '/matra_i_matching.fea', 'w') as f:
        result_lines = (
            ['# CLASSES', ''] + class_def_lines +
            ['# RULES', ''] + substitute_rule_lines
        )
        f.write('\n'.join(result_lines) + '\n')

def match_matra_i_alts(style, offset_range = (0, 0)):

    font = style.open_font()

    mI_list   = [font[glyph_name] for glyph_name in sorted(font.groups['generated_MATRA_I_ALTS'])]
    base_list = [font[glyph_name] for glyph_name in font.groups['generated_BASES_FOR_MATRA_I']]

    MatchRow = collections.namedtuple('MatchRow', 'glyph, stretch, matches')

    mI_table = [
        MatchRow(
            glyph   = mI,
            stretch = abs(mI.rightMargin),
            matches = []
        ) for mI in mI_list
    ]

    for anchor in font[SCRIPT_PREFIX + 'mE'].anchors:
        if anchor.name in ['_' + name for name in STEM_ANCHOR_NAMES]:
            stem_right_margin = abs(anchor.x)
            break
    else:
        raise SystemExit("[WARNING] Can't find the stem anchor in glyph `mE`!")

    tolerance_of_mI_stretch_shormI_numbere = (font[SCRIPT_PREFIX + 'VA'].width - stem_right_margin) / 2
    long_base_names = []

    stem_positions = [get_stem_position(b, stem_right_margin) for b in base_list]
    stem_position_min = min(stem_positions)
    stem_position_max = max(stem_positions)

    stem_positions_with_offset = []
    for stem_position in stem_positions:
        ratio = (stem_position - stem_position_min) / (stem_position_max - stem_position_min)
        adjusted_offset = offset_range[0] + (offset_range[-1] - offset_range[0]) * ratio
        stem_position_with_offset = stem_position + int(adjusted_offset)
        stem_positions_with_offset.append(stem_position_with_offset)

    for i, base in enumerate(base_list):

        base_name = base.name
        stem_position = stem_positions_with_offset[i]

        if stem_position < mI_table[0].stretch:
            mI_table[0].matches.append(base_name)

        elif stem_position >= mI_table[-1].stretch:
            if stem_position < mI_table[-1].stretch + tolerance_of_mI_stretch_shormI_numbere:
                mI_table[-1].matches.append(base_name)
            else:
                long_base_names.append(base_name)

        else:
            for index, mI in enumerate(mI_table):
                if stem_position < mI.stretch:
                    if mI.stretch - stem_position < abs(mI_table[index - 1].stretch - stem_position):
                        mI.matches.append(base_name)
                    else:
                        mI_table[index - 1].matches.append(base_name)
                    break

    write_mI_matches_to_files(style.directory, mI_table, long_base_names)

POTENTIAL_BASES_FOR_WIDE_MATRA_II = '''\
KA
PHA
KxA
PHxA
K_RA
PH_RA
Kx_RA
PHx_RA
J_KA
K_KA
K_PHA
Kx_KxA
Kx_PHA
Kx_PHxA
L_KA
L_PHA
N_KA
N_PHA
N_PH_RA
PH_PHA
PHx_PHxA
P_PHA
SH_KA
SH_KxA
SS_KA
SS_K_RA
SS_PHA
S_KA
S_K_RA
S_PHA
T_KA
T_K_RA
T_PHA
K_TA.traditional
'''.splitlines()

POTENTIAL_BASES_FOR_MATRA_I = '''\
KA
KHA
GA
GHA
NGA
CA
CHA
JA
JHA
NYA
TTA
TTHA
DDA
DDHA
NNA
TA
THA
DA
DHA
NA
PA
PHA
BA
BHA
MA
YA
RA
LA
VA
SHA
SSA
SA
HA
LLA
K_SSA
J_NYA
KxA
KHxA
GxA
GHxA
NGxA
CxA
CHxA
JxA
JHxA
NYxA
TTxA
TTHxA
DDxA
DDHxA
NNxA
TxA
THxA
DxA
DHxA
NxA
PxA
PHxA
BxA
BHxA
MxA
YxA
RxA
LxA
VxA
SHxA
SSxA
SxA
HxA
LLxA
GAbar
JAbar
DDAbar
BAbar
ZHA
YAheavy
DDAmarwari
K_RA
KH_RA
G_RA
GH_RA
NG_RA
C_RA
CH_RA
J_RA
JH_RA
NY_RA
TT_RA
TTH_RA
DD_RA
DDH_RA
NN_RA
T_RA
TH_RA
D_RA
DH_RA
N_RA
P_RA
PH_RA
B_RA
BH_RA
M_RA
Y_RA
L_RA
V_RA
SH_RA
SS_RA
S_RA
H_RA
LL_RA
K_SS_RA
J_NY_RA
Kx_RA
KHx_RA
Gx_RA
GHx_RA
NGx_RA
Cx_RA
CHx_RA
Jx_RA
JHx_RA
NYx_RA
TTx_RA
TTHx_RA
DDx_RA
DDHx_RA
NNx_RA
Tx_RA
THx_RA
Dx_RA
DHx_RA
Nx_RA
Px_RA
PHx_RA
Bx_RA
BHx_RA
Mx_RA
Yx_RA
Lx_RA
Vx_RA
SHx_RA
SSx_RA
Sx_RA
Hx_RA
LLx_RA
K_KA
Kx_KxA
K_KHA
K_CA
K_JA
K_TTA
K_TT_RA
K_NNA
K_TA
Kx_TA
K_T_YA
K_T_RA
K_T_VA
K_THA
K_DA
K_NA
Kx_NA
K_PA
K_P_RA
K_PHA
Kx_PHA
Kx_PHxA
K_BA
Kx_BA
K_MA
Kx_MA
K_YA
K_LA
K_VA
K_V_YA
K_SHA
Kx_SHA
K_SS_MA
K_SS_M_YA
K_SS_YA
K_SS_VA
K_SA
K_S_TTA
K_S_DDA
K_S_TA
K_S_P_RA
K_S_P_LA
KH_KHA
KH_TA
KHx_TA
KH_NA
KHx_NA
KH_MA
KHx_MA
KH_YA
KHx_YA
KH_VA
KHx_VA
KH_SHA
KHx_SHA
KHx_SA
G_GA
G_GHA
G_JA
G_NNA
G_DA
G_DHA
G_DH_YA
G_DH_VA
G_NA
Gx_NA
G_N_YA
G_BA
G_BHA
G_BH_YA
G_MA
G_YA
G_R_YA
G_LA
G_VA
G_SA
GH_NA
GH_MA
GH_YA
NG_KA
NG_KHA
NG_GA
NG_GHA
NG_NGA
NG_YA
NG_VA
C_CA
C_CHA
C_CH_VA
C_NA
C_MA
C_YA
CH_YA
CH_R_YA
CH_VA
J_KA
J_JA
Jx_JxA
J_J_NYA
J_J_YA
J_J_VA
J_JHA
J_NY_YA
J_TTA
J_DDA
J_TA
J_DA
J_NA
Jx_NA
J_BA
J_MA
J_YA
Jx_YA
J_VA
JH_NA
JH_MA
JH_YA
NY_CA
NY_CHA
NY_JA
NY_NYA
NY_SHA
TT_TTA
TT_TTHA
TT_YA
TT_VA
TTH_TTHA
TTH_YA
TTH_VA
DD_DDA
DD_DDHA
DD_YA
DD_VA
DDH_DDHA
DDH_YA
DDH_VA
NN_TTA
NN_TTHA
NN_DDA
NN_DDHA
NN_NNA
NN_MA
NN_YA
NN_VA
T_KA
T_K_YA
T_K_RA
T_K_VA
T_K_SSA
T_KHA
T_KH_NA
T_KH_RA
T_TA
T_T_YA
T_T_VA
T_THA
T_NA
T_N_YA
T_PA
T_P_RA
T_P_LA
T_PHA
T_MA
T_M_YA
T_YA
T_R_YA
T_LA
T_VA
T_SA
T_S_NA
T_S_YA
T_S_VA
TH_NA
TH_YA
TH_VA
D_GA
D_G_RA
D_GHA
D_DA
D_DHA
D_DH_YA
D_NA
D_BA
D_B_RA
D_BHA
D_BH_YA
D_MA
D_YA
D_R_YA
D_VA
D_V_YA
DH_NA
DH_N_YA
DH_MA
DH_YA
DH_VA
N_KA
N_K_SA
N_CA
N_CHA
N_JA
N_TTA
N_DDA
N_TA
N_T_YA
N_T_RA
N_T_SA
N_THA
N_TH_YA
N_TH_VA
N_DA
N_D_RA
N_D_VA
N_DHA
N_DH_YA
N_DH_RA
N_DH_VA
N_NA
N_N_YA
N_PA
N_P_RA
N_PHA
N_PH_RA
N_BHA
N_BH_YA
N_BH_VA
N_MA
N_M_YA
N_YA
N_VA
N_SHA
N_SA
N_S_TTA
N_S_M_YA
N_S_YA
N_HA
P_CA
P_TTA
P_TTHA
P_TA
P_T_YA
P_NA
P_PA
P_PHA
P_MA
P_YA
P_LA
P_VA
P_SHA
P_SA
PH_JA
PHx_JxA
PH_TTA
PHx_TTA
PH_TA
PHx_TA
PH_NA
PHx_NA
PH_PA
PH_PHA
PHx_PHxA
PH_YA
PH_LA
PH_SHA
PHx_SA
B_JA
B_JxA
B_J_YA
B_JHA
B_TA
B_DA
B_DHA
B_DH_VA
B_NA
B_BA
B_BHA
B_BH_RA
B_YA
B_LA
B_L_YA
B_VA
B_SHA
B_SA
BH_NA
BH_YA
BH_R_YA
BH_LA
BH_VA
M_TA
M_DA
M_NA
M_PA
M_P_RA
M_BA
M_B_YA
M_B_RA
M_BHA
M_BH_YA
M_BH_RA
M_BH_VA
M_MA
M_YA
M_LA
M_VA
M_SHA
M_SA
M_HA
Y_NA
Y_YA
Eyelash_YA
Eyelash_HA
L_KA
L_K_YA
L_KHA
L_GA
L_CA
L_JA
L_JxA
L_TTA
L_TTHA
L_DDA
L_DDHA
L_TA
L_THA
L_TH_YA
L_DA
L_D_RA
L_NA
L_PA
L_PHA
L_BA
L_BHA
L_MA
L_YA
L_LA
L_L_YA
L_VA
L_V_DDA
L_SA
L_HA
V_NA
V_YA
V_LA
V_VA
V_HA
SH_KA
SH_KxA
SH_CA
SH_CHA
SH_TTA
SH_TA
SH_NA
SH_MA
SH_YA
SH_LA
SH_VA
SH_SHA
SS_KA
SS_K_RA
SS_TTA
SS_TT_YA
SS_TT_RA
SS_TT_VA
SS_TTHA
SS_TTH_YA
SS_TTH_RA
SS_NNA
SS_NN_YA
SS_NA
SS_PA
SS_P_RA
SS_PHA
SS_MA
SS_M_YA
SS_YA
SS_VA
SS_SSA
S_KA
S_K_RA
S_K_VA
S_KHA
S_JA
S_TTA
S_TA
S_T_YA
S_T_RA
S_T_VA
S_THA
S_TH_YA
S_DA
S_NA
S_PA
S_P_RA
S_PHA
S_BA
S_MA
S_M_YA
S_YA
S_LA
S_VA
S_SA
H_NNA
H_NA
H_MA
H_YA
H_LA
H_VA
LL_YA
NG_NA
NG_MA
CH_NA
TT_NA
TTH_NA
DD_NA
'''.splitlines()
