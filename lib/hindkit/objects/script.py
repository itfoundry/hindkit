#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import hindkit as kit

class Script(object):
    def __init__(
        self,
        name,
        abbreviation,
        tags,
        aliases = None,
        sample_text = None,
        is_indic = False,
    ):
        self.name = name
        self.abbreviation = abbreviation
        self.tags = tags
        self.aliases = kit.fallback(aliases, [])
        self.sample_text = sample_text
        self.is_indic = is_indic
