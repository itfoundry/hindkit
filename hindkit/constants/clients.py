#!/usr/bin/env AFDKOPython

from __future__ import division, absolute_import, print_function, unicode_literals

from . import styles

DEFAULT_CLIENT = 'googlefonts'

ITF = {
    'style_scheme': styles.ITF,
    'tables': {
        'name': [
            (0, "Copyright {} Indian Type Foundry. All rights reserved.".format(time.year)),
            (7, "{} is a trademark of the Indian Type Foundry.").format(self.family.trademark),
            (8, "Indian Type Foundry"),
            (9, self.family.designers),
            (10, self.family.description),
            (11, "http://www.indiantypefoundry.com"),
            (12, self.family.designer_url),
            (13, "This Font Software is protected under domestic and international trademark and copyright law. You agree to identify the ITF fonts by name and credit the ITF\'s ownership of the trademarks and copyrights in any design or production credits."),
            (14, "http://www.indiantypefoundry.com/licensing/eula/"),
            (19, INDIC_SCRIPTS[self.family.script]['sample text']),
        ],
        'OS/2': {
            'Vendor': 'ITFO'
        },
    },
}

GOOGLE_FONTS = {
    'style_scheme': styles.ITF_CamelCase,
    'tables': {
        'name': [
            (0, "Copyright (c) {} Indian Type Foundry (info@indiantypefoundry.com)".format(time.year)),
            (11, "http://www.indiantypefoundry.com/googlefonts"),
            (13, "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: http://scripts.sil.org/OFL"),
            (14, "http://scripts.sil.org/OFL"),
        ],
    },
}

IS_OUTSOURCING = False

def get_vendor_id(client):
    vendor_id = ITF['vendor_id']
    if IS_OUTSOURCING:
        vendor_id = client['vendor_id']
    return vendor_id
