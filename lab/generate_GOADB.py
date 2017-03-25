#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import hindkit as k

class GlyphSet(object):

    def __init__(self, development_names = []):
        self.glyphs = [Glyph(name) for name in development_names]

    def to_goadb(self, convert_to_production_name=True):
        goadb_lines = []
        for glyph in self.glyphs:
            if convert_to_production_name:
                row = [glyph.production_name, glyph.name]
            else:
                row = [glyph.name, glyph.name]
            if glyph.unicode_mapping:
                row.append("uni" + glyph.unicode_mapping)
            line = " ".join(row)
            goadb_lines.append(line)
        goadb = "\n".join(goadb_lines) + "\n"
        return goadb

u_name_to_u_scalar = {v: k for k, v in k.constants.get_u_scalar_to_u_name().items()}

class Glyph(object):

    cstems = k.constants.CONSONANT_STEMS
    vstems = k.constants.VOWEL_STEMS

    half_map = {s: (s + "A_Virama") for s in cstems}
    nukta_map = {(s + "xA"): (s + "A_Nukta") for s in cstems}
    half_nukta_map = {(s + "x"): (s + "A_Nukta_Virama") for s in cstems}
    c2_map = {(s + "Ac2"): ("Virama_" + s + "A") for s in cstems}
    cv_map = {}
    for v in vstems:
        for c in cstems:
            cv_map[c + v] = c + "A_m" + v
        cv_map["KSS" + v] = "KA_Virama_SSA_m" + v

    shorthand_flattening_map = {
        "Reph": "RA_Virama",
        "Eyelash": "RA_Virama_zerowidthjoiner",
        "Rashtrasign": "Virama_RA",
        "Rakar": "Virama_RA",
        "RAphalaa": "Virama_RA",
        "BAphalaa": "Virama_BA",
        "YAphalaa": "Virama_YA",
    }
    for m in [half_map, nukta_map, half_nukta_map, c2_map, cv_map]:
        shorthand_flattening_map.update(m)

    name_to_scalar_map  = {
        "space": "0020",
        "rupee": "20A8",
        "indianrupee": "20B9",
        "apostrophemod": "02BC",
        "zerowidthspace": "200B",
        "zerowidthnonjoiner": "200C",
        "zerowidthjoiner": "200D",
        "dottedcircle": "25CC",
    }
    name_to_scalar_map.update({
        glyph_name: u_name_to_u_scalar[u_name]
        for glyph_name, u_name in k.constants.get_glyph_list("itfgl.txt").items()
    })

    def __init__(
        self,
        development_name = "",
        unicode_mapping = "",
        production_name = "",
        character_sequence = "", #TODO
    ):
        if development_name:
            self.name = development_name
            self.prefix, self.stem, self.stem_pieces, self.suffixes = self._get_name_structure()
            if unicode_mapping:
                self.unicode_mapping = unicode_mapping
            else:
                self.unicode_mapping = self._get_unicode_mapping()
            if production_name:
                self.production_name = production_name
            else:
                self.production_name = self._get_production_name()
        elif unicode_mapping:
            self.unicode_mapping = unicode_mapping
            self.name = self._get_name_from_unicode_mapping()
            if production_name:
                self.production_name = production_name
            else:
                self.production_name = self._get_production_name()
        elif production_name:
            self.production_name = production_name
            self.name = self._get_name_from_production_name()
            self.unicode_mapping = self._get_unicode_mapping()

    def _get_unicode_mapping(self):
        return self.name_to_scalar_map.get(self.name, "")

    def _get_name_from_unicode_mapping(self):
        return kit.linguistics.SCALAR_TO_NAME_MAP.get(self.unicode_mapping, "uni" + unicode_mapping)

    def _get_name_structure(self):
        name = self.name
        prefix = ""
        if name.startswith(
            tuple(
                i.abbr for i in k.constants.SCRIPT_NAMES_TO_SCRIPTS.values()
            )
        ):
            prefix = name[:2]
            name = name[2:]
        stem, sep, suffix = name.partition(".")
        stem_pieces = stem.split("_")
        suffixes = suffix.split(".")
        if name == ".notdef":
            stem = ".notdef"
            stem_pieces = [stem]
            suffixes = []
        return prefix, stem, stem_pieces, suffixes

    def _get_scalars(self):

        splits = self.stem_pieces[:]

        splits_with_underscores = [self.shorthand_flattening_map.get(s, s) for s in splits]

        splits = []
        for s in splits_with_underscores:
            splits.extend(s.split("_"))

        scalars = []
        for split in splits:

            prefix_for_this_split = self.prefix
            if split in ["zerowidthjoiner", "udatta", "anudatta"]:
                prefix_for_this_split = ""
            name = prefix_for_this_split + split

            if name in k.constants.get_glyph_list("aglfn.txt"):
                scalars.append(name)
            else:
                scalar = self.name_to_scalar_map.get(name)
                if scalar:
                    scalars.append("uni" + scalar)
                else:
                    scalars.append("{" + name + "}")

        suffixes = self.suffixes[:]
        if self.stem_pieces == ["Reph"]: # Information lost in scalars gets into suffixes
            suffixes.insert(0, "reph")
        suffixes = filter(None, suffixes)

        return scalars, suffixes

    def _get_production_name(self):
        scalars, suffixes = self._get_scalars()
        production_name = scalars[0]
        for s in scalars[1:]:
            if s.startswith("uni"):
                production_name += s[3:]
            else:
                production_name += s
        if suffixes:
            production_name += "." + ".".join(suffixes)
        return production_name

    def _get_sequence(self):
        scalars, suffixes = self._get_scalars()
        characters = []
        for s in scalars:
            if s.startswith("uni"):
                characters.append(("\\u" + s[3:]).decode("unicode_escape"))
            else:
                characters.append(s)
        sequence = "".join(characters)
        if suffixes:
            sequence += "." + ".".join(suffixes)
        return sequence

    def _get_name_from_production_name(self, production_name):
        pass

with open("lab/input.txt") as f:
    names = f.read().splitlines()
gset = GlyphSet(names)
with open("lab/output.txt", "w") as f:
    f.write(gset.to_goadb(convert_to_production_name=False))
