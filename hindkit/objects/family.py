#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, subprocess
import defcon, mutatorMath.ufo.document
import hindkit as kit

class Family(kit.Base):

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

    def set_masters(self, value=None):
        scheme = self.fallback(value, [('Light', 0), ('Bold',  100)])
        self.masters = [
            kit.Master(self, name, weight_location)
            for name, weight_location in scheme
        ]

    def set_styles(self, value=None):
        scheme = self.fallback(value, kit.Client(self).style_scheme)
        self.styles = [
            kit.Style(self, name, weight_location, weight_class)
            for name, weight_location, weight_class in scheme
        ]
        if self.masters is None:
            self.set_masters((i.name, i.weight_location) for i in self.styles)

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

    def prepare_styles(self):

        b = self.project
        styles = [product.style for product in b.products]
        for style in styles:
            style.temp = True
            kit.makedirs(style.directory)

        if b.options['run_makeinstances']:
            self.generate_styles()
        else:
            for master, style in zip(self.masters, styles):
                kit.copy(master.path, style.path)
                font = style.open()
                font.info.postscriptFontName = style.full_name_postscript
                if font.dirty:
                    font.save()
                if b.options['run_checkoutlines'] or b.options['run_autohint']:
                    options = {
                        'doOverlapRemoval': b.options['run_checkoutlines'],
                        'doAutoHint': b.options['run_autohint'],
                        'allowDecimalCoords': False,
                    }
                    _updateInstance(options, style.path)

    def generate_styles(self):

        b = self.project
        b.designspace.prepare()

        arguments = ['-d', b.designspace.path]
        if not b.options['run_checkoutlines']:
            arguments.append('-c')
        if not b.options['run_autohint']:
            arguments.append('-a')

        subprocess.call(['makeInstancesUFO'] + arguments)


class DesignSpace(kit.BaseFile):

    def __init__(self, project, name='font'):
        super(DesignSpace, self).__init__(name, project=project)
        self.file_format = 'DesignSpace'

    def generate(self):

        doc = mutatorMath.ufo.document.DesignSpaceDocumentWriter(
            os.path.abspath(kit.relative_to_cwd(self.path))
        )

        for i, master in enumerate(self.project.family.masters):

            doc.addSource(

                path = os.path.abspath(kit.relative_to_cwd(master.path)),
                name = 'master ' + master.name,
                location = {'weight': master.weight_location},

                copyLib    = i == 0,
                copyGroups = i == 0,
                copyInfo   = i == 0,

                # muteInfo = False,
                # muteKerning = False,
                # mutedGlyphNames = None,

            )

        for product in self.project.products:
            if product.file_format == 'OTF':
                style = product.style
                doc.startInstance(
                    name = 'instance ' + style.name,
                    location = {'weight': style.weight_location},
                    familyName = self.project.family.name,
                    styleName = style.name,
                    fileName = os.path.abspath(
                        kit.relative_to_cwd(style.path)
                    ),
                    postScriptFontName = style.full_name_postscript,
                    # styleMapFamilyName = None,
                    # styleMapStyleName = None,
                )
                doc.writeInfo()
                if self.project.options['prepare_kerning']:
                    doc.writeKerning()
                doc.endInstance()
        doc.save()


class Fmndb(kit.BaseFile):

    LINES_HEAD = [
        '# [PostScriptName]',
        '#   f = Preferred Family Name',
        '#   s = Subfamily/Style Name',
        '#   l = Compatible Family Menu Name (Style-Linking Family Name)',
        '#   m = 1, Macintosh Compatible Full Name (Deprecated)',
    ]

    def __init__(self, project, name='FontMenuNameDB'):
        super(Fmndb, self).__init__(name, project=project)
        self.lines = []
        self.lines.extend(self.LINES_HEAD)

    def generate(self):

        f_name = self.project.family.name

        for product in self.project.products:

            if product.file_format == 'OTF':

                style = product.style

                self.lines.append('')
                self.lines.append('[{}]'.format(style.full_name_postscript))
                self.lines.append('  f = {}'.format(f_name))
                self.lines.append('  s = {}'.format(style.name))

                l_name = style.full_name
                comment_lines = []

                if self.project.options['do_style_linking']:
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
