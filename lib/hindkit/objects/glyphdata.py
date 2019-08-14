#!/usr/bin/env AFDKOPython
# encoding: UTF-8


import os, sys, collections
import hindkit as kit

class GlyphData(object):

    ITFDG = []

    @staticmethod
    def split(line):
        return line.partition("#")[0].split()

    def __init__(
        self,
        glyph_order_name = "glyphorder.txt",
    ):

        self.glyph_order = []
        self.dictionary = collections.OrderedDict()
        self.goadb_path = kit.Project.directories["GOADB"]

        if os.path.exists(self.goadb_path):

            with open(self.goadb_path) as f:
                for line in f:
                    parts = self.split(line)
                    if parts:
                        development_name = parts[1]
                        production_name = parts[0]
                        if len(parts) >= 3:
                            uni = parts[2]
                        else:
                            uni = None
                        self.dictionary[development_name] = production_name, uni

            self.glyph_order = list(self.dictionary.keys())

    def generate_goadb(self, names=None):
        if names is None:
            names = self.glyph_order
        lines = []
        for development_name, data in list(self.dictionary.items()):
            if (names is None) or (development_name in names):
                production_name, uni = data
                if uni:
                    lines.append(
                        "{} {} {}".format(
                            production_name.replace("-", "__"),
                            development_name,
                            uni,
                        )
                    )
                else:
                    lines.append(
                        "{} {}".format(
                            production_name.replace("-", "__"),
                            development_name,
                        )
                    )
        return lines


class Goadb(kit.BaseFile):

    TTF_DIFFERENCES_INTRODUCED_BY_GLYPHS_APP = {
        "CR CR uni000D": "CR uni000D uni000D",
        "uni00A0 nonbreakingspace uni00A0": "uni00A0 uni00A0 uni00A0",
    }

    def __init__(
        self,
        project,
        name = "GlyphOrderAndAliasDB",
        product=None,
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

    def generate(self):
        goadb_lines = self.project.glyph_data.generate_goadb(names=self.names)
        with open(self.get_path(), "w") as f:
            for line in goadb_lines:
                if self.product.file_format == "TTF":
                    line = self.TTF_DIFFERENCES_INTRODUCED_BY_GLYPHS_APP.get(
                        line,
                        line,
                    )
                f.write(line + "\n")
