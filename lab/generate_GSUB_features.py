#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import collections, re
import hindkit as k
from generate_GOADB import Glyph

DO_HACK_FOR_CORE_TEXT = True

DO_OUTPUT_INDIC1 = True
DO_OUTPUT_INDIC2 = True
DO_OUTPUT_USE = True

PREFIX = "dv"

def indent(line):
    return "  " + line

def comment(line):
    return "# " + line

def add_prefix(name):
    return PREFIX + name

def remove_prefix(name):
    if name.startswith("dv"):
        name = name[2:]
    return name

class Font(object):

    def __init__(self):
        self.features = collections.OrderedDict()

    def add_feature(self, tag):
        self.features[tag] = Feature(tag)

    def dump(self):
        lines = []
        for f in self.features.values():
            lines.extend(f.dump())
        return lines

    @property
    def lookups(self):
        lookups = collections.OrderedDict()
        for k, v in self.features.items():
            for k, v in v.lookups.items():
                lookups[k] = v
        return lookups

class Feature(object):

    def __init__(self, tag):
        self.tag = tag
        self.lookups = collections.OrderedDict()

    def register_lookup(self, label):
        self.lookups[label] = Lookup(label)

    def dump(self):
        lines = []
        lines.append("feature {} {{".format(self.tag))
        for l in self.lookups.values():
            lines.extend(map(indent, l.dump()))
        lines.append("}} {};".format(self.tag))
        return lines

class Lookup(object):

    def __init__(self, label, determinate = False):
        self.label = label
        self.determinate = determinate
        self.rules = []

    def add_rule(self, input_components, output_components, text=None, is_commented=False):
        self.rules.append(Rule(input_components, output_components, text=text, is_commented=is_commented))
        rule = self.rules[-1]
        # return rule

    def dump(self):
        lines = []
        lines.append("lookup {} {{".format(self.label))
        lines.extend([indent(r.dump()) for r in self.rules])
        lines.append("}} {};".format(self.label))
        if not self.rules:
            lines = map(comment, lines)
        return lines

class Rule(object):

    def __init__(self, input_components, output_components, text=None, is_commented=False):
        self.input_components = input_components
        self.output_components = output_components
        self._text = text
        self.is_commented = is_commented

    @property
    def text(self):
        if self._text is None:
            text = "sub {} by {};".format(
                " ".join(self.input_components),
                " ".join(self.output_components),
            )
        else:
            text = self._text
        return text

    @property
    def is_empty(self):
        is_empty = False
        if not self.input_components:
            is_empty = True
        return is_empty

    def dump(self):
        dump = self.text
        if self.is_empty:
            dump = " ".join(self.output_components)
            self.is_commented = True
        if self.is_commented:
            dump = "# " + dump
        return dump

PLAIN_CONSONANTS_LETTERS = [i + "A" for i in k.constants.CONSONANT_STEMS]
AKHAND_LIGATURES = ["K_SSA", "J_NYA"]

BASIC_FORMS = PLAIN_CONSONANTS_LETTERS + AKHAND_LIGATURES

NUKTA_FORMS = [i + "xA" for i in k.constants.CONSONANT_STEMS]

RAKAR_FORMS = [i[:-1] + "_RA" for i in BASIC_FORMS]
RAKAR_NUKTA_FORMS = [i[:-1] + "_RA" for i in NUKTA_FORMS]

HALF_FORMS = [i[:-1] for i in BASIC_FORMS]
HALF_NUKTA_FORMS = [i[:-1] for i in NUKTA_FORMS]
HALF_RAKAR_FORMS = [i[:-1] for i in RAKAR_FORMS]
HALF_RAKAR_NUKTA_FORMS = [i[:-1] for i in RAKAR_NUKTA_FORMS]

CANONICAL_FORMED_GLYPHS = BASIC_FORMS + NUKTA_FORMS + RAKAR_FORMS + RAKAR_NUKTA_FORMS + HALF_FORMS + HALF_NUKTA_FORMS + HALF_RAKAR_FORMS + HALF_RAKAR_NUKTA_FORMS

def get_components(name, mode="indic2"):
    g = Glyph(name)
    global PREFIX
    PREFIX = g.prefix
    stem = g.stem
    input_pieces = g.stem_pieces
    suffixes = g.suffixes
    components = input_pieces
    lookup = None
    if PREFIX != "dv":
        pass
    elif suffixes != [""]:
        pass
    elif stem == "Reph":
        lookup = "rphf"
        components = ["RA", "Virama"]
    elif stem == "RAc2":
        if mode == "indic2":
            lookup = "blwf_new"
            components = ["Virama", "RA"]
        elif mode == "indic1":
            lookup = "blwf_old"
            components = ["RA", "Virama"]
    elif stem == "Eyelash":
        lookup = "akhn_eyelash"
        components = ["RA'", "Virama'", "zerowidthjoiner"]
    elif stem in PLAIN_CONSONANTS_LETTERS:
        pass
    elif stem in AKHAND_LIGATURES:
        lookup = "akhn"
        if stem == "K_SSA":
            components = ["KA", "Virama", "SSA"]
        elif stem == "J_NYA":
            components = ["JA", "Virama", "NYA"]
    elif stem in NUKTA_FORMS:
        lookup = "nukt"
        components = [stem[:-2] + "A", "Nukta"]
    elif stem in HALF_FORMS + HALF_NUKTA_FORMS:
        lookup = "half"
        components = [stem + "A", "Virama"]
    elif stem in RAKAR_FORMS + RAKAR_NUKTA_FORMS:
        if mode == "indic2":
            lookup = "rkrf_new"
            components = [stem[:-3] + "A", "Virama", "RA"]
        elif mode == "indic1":
            lookup = "vatu_old"
            components = [stem[:-3] + "A", "RAc2"]
    elif stem in HALF_RAKAR_FORMS + HALF_RAKAR_NUKTA_FORMS:
        if mode == "indic2":
            lookup = "half_new"
            components = [stem + "A", "Virama"]
        elif mode == "indic1":
            lookup = "vatu_old"
            components = [stem[:-2], "RAc2"]
    components = map(add_prefix, components)
    return components, lookup

def ligate(components, reference):
    output = [components[0]]
    for a in components[1:]:
        b = output[-1]
        b_a = b + "_" + a
        if b_a in reference:
            output.pop()
            output.append(b_a)
        else:
            output.append(a)
    return output

def generate_cjct(components, formed_glyphs):

    is_cjct = False
    output = []

    for a in components:

        is_different = False
        if "dv" + a not in formed_glyphs:
            if a in RAKAR_FORMS + RAKAR_NUKTA_FORMS + HALF_FORMS + HALF_NUKTA_FORMS + HALF_RAKAR_FORMS + HALF_RAKAR_NUKTA_FORMS:
                if not is_cjct:
                    is_cjct = True
                    output = {
                        "cjct_new": output[:],
                        "pres_old": output[:],
                    }
                if a in HALF_FORMS + HALF_NUKTA_FORMS:
                    extension = [a + "A", "Virama"]
                elif a in RAKAR_FORMS + RAKAR_NUKTA_FORMS:
                    extension = [a[:-3] + "A", "RAc2"]
                elif a in HALF_RAKAR_FORMS + HALF_RAKAR_NUKTA_FORMS:
                    is_different = True
                    if "dv" + a + "A" in formed_glyphs:
                        extension_indic2 = [a + "A", "Virama"]
                    else:
                        extension_indic2 = [a[:-2] + "A", "RAc2", "Virama"]
                    if "dv" + a[:-2] in formed_glyphs:
                        extension_indic1 = [a[:-2], "RAc2"]
                    else:
                        extension_indic1 = [a[:-2] + "A", "Virama", "RAc2"]
            else:
                extension = [a]
        else:
            extension = [a]

        if is_different:
            extension_cjct_new = extension_indic2
            extension_pres_old = extension_indic1
        else:
            extension_cjct_new = extension
            extension_pres_old = extension

        if is_cjct:
            output["cjct_new"].extend(extension_cjct_new)
            output["pres_old"].extend(extension_pres_old)
        else:
            output.extend(extension)

    return is_cjct, output
