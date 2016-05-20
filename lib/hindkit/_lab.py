#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals
import collections
import pytoml

DATA = """
    K:   Consonant Velar Stop Voiceless Unaspirated,
    KH:  Consonant Velar Stop Voiceless Aspirated,
    G:   Consonant Velar Stop Voiced Unaspirated,
    GH:  Consonant Velar Stop Voiced Aspirated,
    NG:  Consonant Velar Nasal Voiced Unaspirated,

    C:   Consonant Palatal Stop Voiceless Unaspirated,
    CH:  Consonant Palatal Stop Voiceless Aspirated,
    J:   Consonant Palatal Stop Voiced Unaspirated,
    JH:  Consonant Palatal Stop Voiced Aspirated,
    NY:  Consonant Palatal Nasal Voiced Unaspirated,

    TT:  Consonant Retroflex Stop Voiceless Unaspirated,
    TTH: Consonant Retroflex Stop Voiceless Aspirated,
    DD:  Consonant Retroflex Stop Voiced Unaspirated,
    DDH: Consonant Retroflex Stop Voiced Aspirated,
    NN:  Consonant Retroflex Nasal Voiced Unaspirated,

    T:   Consonant Dental Stop Voiceless Unaspirated,
    TH:  Consonant Dental Stop Voiceless Aspirated,
    D:   Consonant Dental Stop Voiced Unaspirated,
    DH:  Consonant Dental Stop Voiced Aspirated,
    N:   Consonant Dental Nasal Voiced Unaspirated,

    P:   Consonant Labial Stop Voiceless Unaspirated,
    PH:  Consonant Labial Stop Voiceless Aspirated,
    B:   Consonant Labial Stop Voiced Unaspirated,
    BH:  Consonant Labial Stop Voiced Aspirated,
    M:   Consonant Labial Nasal Voiced Unaspirated,

    Y:   Consonant Approximant Voiced Palatal Unaspirated,
    R:   Consonant Approximant Voiced Retroflex Unaspirated,
    L:   Consonant Approximant Voiced Dental Unaspirated,
    V:   Consonant Approximant Voiced Labial Unaspirated,

    SH:  Consonant Fricative Voiceless Palatal Aspirated,
    SS:  Consonant Fricative Voiceless Retroflex Aspirated,
    S:   Consonant Fricative Voiceless Dental Aspirated,
    H:   Consonant Fricative Voiced Aspirated,
"""

class Enum(object):
    def __init__(self, case_names, case_values=None):
        if not case_values:
            case_values = case_names
        for name, value in zip(case_names, case_values):
            setattr(self, name, value)

Property = Enum("""
    Vowel Consonant
    Stop Nasal Approximant Fricative
    Velar Palatal Retroflex Dental Labial
    Voiceless Voiced Unaspirated Aspirated
""".split())

def properties(names):
    if isinstance(names, unicode):
        names = names.split()
    return set(getattr(Property, name) for name in names)

class Letter(object):
    def __init__(self, name, properties_names):
        self.name = name
        self.properties = properties(properties_names)
    def __contains__(self, item):
        return item in self.properties

class LetterEnum(Enum):
    def __init__(self, letter_names, letters):
        super(LetterEnum, self).__init__(letter_names, letters)
        self.letters = letters
    def get(self, is_=set(), not_=set()):
        letters = []
        for l in self.letters:
            if l.properties >= is_ - not_ and \
            l.properties.isdisjoint(not_):
                letters.append(l)
        return letters

case_names = []
case_values = []
for item in DATA.split(",")[:-1]:
    name, _, properties_names = item.partition(":")
    name = name.strip()
    properties_names = properties_names.split()
    case_names.append(name)
    case_values.append(Letter(name, properties_names))
Consonant = LetterEnum(case_names, case_values)

c = Consonant
p = Property

with open("temp/output.txt", "w") as f:

    for c2 in c.letters:

        f.write(c2.name + "A" + "\n")

        c1_list = set()

        if p.Stop in c2:
            c1_list.update(
                c.get(
                    is_ = c2.properties,
                    not_ = properties("Aspirated"),
                )
            )
            c1_list.update(
                c.get(
                    (c2.properties & properties("Velar Palatal Retroflex Dental Labial")) | properties("Nasal")
                )
            )
        else:
            c1_list.add(c2)

        if (p.Stop in c2 and p.Voiceless in c2) or p.Nasal in c2:
            c1_list.update(
                c.get(
                    (c2.properties & properties("Velar Palatal Retroflex Dental Labial")) | properties("Fricative")
                )
            )

        if c2 in [c.Y, c.R, c.V]:
            c1_list.update(c.letters)

        c1_list.discard(c.R)

        for c1 in (i for i in c.letters if i in c1_list):
            f.write(c1.name + "_" + c2.name + "A" + "\n")

        f.write("\n")
