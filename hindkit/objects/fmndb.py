#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

from hindkit.objects.base import BaseObject

class Fmndb(BaseObject):

    LINES_HEAD = [
        '# [PostScriptName]',
        '#   f = Preferred Family Name',
        '#   s = Subfamily/Style Name',
        '#   l = Compatible Family Menu Name (Style-Linking Family Name)',
        '#   m = 1, Macintosh Compatible Full Name (Deprecated)',
    ]

    def __init__(self, builder):
        name = kit.constants.paths.FMNDB
        super(FeatureFile, self).__init__(name)
        self.builder = builder
        self.lines = []
        self.lines.extend(LINES_HEAD)

    def generate(self):

        f_name = self.builder.family.name

        for style in self.builder.styles_to_produce:

            self.lines.append('')
            self.lines.append('[{}]'.format(style.full_name_postscript))
            self.lines.append('  f = {}'.format(f_name))
            self.lines.append('  s = {}'.format(style.name))

            l_name = style.full_name
            comment_lines = []

            if self.builder.options['do_style_linking']:
                if style.name == 'Regular':
                    l_name = l_name.replace(' Regular', '')
                else:
                    if style.is_bold:
                        comment_lines.append('  # IsBoldStyle')
                        l_name = l_name.replace(' Bold', '')
                    if style.is_italic:
                        comment_lines.append('  # IsItalicStyle')
                        l_name = l_name.replace(' Italic', '')

            if l_name != f_name:
                self.lines.append('  l = {}'.format(l_name))

            self.lines.extend(comment_lines)

        with open(self.path, 'w') as f:
            f.writelines(i + '\n' for i in self.lines)
