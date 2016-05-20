#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals
import collections
import pytoml

enum = collections.namedtuple

p = enum(
    "Property",
    """
        Vowel Consonant
        Stop Nasal Approximant Fricative
        Guttural Palatal Retroflex Dental Labial
        Voiced Aspirated
    """
)

class Letter(object):
    # IMPLICIT_PROPERTIES = {
    #     "Nasal": "Voiced",
    # }
    def __init__(self, name, properties):
        self.name = name
        self.properties = set(properties)
        # for k, v in self.IMPLICIT_PROPERTIES.items():
        #     if p.__dict__[k] in self.properties:
        #         self.properties.update(p.__dict__[i] for i in v.split())

    def __contains__(self, item):
        return item in self.properties

class Consonant(object):
    pass

DATA = """
    K:   Consonant Guttural Stop,
    KH:  Consonant Guttural Stop Aspirated,
    G:   Consonant Guttural Stop Voiced,
    GH:  Consonant Guttural Stop Voiced Aspirated,
    NG:  Consonant Guttural Nasal Voiced,

    C:   Consonant Palatal Stop,
    CH:  Consonant Palatal Stop Aspirated,
    J:   Consonant Palatal Stop Voiced,
    JH:  Consonant Palatal Stop Voiced Aspirated,
    NY:  Consonant Palatal Nasal Voiced,

    TT:  Consonant Retroflex Stop,
    TTH: Consonant Retroflex Stop Aspirated,
    DD:  Consonant Retroflex Stop Voiced,
    DDH: Consonant Retroflex Stop Voiced Aspirated,
    NN:  Consonant Retroflex Nasal Voiced,

    T:   Consonant Dental Stop,
    TH:  Consonant Dental Stop Aspirated,
    D:   Consonant Dental Stop Voiced,
    DH:  Consonant Dental Stop Voiced Aspirated,
    N:   Consonant Dental Nasal Voiced,

    P:   Consonant Labial Stop,
    PH:  Consonant Labial Stop Aspirated,
    B:   Consonant Labial Stop Voiced,
    BH:  Consonant Labial Stop Voiced Aspirated,
    M:   Consonant Labial Nasal Voiced,

    Y:   Consonant Approximant Voiced Palatal,
    R:   Consonant Approximant Voiced Retroflex,
    L:   Consonant Approximant Voiced Dental,
    V:   Consonant Approximant Voiced Labial,

    SH:  Consonant Fricative Palatal,
    SS:  Consonant Fricative Retroflex,
    S:   Consonant Fricative Dental,
    H:   Consonant Fricative Voiced Guttural,
"""
for item in DATA.split(",")[:-1]:
    name, _, properties = item.partition(":")
    name = name.strip()
    properties = properties.split()
    Consonant.__setattr__(name, Letter(name, (p.__getattr__(i) for i in properties)))
    Consonant.list.append(Consonant.__getattr__(name))

print(l.__dict__)
