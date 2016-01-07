#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import hindkit as kit

family = kit.Family(
    client = 'Google Fonts',
    trademark = 'Hind Siliguri',
    script = 'Bangla',
)
family.set_masters()
family.set_styles()

builder = kit.Builder(
    family,
    fontrevision = '0.100',
    options = {
        'override_GDEF': True,
        'do_style_linking': True,
    },
)
builder.build()
