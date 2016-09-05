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
        return StringIO.StringIO(self.dictionary.aliasfile(names) + '\n')


class Goadb(kit.BaseFile):

    TTF_DIFFERENCES_INTRODUCED_BY_GLYPHS_APP = {
        'CR\tCR\tuni000D\n': 'CR\tuni000D\tuni000D\n',
        'uni00A0\tnonbreakingspace\tuni00A0\n': 'uni00A0\tuni00A0\tuni00A0\n',
    }

    def __init__(
        self,
        project,
        name = 'GlyphOrderAndAliasDB',
        for_ttf = False,
    ):
        super(Goadb, self).__init__(name, project=project)
        self.for_ttf = for_ttf

    def generate(self, names=None):
        goadb_trimmed = self.project.glyph_data.generate_goadb(names)
        with open(self.path, 'w') as f:
            for line in goadb_trimmed:
                if self.for_ttf:
                    line = self.TTF_DIFFERENCES_INTRODUCED_BY_GLYPHS_APP.get(
                        line,
                        line,
                    )
                f.write(line)
