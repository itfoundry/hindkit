#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import datetime, collections
import hindkit as kit

class Client(object):

    def __init__(self, family):

        self.family = family

        self.DATA = {
            'ITF': {
                'info': {
                    'style_scheme': kit.styles.ITF,
                    'vertical_metrics_strategy': 'ITF',
                },
                'table_name': collections.OrderedDict([
                    (
                        0,
                        kit.fallback(
                            self.family.info.copyright,
                            "Copyright {} Indian Type Foundry. All Rights Reserved.".format(datetime.date.today().year),
                        )
                    ),
                    (7, "{} is a trademark of the Indian Type Foundry.".format(self.family.base_name)),
                    (8, "Indian Type Foundry"),
                    (9, self.family.info.openTypeNameDesigner),
                    (10, self.family.info.openTypeNameDescription),
                    (11, "http://www.indiantypefoundry.com"),
                    (12, self.family.info.openTypeNameDesignerURL),
                    (13, "This Font Software is protected under domestic and international trademark and copyright law. You agree to identify the ITF fonts by name and credit the ITF\'s ownership of the trademarks and copyrights in any design or production credits."),
                    (14, "http://www.indiantypefoundry.com/licensing/eula/"),
                    (19, self.family.script.sample_text),
                ]),
                'table_OS_2': {
                    'fsType': kit.fallback(self.family.info.openTypeOS2Type, 4),
                    'Vendor': 'ITFO'
                },
            },
        }

        self.expand_data()

        DEFAULT = self.DATA['ITF']
        CURRENT = self.DATA[self.family.client]

        self.info = DEFAULT['info']
        self.info.update(CURRENT.get('info', {}))

        self.style_scheme = self.info['style_scheme']
        self.vertical_metrics_strategy = self.info['vertical_metrics_strategy']

        self.table_name = DEFAULT['table_name']
        self.table_name.update(CURRENT.get('table_name', {}))

        self.table_OS_2 = DEFAULT['table_OS_2']
        self.table_OS_2.update(CURRENT.get('table_OS_2', {}))

    def expand_data(self):
        self.DATA['Google Fonts'] = {
            'info': {
                'style_scheme': kit.styles.ITF_CamelCase,
                'vertical_metrics_strategy': 'Google Fonts',
            },
            'table_name': collections.OrderedDict([
                (
                    0,
                    kit.fallback(
                        self.family.info.copyright,
                        "Copyright (c) {} Indian Type Foundry (info@indiantypefoundry.com)".format(datetime.date.today().year),
                    )
                ),
                (7, None),
                (11, "http://www.indiantypefoundry.com/googlefonts"),
                (13, "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: http://scripts.sil.org/OFL"),
                (14, "http://scripts.sil.org/OFL"),
            ]),
            'table_OS_2': {
                'fsType': 0,
            },
        }
