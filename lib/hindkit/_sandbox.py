#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import hindkit as kit

ALIVE_CONSONANTS = [i + 'A' for i in kit.constants.CONSONANT_STEMS] + \
                   'GAbar JAbar DDAbar BAbar ZHA YAheavy DDAmarwari'.split()
DEAD_CONSONANTS = kit.constants.CONSONANT_STEMS

# font.groups['BASES_ALIVE']
# font.groups['BASES_DEAD']

consonant_name_sequences = [
    'K KA',
    'G GA',
]
base_name_sequences = [
    'K_KA',
    'G GA',
]

def match_mI():
    pass
def position_marks():
    pass

def match_mI_variants(style, adjustment_extremes):

    font = style.open()

    # get abvm_right_margin

    abvm_position_in_mE = get_abvm_position(
        font[style.family.script.abbreviation + 'mE'],
        in_base = False,
    )
    if abvm_position_in_mE is None:
        raise SystemExit("[WARNING] Can't find the abvm anchor in glyph `mE`!")
    else:
        abvm_right_margin = abs(abvm_position_in_mE)

    # get tolerance

    tolerance = get_stem_position(
        font[style.family.script.abbreviation + 'VA']
    ) * 0.5

    # prepare bases and matches

    bases = [
        Base(
            name_sequence = base_name_sequence,
            abvm_right_margin = abvm_right_margin,
        )
        for base_name_sequence in base_name_sequences
    ]
    if adjustment_extremes:
        targets = [base.target for base in bases]
        target_min = min(targets)
        target_max = max(targets)
        for target in targets:
            print('Old:', target, end=', ')
            ratio = (target - target_min) / (target_max - target_min)
            adjustment = (
                adjustment_extremes[0] +
                (adjustment_extremes[-1] - adjustment_extremes[0]) * ratio
            )
            target += adjustment
            print('New:', target, end='; ')
        print()

    matches = [
        Match(font=font, mI_variant_name=name)
        for name in font.groups['MATRA_I_ALTS']
    ]
    bases_ignored = []

    for base in bases:
        if base.target <= matches[0].overhanging:
            match = matches[0]
        elif base.target < matches[-1].overhanging:
            i = 0
            while matches[i].overhanging < base.target:
                candidate_short = matches[i]
                i += 1
            candidate_enough = matches[i]
            if (
                abs(candidate_enough.overhanging - base.target) <
                abs(candidate_short.overhanging - base.target)
            ):
                match = candidate_enough
            else:
                match = candidate_short
        elif base.target <= matches[-1].overhanging + tolerance:
            match = matches[-1]
        else:
            match = bases_ignored
        match.bases.append(base)

    return matches, bases_ignored

mI_NAME_STEM = 'mI.'
mI_ANCHOR_NAME = 'abvm.i'

def output_mI_variant_matches(style, matches, bases_ignored):

    lookup_name = 'matra_i_matching'

    do_position_marks = style.family.project.options[
        'position_marks_for_mI_variants'
    ]
    abvm_backup_path = os.path.join(
        style.directory,
        'backup--' + WriteFeaturesMarkFDK.kAbvmFeatureFileName,
    )
    abvm_path = os.path.join(
        style.directory,
        WriteFeaturesMarkFDK.kAbvmFeatureFileName,
    )
    matches_path = os.path.join(
        style.directory,
        lookup_name + '.fea',
    )

    if do_position_marks:

        if os.path.exists(abvm_path_backup):
            kit.copy(abvm_backup_path, abvm_path)
        else:
            kit.copy(abvm_path, abvm_backup_path)
        with open(abvm_path, 'r') as f:
            abvm_content = f.read()

        abvm_lookup = re.search(
            r'''
                (?mx)
                lookup \s (MARK_BASE_%s) \s \{ \n
                ( .+ \n )+
                \} \s \1 ; \n
            ''' % mI_ANCHOR_NAME,
            abvm_content,
        ).group(0)
        print('abvm_lookup:', abvm_lookup)

        abvm_lookup_modified = abvm_lookup.replace(
            'pos base %s%s' % (style.family.script.abbreviation, mI_NAME_STEM),
            'pos base @MATRA_I_BASES_',
        )

    mark_positioning_offset = matches.mI_variant.width

    # class_def_lines = []
    # class_def_lines.extend(
    #     kit.Feature.compose_glyph_class_def_lines(
    #         'MATRA_I_BASES_TOO_LONG',
    #         [base.name for base in bases_ignored]
    #     )
    # )

    substitute_rule_lines = []

    substitute_rule_lines.append('lookup %s {' % lookup_name)

    for match in matches:

        do_comment_substitute_rule = False

        if not match.bases:
            print('\t\t`{}` is not used.'.format(match.name))
            do_comment_substitute_rule = True

            if do_position_marks:
                abvm_lookup_modified = abvm_lookup_modified.replace(
                    '\tpos base @MATRA_I_BASES_' + match.number,
                    '#\tpos base @MATRA_I_BASES_' + match.number
                )

        if do_position_marks:
            pass


    substitute_rule_lines.append('} %s;' % lookup_name)

    if do_position_marks:
        abvm_content_modified = abvm_content.replace(
            abvm_lookup,
            abvm_lookup_modified,
        )
        with open(abvm_path, 'w') as f:
            f.write(abvm_content_modified)

    with open(matches_path, 'w') as f:
        f.write(
            line + '\n'
            for line in class_def_lines + substitute_rule_lines
        )

class Base(object):
    def __init__(self, name_sequence, abvm_right_margin):
        self.name_sequence = name_sequence
        self.target = 0
        for glyph in base:
            if is_alive(glyph):
                self.target += get_stem_position(glyph, abvm_right_margin)
            elif is_dead(glyph):
                self.target += glyph.width
            else: # is mark, etc.
                pass

class Match(object):
    def __init__(self, font, mI_variant_name):
        self.name = mI_variant_name
        self.mI_variant = font[self.name]
        self.number = self.mI_variant.name.partition('.')[2]
        self.overhanging = abs(self.mI_variant.rightMargin)
        self.bases = []

ABVM_ANCHOR_NAMES = ['abvm.e', 'abvm']
def get_abvm_position(glyph, in_base=True):
    anchor_name_prefix = '' if in_base else '_'
    for potential_anchor_name in ABVM_ANCHOR_NAMES:
        for anchor in glyph.anchors:
            if anchor.name == anchor_name_prefix + potential_anchor_name:
                return anchor.x

def get_stem_position(glyph, abvm_right_margin):
    abvm_position = get_abvm_position(glyph)
    if abvm_position is None:
        return glyph.width - abvm_right_margin
    else:
        return abvm_position
