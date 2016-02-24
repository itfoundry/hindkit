#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os
import defcon
import hindkit.constants as constants

class Family(object):

    default_client = constants.clients.DEFAULT

    def __init__(
        self,
        client = None,
        trademark = '',
        script = '',
        append_script_name = False,
    ):

        if client:
            self.client = client
        else:
            self.client = self.default_client

        self.trademark = trademark
        self.script = script
        self.append_script_name = append_script_name

        self.name = self.trademark
        if self.script and self.append_script_name:
            self.name += ' ' + self.script
        self.name_postscript = self.name.replace(' ', '')

        self.output_name_affix = '{}'

        self.masters = []
        self.styles = []

        info_host = defcon.Font()
        self.info = info_host.info

    @property
    def output_name(self):
        return self.output_name_affix.format(self.name)

    @property
    def output_name_postscript(self):
        return self.output_name.replace(' ', '')

    @property
    def goadb(self):

        goadb = []

        try:
            with open(constants.paths.GOADB, 'r') as file:
                goadb_content = file.read()
        except IOError:
            goadb.append((None, None, None))
            return goadb

        for line in goadb_content.splitlines():
            content = line.partition('#')[0].strip()
            if content:
                row = content.split()
                if len(row) == 2:
                    production_name, development_name = row
                    unicode_mapping = None
                elif len(row) == 3:
                    production_name, development_name, unicode_mapping = row
                goadb.append((production_name, development_name, unicode_mapping))

        return goadb

    def set_masters(self, masters = []):
        self.masters = masters
        if not self.masters:
            self.masters = [Master(self, 'Light', 0), Master(self, 'Bold', 100)]

    def set_styles(self, style_scheme = []):

        if not style_scheme:
            style_scheme = constants.clients.Client(self).style_scheme

        for style_name, interpolation_value, weight_class in style_scheme:
            style = Style(
                self,
                name = style_name,
                interpolation_value = interpolation_value,
                weight_class = weight_class,
            )
            self.styles.append(style)

    def get_styles_that_are_directly_derived_from_masters(self):
        master_positions = [
            master.interpolation_value for master in self.masters
        ]
        styles_that_are_directly_derived_from_masters = []
        for style in self.styles:
            if style.interpolation_value in master_positions:
                styles_that_are_directly_derived_from_masters.append(style)
        return styles_that_are_directly_derived_from_masters

    def _has_kerning(self): # TODO
        pass

    def _has_mark_positioning(self): # TODO
        pass

    def _has_mI_variants(self): # TODO
        pass

class _BaseStyle(object):

    def __init__(
        self,
        _family,
        name = 'Regular',
        interpolation_value = 0,
        _file_name = None,
    ):
        self._family = _family
        self.name = name
        self.interpolation_value = interpolation_value
        self._file_name = _file_name

    @property
    def directory(self):
        return ''

    @property
    def file_name(self):
        if self._file_name:
            return self._file_name
        else:
            return ''

    @property
    def path(self):
        return os.path.join(self.directory, self.file_name)

    def open_font(self, is_temp=False):
        path = self.path
        if is_temp:
            path = os.path.join(constants.paths.TEMP, path)
        return defcon.Font(path)

class Master(_BaseStyle):

    @property
    def directory(self):
        return constants.paths.MASTERS

    @property
    def file_name(self):
        if self._file_name:
            return self._file_name
        else:
            return '{}-{}.ufo'.format(self._family.name, self.name)

class Style(_BaseStyle):

    def __init__(
        self,
        _family,
        name = 'Regular',
        interpolation_value = 0,
        weight_class = 400,
        is_bold = None,
        is_italic = None,
        is_oblique = None,
        _output_full_name_postscript = None,
        _otf_name = None,
    ):

        super(Style, self).__init__(_family, name, interpolation_value)

        self.name_postscript = self.name.replace(' ', '')

        self.full_name = _family.name + ' ' + self.name
        self.full_name_postscript = _family.name_postscript + '-' + self.name_postscript

        self.weight_class = weight_class

        self.is_bold = is_bold
        self.is_italic = is_italic
        self.is_oblique = is_oblique
        if is_bold is None:
            self.is_bold = True if 'Bold' in self.name.split() else False
        if is_italic is None:
            self.is_italic = True if 'Italic' in self.name.split() else False
        if is_oblique is None:
            self.is_oblique = True if 'Oblique' in self.name.split() else False

        self._output_full_name_postscript = _output_full_name_postscript

        self._otf_name = _otf_name

    @property
    def directory(self):
        return os.path.join(constants.paths.STYLES, self.name_postscript)

    @property
    def file_name(self):
        if self._file_name:
            return self._file_name
        else:
            return 'font.ufo'

    @property
    def output_full_name(self):
        output_full_name = self._family.output_name + ' ' + self.name
        return output_full_name

    @property
    def output_full_name_postscript(self):
        if self._output_full_name_postscript:
            output_full_name_postscript = self._output_full_name_postscript
        else:
            output_full_name_postscript = self._family.output_name_postscript + '-' + self.name_postscript
        return output_full_name_postscript

    @property
    def otf_name(self):
        if self._otf_name:
            otf_name = self._otf_name
        else:
            otf_name = self.output_full_name_postscript + '.otf'
        return otf_name

    @property
    def otf_path(self):
        return os.path.join(constants.paths.BUILD, self.otf_name)
