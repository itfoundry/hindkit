#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os
import defcon
import hindkit.constants, hindkit.tools, hindkit.patches

defcon.Glyph.insertAnchor = hindkit.patches.insertAnchor

class Family(object):

    default_client = hindkit.constants.clients.DEFAULT

    def __init__(
        self,
        client = None,
        trademark = '',
        script = '',
        append_script_name = False,
        name = '',
    ):

        if client:
            self.client = client
        else:
            self.client = self.default_client

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

    @hindkit.memoize
    def get_goadb(self):

        goadb = []

        if os.path.exists('glyphorder.txt'):

            glyphorder = []
            with open('glyphorder.txt') as f:
                for line in f:
                    line_without_comment = line.partition('#')[0].strip()
                    for development_name in line_without_comment.split():
                        glyphorder.append(development_name)

            U_SCALAR_TO_U_NAME = hindkit.constants.misc.get_u_scalar_to_u_name()

            AGLFN = hindkit.constants.misc.get_glyph_list('aglfn.txt')
            ITFGL = hindkit.constants.misc.get_glyph_list('itfgl.txt')
            ITFGL_PATCH = hindkit.constants.misc.get_glyph_list('itfgl_patch.txt')

            AL5 = hindkit.constants.misc.get_adobe_latin(5)

            D_NAME_TO_U_NAME = {}
            D_NAME_TO_U_NAME.update(AGLFN)
            D_NAME_TO_U_NAME.update(AL5)
            D_NAME_TO_U_NAME.update(ITFGL)
            D_NAME_TO_U_NAME.update(ITFGL_PATCH)

            U_NAME_TO_U_SCALAR = {v: k for k, v in U_SCALAR_TO_U_NAME.items()}
            AGLFN_REVERSED = {v: k for k, v in AGLFN.items()}

            PREFIXS = tuple(
                v['abbreviation']
                for v in hindkit.constants.misc.SCRIPTS.values()
            )

            PRESERVED_NAMES = 'NULL CR'.split()

            SPECIAL_D_NAME_TO_U_SCALAR = {
                'NULL': '0000',
                'CR': '000D',
            }

            with open(hindkit.constants.paths.GOADB, 'w') as f:

                for development_name in glyphorder:

                    u_scalar = None
                    u_mapping = None
                    production_name = None

                    u_name = D_NAME_TO_U_NAME.get(development_name)
                    if u_name:
                        u_scalar = U_NAME_TO_U_SCALAR[u_name]
                    else:
                        u_scalar = SPECIAL_D_NAME_TO_U_SCALAR.get(development_name)

                    if u_scalar:
                        form = 'uni{}' if (len(u_scalar) <= 4) else 'u{}'
                        u_mapping = form.format(u_scalar)

                    if u_name in AGLFN.values():
                        production_name = AGLFN_REVERSED[u_name]
                    elif (
                        development_name in PRESERVED_NAMES or
                        development_name.partition('.')[0].split('_')[0] in ITFGL
                    ):
                        production_name = development_name
                    elif u_mapping:
                        production_name = u_mapping
                    else:
                        production_name = development_name

                    row = production_name, development_name, u_mapping
                    f.write(' '.join(filter(None, row)) + '\n')
                    goadb.append(row)

        elif os.path.exists(hindkit.constants.paths.GOADB):
            with open(hindkit.constants.paths.GOADB) as f:
                for line in f:
                    line_without_comment = line.partition('#')[0].strip()
                    if line_without_comment:
                        row = line_without_comment.split()
                        if len(row) == 2:
                            row.append(None)
                        production_name, development_name, u_mapping = row
                        goadb.append(
                            (production_name, development_name, u_mapping)
                        )

        return goadb

    def set_masters(self, masters=None):
        if masters:
            self.masters = masters
        else:
            self.masters = [Master(self, 'Light', 0), Master(self, 'Bold', 100)]

    def set_styles(self, style_scheme=None):
        if not style_scheme:
            style_scheme = hindkit.constants.clients.Client(self).style_scheme
        self.styles = [
            Style(
                self,
                name = style_name,
                interpolation_value = interpolation_value,
                weight_class = weight_class,
            )
            for style_name, interpolation_value, weight_class in style_scheme
        ]
        if not self.masters:
            self.set_masters([
                Master(self, i.name, i.interpolation_value)
                for i in self.styles
            ])

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

        self.postprocess_counter = 0

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
            path = hindkit.tools.temp(path)
        if os.path.exists(path):
            print("Opening `{}`".format(path))
            return defcon.Font(path)
        else:
            raise SystemExit("`{}` is missing.".format(path))

    def update_glyph_order(self, order=None):
        if order is None:
            order = [i[1] for i in self._family.get_goadb()]
        target = self.open_font(is_temp=True)
        target.lib['public.glyphOrder'] = order
        if 'com.schriftgestaltung.glyphOrder' in target.lib:
            del target.lib['com.schriftgestaltung.glyphOrder']
        self.postprocess_counter += 1
        self._file_name = 'TEMP{}-{}.ufo'.format(self.postprocess_counter, self.name)
        hindkit.tools.remove_files(hindkit.tools.temp(self.path))
        target.save(hindkit.tools.temp(self.path))

class Master(_BaseStyle):

    @property
    def directory(self):
        return hindkit.constants.paths.MASTERS

    @property
    def file_name(self):
        if self._file_name:
            return self._file_name
        else:
            return '{}-{}.ufo'.format(self._family.name, self.name)

    def import_glyphs_from(
        self,
        source_dir,
        target_dir = None,
        importing_names = None,
        excluding_names = None,
    ):

        if importing_names is None:
            importing_names = []
        if excluding_names is None:
            excluding_names = []

        import glob

        source_file_name_pattern = '{}*-{}.ufo'.format(source_dir, self.name)
        source_paths = glob.glob(source_file_name_pattern)
        if source_paths:
            source_path = source_paths[0]
        else:
            raise SystemExit("`{}` is missing.".format(source_file_name_pattern))
        source = defcon.Font(source_path)

        if target_dir:
            target_file_name_pattern = '{}*-{}.ufo'.format(target_dir, self.name)
            target_paths = glob.glob(target_file_name_pattern)
            if target_paths:
                target_path = target_paths[0]
            else:
                raise SystemExit("`{}` is missing.".format(target_file_name_pattern))
            target = defcon.Font(target_path)
        else:
            target = self.open_font(is_temp=True)

        if importing_names:
            new_names = set(importing_names)
        else:
            new_names = set(source.keys())

        existing_names = set(target.keys())
        new_names.difference_update(existing_names)
        new_names.difference_update(set(excluding_names))
        new_names = hindkit.tools.sort_glyphs(source.glyphOrder, new_names)

        print('\n[NOTE] Importing glyphs from `{}` to `{}`:'.format(source_path, self.name))
        for new_name in new_names:
            target.newGlyph(new_name)
            target[new_name].copyDataFromGlyph(source[new_name])
            print(new_name, end=', ')
        print()

        self.postprocess_counter += 1
        self._file_name = 'TEMP{}-{}.ufo'.format(self.postprocess_counter, self.name)
        hindkit.tools.remove_files(hindkit.tools.temp(self.path))
        target.save(hindkit.tools.temp(self.path))

    def derive_glyphs(self, deriving_names):

        if deriving_names is None:
            deriving_names = []

        target = self.open_font(is_temp=True)

        print('\n[NOTE] Deriving glyphs in `{}`:'.format(self.name))
        for deriving_name in deriving_names:
            source_name = hindkit.constants.misc.DERIVING_MAP[deriving_name]
            target.newGlyph(deriving_name)
            if source_name:
                target[deriving_name].width = target[source_name].width
            print('{} (from {})'.format(deriving_name, source_name), end=', ')
        print()

        self.postprocess_counter += 1
        self._file_name = 'TEMP{}-{}.ufo'.format(self.postprocess_counter, self.name)
        hindkit.tools.remove_files(hindkit.tools.temp(self.path))
        target.save(hindkit.tools.temp(self.path))

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
        input_format = 'UFO',
        output_format = 'OTF',
        _output_full_name_postscript = None,
        _font_name = None,
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

        self.input_format = input_format
        self.output_format = output_format

        self._output_full_name_postscript = _output_full_name_postscript

        self._font_name = _font_name

    @property
    def directory(self):
        return os.path.join(hindkit.constants.paths.STYLES, self.name_postscript)

    @property
    def file_name(self):
        if self._file_name:
            file_name = self._file_name
        else:
            file_name = 'font' + '.' + self.input_format.lower()
        return file_name

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
    def font_name(self):
        if self._font_name:
            font_name = self._font_name
        else:
            font_name = self.output_full_name_postscript + '.' + self.output_format.lower()
        return font_name

    @property
    def font_path(self):
        return os.path.join(hindkit.constants.paths.BUILD, self.font_name)
