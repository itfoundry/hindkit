#!/usr/bin/env AFDKOPython
# encoding: UTF-8

import collections
import pytoml

DATA = """
    K:   consonant+ stop  velar voiced- aspirated-,
    KH:  consonant+ stop  velar voiced- aspirated+,
    G:   consonant+ stop  velar voiced+ aspirated-,
    GH:  consonant+ stop  velar voiced+ aspirated+,
    NG:  consonant+ nasal velar voiced+ aspirated-,

    C:   consonant+ stop  palatal voiced- aspirated-,
    CH:  consonant+ stop  palatal voiced- aspirated+,
    J:   consonant+ stop  palatal voiced+ aspirated-,
    JH:  consonant+ stop  palatal voiced+ aspirated+,
    NY:  consonant+ nasal palatal voiced+ aspirated-,

    TT:  consonant+ stop  retroflex voiced- aspirated-,
    TTH: consonant+ stop  retroflex voiced- aspirated+,
    DD:  consonant+ stop  retroflex voiced+ aspirated-,
    DDH: consonant+ stop  retroflex voiced+ aspirated+,
    NN:  consonant+ nasal retroflex voiced+ aspirated-,

    T:   consonant+ stop  dental voiced- aspirated-,
    TH:  consonant+ stop  dental voiced- aspirated+,
    D:   consonant+ stop  dental voiced+ aspirated-,
    DH:  consonant+ stop  dental voiced+ aspirated+,
    N:   consonant+ nasal dental voiced+ aspirated-,

    P:   consonant+ stop  labial voiced- aspirated-,
    PH:  consonant+ stop  labial voiced- aspirated+,
    B:   consonant+ stop  labial voiced+ aspirated-,
    BH:  consonant+ stop  labial voiced+ aspirated+,
    M:   consonant+ nasal labial voiced+ aspirated-,

    Y:   consonant+ approximant palatal   voiced+ aspirated-,
    R:   consonant+ approximant retroflex voiced+ aspirated-,
    L:   consonant+ approximant dental    voiced+ aspirated-,
    V:   consonant+ approximant labial    voiced+ aspirated-,

    SH:  consonant+ fricative palatal   voiced- aspirated+,
    SS:  consonant+ fricative retroflex voiced- aspirated+,
    S:   consonant+ fricative dental    voiced- aspirated+,
    H:   consonant+ fricative glottal   voiced+ aspirated+,
"""



class Letter(object):
    PROPERTIES = {
        "is_consonant": [True, False],
        "manner": ["stop", "nasal", "approximant", "fricative"],
        "place": ["velar", "palatal", "retroflex", "dental", "labial", "glottal"],
        "is_voiced": [True, False],
        "is_aspirated": [True, False],
    }
    def __init__(self, name, property_literals):
        self.name = name
        self.letter_enum = None
        for i in property_literals:
            property_name = None
            property_value = None
            if i.endswith(("-", "+")):
                property_name = "is_" + i[:-1]
                property_value = bool(("-", "+").index(i[-1:]))
            else:
                for k, v in self.PROPERTIES.items():
                    if i in v:
                        property_name = k
                        property_value = i
                        break
            if property_name:
                setattr(self, property_name, property_value)
    def same(self, property_names):
        for l in self.letter_enum.letters:
            if all(
                getattr(l, n) == getattr(self, n)
                for n in property_names
            ):
                yield l
    def free(self, property_names):
        for l in self.letter_enum.letters:
            if all(
                getattr(l, n) != getattr(self, n)
                for n in property_names
            ):
                yield l

class LetterEnum(object):
    def __init__(self, letters):
        self.letters = letters
        self._letter_dict = {}
        for l in self.letters:
            l.letter_enum = self
            self._letter_dict[l.name] = l
    def __getattr__(self, name):
        return self._letter_dict[name]

letters = []
for item in DATA.split(",")[:-1]:
    name, _, property_record = item.partition(":")
    letters.append(Letter(name.strip(), property_record.split()))
Consonant = LetterEnum(letters)
c = Consonant

with open("lab/output.txt", "w") as f:

    for c2 in c.letters:

        f.write(c2.name + "A" + "\n")

        c1_list = set()

        if c2.manner == "stop":
            c1_list.update(
                i for i in c2.free("is_aspirated".split())
                if not i.is_aspirated
            )
            c1_list.update(
                i for i in c2.same("place".split())
                if i.manner == "nasal"
            )
        # else:
        #     c1_list.add(c2)

        # if (p.stop in c2 and p.voiced in c2) or p.nasal in c2:
        #     c1_list.update(
        #         c.get(
        #             (c2.properties & properties("velar palatal retroflex dental labial")) | properties("fricative")
        #         )
        #     )

        if c2 in [c.Y, c.R, c.V]:
            c1_list.update(c.letters)

        c1_list.discard(c.R)

        for c1 in (i for i in c.letters if i in c1_list):
            f.write(c1.name + "_" + c2.name + "A" + "\n")

        f.write("\n")
