#!/usr/bin/env AFDKOPython

import hindkit as kit

family = kit.Family(
    trademark = 'Hind Siliguri',
    script = 'Bangla',
    hide_script_name = True,
)
# family.set_masters()
# family.set_styles()

builder = kit.Builder(
    family,
    fontrevision = '1.000',
    options = {
        'do_style_linking': True,
    },
)
builder.build()
