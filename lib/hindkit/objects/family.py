#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, subprocess
import defcon, mutatorMath.ufo.document
import hindkit as kit

class Family(object):

    def __init__(
        self,
        name = None,
        trademark = None,
        name_stem = None,
        script_name = None,
        append_script_name = False,
        client_name = None,
        variant_tag = None,
        initial_release_year = None,
    ):

        self.trademark = trademark
        self.name_stem = kit.fallback(name_stem, self.trademark)
        self.script = kit.constants.SCRIPT_NAMES_TO_SCRIPTS.get(script_name)
        if name:
            self.name = name
        else:
            self.name = self.name_stem
            if script_name and append_script_name:
                self.name += ' ' + script_name
        self.name_postscript = self.name.replace(' ', '')

        self.masters = None
        self.styles = None

        self.info = defcon.Font().info

        self.client_name = client_name
        self.variant_tag = variant_tag
        self.initial_release_year = initial_release_year

    def get_client_data(self):
        return kit.Client(self, self.client_name)

    def set_masters(self, value=None):
        scheme = kit.fallback(value, [('Light', 0), ('Bold',  100)])
        self.masters = [
            kit.Master(self, name, weight_location)
            for name, weight_location in scheme
        ]

    def set_styles(self, value=None):
        scheme = kit.fallback(value, self.get_client_data().style_scheme)
        self.styles = [
            kit.Style(self, name, weight_location, weight_class)
            for name, weight_location, weight_class in scheme
        ]
        if self.masters is None:
            self.set_masters((i.name, i.weight_location) for i in self.styles)
        else:
            for master in self.masters:
                for style in self.styles:
                    if style.weight_location == master.weight_location:
                        style.master = master
                        break

    def _has_kerning(self):
        raise NotImplementedError()

    def _has_mark_positioning(self):
        raise NotImplementedError()

    def _has_mI_variants(self):
        raise NotImplementedError()

    def prepare_styles(self):

        p = self.project
        styles = [i.style for i in p.products if not i.incidental]
        for style in styles:
            style.temp = True
            kit.makedirs(style.directory)

        if p.options['run_makeinstances']:
            self.generate_styles()
        else:
            for style in styles:
                kit.copy(style.master.path, style.path)
                style.open().info.postscriptFontName = style.full_name_postscript
                style.dirty = True

        for style in styles:
            try:
                style.postprocess()
                style.dirty = True
            except AttributeError:
                pass
            style.save_temp()

    def generate_styles(self):

        p = self.project
        p.designspace.prepare()

        arguments = ['-d', p.designspace.path]
        if not p.options['run_checkoutlines']:
            arguments.append('-c')
        if not p.options['run_autohint']:
            arguments.append('-a')

        subprocess.call(['makeInstancesUFO'] + arguments)


class DesignSpace(kit.BaseFile):

    def __init__(self, project, name='font'):
        super(DesignSpace, self).__init__(
            name,
            project = project,
            file_format = 'DesignSpace',
        )

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

                self.lines.append('')
                self.lines.append('[{}]'.format(product.full_name_postscript))
                self.lines.append('  f = {}'.format(f_name))
                self.lines.append('  s = {}'.format(product.name))

                l_name = product.full_name
                comment_lines = []

                if self.project.options['do_style_linking']:
                    if product.name == 'Regular':
                        l_name = l_name.replace(' Regular', '')
                    else:
                        if product.is_bold:
                            comment_lines.append('  # IsBoldStyle')
                            l_name = l_name.replace(' Bold', '')
                        if product.is_italic:
                            comment_lines.append('  # IsItalicStyle')
                            l_name = l_name.replace(' Italic', '')

                if l_name != f_name:
                    self.lines.append('  l = {}'.format(l_name))

                self.lines.extend(comment_lines)

        with open(self.path, 'w') as f:
            f.writelines(i + '\n' for i in self.lines)
