#! /usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals
import hindkit as kit

family = kit.Family(
    base_name = "Hind",
    script_name = "Devanagari",
    client_name = "Google Fonts",
)
family.set_masters()
family.set_styles()

project = kit.Project(
    family,
    fontrevision = "0.100",
    options = {
        "prepare_mark_positioning": True,
        "match_mI_variants": "single",
        "position_marks_for_mI_variants": True,
        # "build_ttf": True,
        # "do_style_linking": True,
        # "use_os_2_version_4": True,
        # "prefer_typo_metrics": True,
        # "is_width_weight_slope_only": True,
    },
)
project.build()
