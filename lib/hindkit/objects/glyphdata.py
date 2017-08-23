#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, sys, StringIO
import hindkit as kit

sys.path.insert(0, kit.relative_to_interpreter("../SharedData/FDKScripts"))
import agd

class GlyphData(object):

    with open(kit.relative_to_interpreter("../SharedData/AGD.txt"), "rU") as f:
        agd_content = f.read()
    agd_dictionary = agd.dictionary(agd_content)

    ITFDG = []

    @staticmethod
    def split(line):
        return line.partition("#")[0].split()

    def __init__(
        self,
        glyph_order_name = "glyphorder.txt",
    ):

        self.glyph_order = []
        self.dictionary = agd.dictionary()
        self.goadb = StringIO.StringIO()
        self.goadb_path = kit.Goadb.NAME

        if os.path.exists(self.goadb_path):

            with open(self.goadb_path) as f:
                self.goadb.writelines(
                    "\t".join(self.split(line)) + "\n"
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
        return StringIO.StringIO(self.dictionary.aliasfile(names) + "\n")


class Goadb(kit.BaseFile):

    NAME = "GlyphOrderAndAliasDB"

    TTF_DIFFERENCES_INTRODUCED_BY_GLYPHS_APP = {
        "CR\tCR\tuni000D\n": "CR\tuni000D\tuni000D\n",
        "uni00A0\tnonbreakingspace\tuni00A0\n": "uni00A0\tuni00A0\tuni00A0\n",
    }

    def __init__(
        self,
        project,
        name = "GlyphOrderAndAliasDB",
        content = None,
        product = None,
    ):
        if product:
            abstract_directory = product.style.abstract_directory
        else:
            abstract_directory = kit.Project.directories["sources"]
        super(Goadb, self).__init__(
            name,
            project = project,
            abstract_directory = abstract_directory,
        )
        self.product = product
        if self.product:
            names = self.project.glyph_data.glyph_order
            reference_names = self.product.style.open().glyphOrder
            not_covered_glyphs = [
                name
                for name in reference_names
                if name not in names
            ]
            if not_covered_glyphs:
                print(
                    "[WARNING] Some glyphs are not covered by the GOADB: " +
                    " ".join(not_covered_glyphs)
                )
                if self.project.options["build_ttf"]:
                    raise SystemExit("[EXIT] GOADB must match the glyph set exactly for compiling TTFs.")
            self.names = [
                name
                for name in names
                if name in reference_names
            ]
        else:
            self.names = None
        self.content = kit.fallback(
            content,
            self.project.glyph_data.generate_goadb(names=self.names),
        )

    def parse(self):
        pass

    def generate(self):
        with open(self.get_path(), "w") as f:
            for line in self.content:
                if self.product and self.product.file_format == "TTF":
                    line = self.TTF_DIFFERENCES_INTRODUCED_BY_GLYPHS_APP.get(line, line)
                f.write(line)
