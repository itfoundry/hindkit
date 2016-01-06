#!/usr/bin/env AFDKOPython

import hindkit as kit

family = kit.Family(
    trademark = 'Hind Siliguri',
    script = 'Bangla',
    hide_script_name = True,
)
family.set_masters()
family.set_styles()

builder = kit.Builder(
    family,
    fontrevision = '1.000',
    options = [
        'run_makeinstances',
        'run_checkoutlines',
        'run_autohint',
        'do_style_linking',
        'use_os_2_version_4',
        'prefer_typo_metrics',
        'is_width_weight_slope_only',
    ],
)
builder.build()
