#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import datetime, collections
from . import styles, misc

DEFAULT = 'Google Fonts'

class Client(object):

    def __init__(self, family):

        self.family = family

        DATA = {
            'ITF': {
                'info': {
                    'style_scheme': styles.ITF,
                },
                'table_name': collections.OrderedDict([
                    (0, "Copyright {} Indian Type Foundry. All Rights Reserved.".format(datetime.date.today().year)),
                    (7, "{} is a trademark of the Indian Type Foundry.".format(self.family.trademark)),
                    (8, "Indian Type Foundry"),
                    (9, self.family.designers),
                    (10, self.family.description),
                    (11, "http://www.indiantypefoundry.com"),
                    (12, self.family.designer_url),
                    (13, "This Font Software is protected under domestic and international trademark and copyright law. You agree to identify the ITF fonts by name and credit the ITF\'s ownership of the trademarks and copyrights in any design or production credits."),
                    (14, "http://www.indiantypefoundry.com/licensing/eula/"),
                    (19, misc.SCRIPTS[self.family.script.lower()]['sample text']),
                ]),
                'table_OS_2': {
                    'Vendor': 'ITFO'
                },
            },
            'Google Fonts': {
                'info': {
                    'style_scheme': styles.ITF_CamelCase,
                },
                'table_name': collections.OrderedDict([
                    (0, "Copyright (c) {} Indian Type Foundry (info@indiantypefoundry.com)".format(datetime.date.today().year)),
                    (11, "http://www.indiantypefoundry.com/googlefonts"),
                    (13, "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: http://scripts.sil.org/OFL"),
                    (14, "http://scripts.sil.org/OFL"),
                ]),
            },
            'Samsung': {
                'info': {
                    'style_scheme': styles.DUAL,
                },
                'table_name': collections.OrderedDict([
                    (0, "Copyright {} Samsung Electronics Co., Ltd. All Rights Reserved.".format(datetime.date.today().year)),
                    (7, "{} is a trademark of Samsung Electronics Co., Ltd.".format(self.family.trademark)),
                    (9, "Indian Type Foundry"),
                ]),
            },
        }

        DEFAULT = DATA['ITF']
        CURRENT = DATA[self.family.client]

        self.info = DEFAULT['info']
        self.info.update(CURRENT.get('info', {}))

        self.style_scheme = self.info['style_scheme']

        self.table_name = DEFAULT['table_name']
        self.table_name.update(CURRENT.get('table_name', {}))

        self.table_OS_2 = DEFAULT['table_OS_2']
        self.table_OS_2.update(CURRENT.get('table_OS/2', {}))
