#!/usr/bin/env AFDKOPython

import hindkit as kit
kit.confirm_version('1.0.0')

# - - -

family = kit.family.Family(
    trademark = 'Hind',
    script = 'Bangla',
    # hide_script_name = True,
)

family.set_masters(
    modules = [
        'kerning',
        'mark_positioning',
        'mark_to_mark_positioning',
        # 'devanagari_matra_i_variants',
    ],
)

family.set_styles()

# - - -

builder = kit.builder.Builder(
    family,
    fontrevision = '1.000',
    options = [
        'run_makeinstances', #!
        'run_checkoutlines', #!
        'run_autohint',      #!
        'do_style_linking',
        'use_os_2_version_4',
        'prefer_typo_metrics',
        'is_width_weight_slope_only',
    ],
)

builder.build()
