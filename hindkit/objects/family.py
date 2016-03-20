#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import defcon

import hindkit as kit

class Family(object):

    def __init__(
        self,
        client = None,
        trademark = None,
        script = None,
        append_script_name = False,
        name = None,
    ):

        self.client = client

        self.trademark = trademark
        self.script = script
        self.append_script_name = append_script_name

        if name:
            self.name = name
        else:
            self.name = self.trademark
            if self.script and self.append_script_name:
                self.name += ' ' + self.script
        self.name_postscript = self.name.replace(' ', '')

        self.masters = []
        self.styles = []

        self.info = defcon.Font().info

    def set_masters(self, masters=None):
        if masters:
            self.masters = masters
        else:
            self.masters = [kit.Master(self, 'Light', 0), kit.Master(self, 'Bold', 100)]

    def set_styles(self, style_scheme=None):
        if not style_scheme:
            style_scheme = kit.clients.Client(self).style_scheme
        self.styles = [
            kit.Style(
                self,
                name = style_name,
                weight_location = weight_location,
                weight_class = weight_class,
            )
            for style_name, weight_location, weight_class in style_scheme
        ]
        if not self.masters:
            self.set_masters([
                kit.Master(self, i.name, i.weight_location)
                for i in self.styles
            ])

    def get_styles_that_are_directly_derived_from_masters(self):
        master_positions = [
            master.weight_location for master in self.masters
        ]
        styles_that_are_directly_derived_from_masters = []
        for style in self.styles:
            if style.weight_location in master_positions:
                styles_that_are_directly_derived_from_masters.append(style)
        return styles_that_are_directly_derived_from_masters

    def _has_kerning(self):
        raise NotImplementedError()

    def _has_mark_positioning(self):
        raise NotImplementedError()

    def _has_mI_variants(self):
        raise NotImplementedError()


class Fmndb(kit.BaseObject):

    LINES_HEAD = [
        '# [PostScriptName]',
        '#   f = Preferred Family Name',
        '#   s = Subfamily/Style Name',
        '#   l = Compatible Family Menu Name (Style-Linking Family Name)',
        '#   m = 1, Macintosh Compatible Full Name (Deprecated)',
    ]

    def __init__(self, builder, name='FontMenuNameDB'):
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
