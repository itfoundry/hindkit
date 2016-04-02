#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, sys, StringIO
import hindkit as kit

sys.path.insert(0, kit.relative_to_interpreter('../SharedData/FDKScripts'))
import agd

class GlyphData(object):

    with open(kit.relative_to_interpreter('../SharedData/AGD.txt'), 'rU') as f:
        agd_content = f.read()
    agd_dictionary = agd.dictionary(agd_content)

    ITFDG = []

    @staticmethod
    def split(line):
        return line.partition('#')[0].split()

    def __init__(
        self,
        glyph_order_name = 'glyphorder.txt',
        goadb_name = 'GlyphOrderAndAliasDB',
    ):

        self.glyph_order = []
        self.glyph_order_trimmed = None
        self.dictionary = agd.dictionary()
        self.goadb = StringIO.StringIO()

        if os.path.exists(goadb_name):

            with open(goadb_name) as f:
                self.goadb.writelines(
                    '\t'.join(self.split(line)) + '\n'
                    for line in f
                )

            for glyph in agd.parsealiasfile(self.goadb.getvalue()):
                self.dictionary.add(glyph, priority=3)

            self.glyph_order = self.dictionary.list

        elif os.path.exists(glyph_order_name):

            with open(glyph_order_name) as f:
                for line in f:
                    development_name = self.split(line)[0]
                    if development_name:
                        self.glyph_order.append(development_name)

            self.dictionary = agd.dictionary(self.agd_content)
            for glyph in self.ITFDG:
                self.dictionary.add(glyph, priority=3)

            self.goadb = self.generate_goadb()

        # self.production_names = []
        # self.development_names = []
        # self.u_mappings = []

    # def generate_name_order(self):
    #     for section in self.name_order_raw:
    #         if is_agd():
    #             self.name_order.extend(kit.agd.cfforder(section))
    #         else:
    #             self.name_order.extend(section)

    def generate_goadb(self, names=None):
        if names is None:
            names = self.glyph_order
        self.goadb = self.dictionary.aliasfile(names) + '\n'


class Goadb(kit.BaseFile):

    TTF_DIFFERENCES_INTRODUCED_BY_GLYPHS_APP = {
        'CR CR uni000D\n': 'CR uni000D uni000D\n',
    }

    def __init__(
        self,
        project,
        glyph_order_trimmed,
        name = 'GlyphOrderAndAliasDB',
        for_ttf = False,
    ):
        super(Goadb, self).__init__(name, project=project)
        self.glyph_order_trimmed = glyph_order_trimmed
        self.for_ttf = for_ttf

    def generate(self):
        if self.project.glyph_data.goadb is None:
            self.project.glyph_data.generate_goadb(self.glyph_order_trimmed)
        with open(self.path, 'w') as f:
            for line in self.project.glyph_data.goadb:
                if self.for_ttf:
                    line = self.TTF_DIFFERENCES_INTRODUCED_BY_GLYPHS_APP.get(line, line)
                f.write(line)

    def old(self):

        goadb = []

        if os.path.exists('glyphorder.txt'):

            self.goadb_path = kit.temp(self.goadb_path)

            # glyphorder = []
            # with open('glyphorder.txt') as f:
            #     for line in self.normalize(f):
            #         for development_name in line.split():
            #             glyphorder.append(development_name)

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
