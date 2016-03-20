#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import sys

import hindkit as kit

sys.path.insert(0, kit.relative_to_interpreter('../SharedData/FDKScripts'))
import agd

class GlyphData(object):

    @staticmethod
    def normalize(lines):
        for line in lines:
            yield '\t'.join(line.partition('#')[0].split())

    @classmethod
    def patch(cls, dictionary):
        ITFDG = []
        for glyph in ITFDG:
            dictionary.add(glyph, priority=3)
        return dictionary

    def __init__(self, glyph_order_path='glyphorder.txt'):

        self.glyph_order_path = glyph_order_path

        self.name_order = []

        self.production_names = []
        self.development_names = []
        self.u_mappings = []

        with open(kit.relative_to_interpreter('../SharedData/AGD.txt'), 'rU') as f:
            self.agd_dictionary = agd.dictionary(f.read())

        self.itfgd_dictionary = self.patch(self.agd_dictionary)

    def generate_name_order(self):
        for section in self.name_order_raw:
            if is_agd():
                self.name_order.extend(kit.agd.cfforder(section))
            else:
                self.name_order.extend(section)


class Goadb(kit.BaseObject):

    def __init__(self, name='GlyphOrderAndAliasDB'):

        super(Goadb, self).__init__(name)

        # self.goadb_path_trimmed = kit.temp(self.goadb_path + '_trimmed')
        # self.goadb_path_trimmed_ttf = kit.temp(self.goadb_path + '_trimmed_ttf')

    def generate(self, reference_font):

        goadb = []

        if os.path.exists('glyphorder.txt'):

            self.goadb_path = kit.temp(self.goadb_path)

            glyphorder = []
            with open('glyphorder.txt') as f:
                for line in self.normalize(f):
                    for development_name in line.split():
                        glyphorder.append(development_name)

            U_SCALAR_TO_U_NAME = kit.misc.get_u_scalar_to_u_name()

            AGLFN = kit.misc.get_glyph_list('aglfn.txt')
            ITFGL = kit.misc.get_glyph_list('itfgl.txt')
            ITFGL_PATCH = kit.misc.get_glyph_list('itfgl_patch.txt')

            AL5 = kit.misc.get_adobe_latin(5)

            D_NAME_TO_U_NAME = {}
            D_NAME_TO_U_NAME.update(AGLFN)
            D_NAME_TO_U_NAME.update(AL5)
            D_NAME_TO_U_NAME.update(ITFGL)
            D_NAME_TO_U_NAME.update(ITFGL_PATCH)

            U_NAME_TO_U_SCALAR = {v: k for k, v in U_SCALAR_TO_U_NAME.items()}
            AGLFN_REVERSED = {v: k for k, v in AGLFN.items()}

            PREFIXS = tuple(
                v['abbreviation']
                for v in kit.misc.SCRIPTS.values()
            )

            PRESERVED_NAMES = 'NULL CR'.split()

            SPECIAL_D_NAME_TO_U_SCALAR = {
                'NULL': '0000',
                'CR': '000D',
            }

            u_mapping_pattern = re.compile(r'uni([0-9A-F]{4})|u([0-9A-F]{5,6})$')

            with open(self.goadb_path, 'w') as f:

                for development_name in glyphorder:

                    u_scalar = None
                    u_mapping = None
                    production_name = None

                    match = u_mapping_pattern.match(development_name)
                    if match:
                        u_scalar = filter(None, match.groups())[0]
                        u_name = U_SCALAR_TO_U_NAME[u_scalar]
                    else:
                        u_name = D_NAME_TO_U_NAME.get(development_name)
                        if u_name:
                            u_scalar = U_NAME_TO_U_SCALAR[u_name]
                        else:
                            u_scalar = SPECIAL_D_NAME_TO_U_SCALAR.get(development_name)

                    if u_scalar:
                        form = 'uni{}' if (len(u_scalar) <= 4) else 'u{}'
                        u_mapping = form.format(u_scalar)

                    if u_name in AGLFN.values():
                        production_name = AGLFN_REVERSED[u_name]
                    elif (
                        development_name in PRESERVED_NAMES or
                        development_name.partition('.')[0].split('_')[0] in ITFGL
                    ):
                        production_name = development_name
                    elif u_mapping:
                        production_name = u_mapping
                    else:
                        production_name = development_name

                    row = production_name, development_name, u_mapping
                    f.write(' '.join(filter(None, row)) + '\n')
                    goadb.append(row)

        else:
            with open(self.path) as f:
                for line in self.normalize(f):
                    row = line.split()
                    if len(row) == 2:
                        row.append(None)
                    production_name, development_name, u_mapping = row
                    goadb.append(
                        (production_name, development_name, u_mapping)
                    )

    def output_trimmed(self, reference_font, build_ttf=False):
        DIFFERENCES = {
            'CR CR uni000D\n': 'CR uni000D uni000D\n',
        }
        not_covered_glyphs = [
            glyph.name
            for glyph in reference_font
            if glyph.name not in self.development_names
        ]
        if not_covered_glyphs:
            raise SystemExit(
                'Some glyphs are not covered by the GOADB: ' +
                ' '.join(not_covered_glyphs)
            )
        else:
            trimmed = open(self.path_trimmed, 'w')
            if build_ttf:
                trimmed_ttf = open(self.path_trimmed_ttf, 'w')
            for row in self.table:
                if row.development_name in reference_font:
                    line = ' '.join(filter(None, row)) + '\n'
                    trimmed.write(line)
                    if build_ttf:
                        line_ttf = DIFFERENCES.get(line, line)
                        trimmed_ttf.write(line_ttf)
            trimmed.close()
            if build_ttf:
                trimmed_ttf.close()
