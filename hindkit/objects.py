#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, re, sys, collections

from hindkit import constants, patches

def fallback(*candidates):
    # if len(candidates) == 1 and isinstance(candidates[0], collections.Iterable):
    #     candidates = candidates[0]
    for i in candidates:
        if i is not None:
            return i

def postscript(name):
    return name.replace(' ', '')


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
            self.masters = [Master(self, 'Light', 0), Master(self, 'Bold', 100)]

    def set_styles(self, style_scheme=None):
        if not style_scheme:
            style_scheme = constants.clients.Client(self).style_scheme
        self.styles = [
            Style(
                self,
                name = style_name,
                weight_location = weight_location,
                weight_class = weight_class,
            )
            for style_name, weight_location, weight_class in style_scheme
        ]
        if not self.masters:
            self.set_masters([
                Master(self, i.name, i.weight_location)
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

    def _has_kerning(self): # TODO
        pass

    def _has_mark_positioning(self): # TODO
        pass

    def _has_mI_variants(self): # TODO
        pass


class _BaseFont(object):

    def __init__(self, family, name):

        self.family = family
        self.name = name

        self.file_format = 'UFO'
        self.abstract_directory = None
        self.temp = False

        self._name_postscript = None
        self._full_name = None
        self._full_name_postscript = None
        self._extension = None
        self._filename = None
        self._directory = None
        self._path = None

        self.counter = 0

    @property
    def name_postscript(self):
        return fallback(self._name_postscript, postscript(self.name))
    @name_postscript.setter
    def name_postscript(self, value):
        self._name_postscript = value

    @property
    def full_name(self):
        return fallback(self._full_name, self.family.name + ' ' + self.name)
    @full_name.setter
    def full_name(self, value):
        self._full_name = value

    @property
    def full_name_postscript(self):
        return fallback(
            self._full_name_postscript,
            postscript(self.family.name) + '-' + self.name_postscript,
        )
    @full_name_postscript.setter
    def full_name_postscript(self, value):
        self._full_name_postscript = value

    @property
    def extension(self):
        return fallback(self._extension, self.file_format.lower())
    @extension.setter
    def extension(self, value):
        self._extension = value

    @property
    def filename(self):
        return fallback(self._filename, self.name)
    @filename.setter
    def filename(self, value):
        self._filename = value

    @property
    def directory(self):
        directory = self.abstract_directory
        if self.temp:
            directory = os.path.join(constants.paths.TEMP, directory)
        return fallback(
            self._directory,
            directory,
        )
    @directory.setter
    def directory(self, value):
        self._directory = value

    @property
    def path(self):
        filename = self.filename
        if self.extension:
            filename += '.' + self.extension
        return fallback(
            self._path,
            os.path.join(self.directory, filename),
        )
    @path.setter
    def path(self, value):
        self._path = value

    def prepare(self, builder, *args, **kwargs):
        path = self.path
        if os.path.exists(path):
            if not self.temp:
                self.temp = True
                copy(path, self.path)
        else:
            self.temp = True
            try:
                self.generate(builder, *args, **kwargs)
            except AttributeError:
                raise SystemExit("Can't generate {}.".format(self.path))

    # def generate(builder, self):
    #     pass

    def open(self):
        if os.path.exists(self.path):
            if self.file_format == 'UFO':
                print("Opening `{}`".format(self.path))
                return defcon.Font(self.path)
            else:
                raise SystemExit("`{}` is not supported by defcon.".format(self.path))
        else:
            raise SystemExit("`{}` is missing.".format(self.path))

    def save_as(self, font, temp=True):
        self.counter += 1
        self.filename = None
        self.filename += '--{}'.format(self.counter)
        self.temp = temp
        font.save(self.path)


class Master(_BaseFont):

    def __init__(self, family, name, weight_location=0):

        _BaseFont.__init__(self, family, name)
        self.abstract_directory = constants.paths.MASTERS

        self.weight_location = weight_location

    @_BaseFont.filename.getter
    def filename(self):
        '''According to Glyphs app's convention.'''
        return fallback(self._filename, self.family.name + '-' + self.name)

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

        source_filename_pattern = '{}*-{}.ufo'.format(source_dir, self.name)
        source_paths = glob.glob(source_filename_pattern)
        if source_paths:
            source_path = source_paths[0]
        else:
            raise SystemExit("`{}` is missing.".format(source_filename_pattern))
        source = defcon.Font(source_path)

        if target_dir:
            target_filename_pattern = '{}*-{}.ufo'.format(target_dir, self.name)
            target_paths = glob.glob(target_filename_pattern)
            if target_paths:
                target_path = target_paths[0]
            else:
                raise SystemExit("`{}` is missing.".format(target_filename_pattern))
            target = defcon.Font(target_path)
        else:
            target = self.open()

        if importing_names:
            new_names = set(importing_names)
        else:
            new_names = set(source.keys())

        existing_names = set(target.keys())
        new_names.difference_update(existing_names)
        new_names.difference_update(set(excluding_names))
        new_names = tools.sort_glyphs(source.glyphOrder, new_names)

        print('\n[NOTE] Importing glyphs from `{}` to `{}`:'.format(source_path, self.name))
        for new_name in new_names:
            target.newGlyph(new_name)
            target[new_name].copyDataFromGlyph(source[new_name])
            print(new_name, end=', ')
        print()

        self.save_as(target)

    def derive_glyphs(self, deriving_names):

        if deriving_names is None:
            deriving_names = []

        target = self.open()

        print('\n[NOTE] Deriving glyphs in `{}`:'.format(self.name))
        for deriving_name in deriving_names:
            source_name = constants.misc.DERIVING_MAP[deriving_name]
            target.newGlyph(deriving_name)
            if source_name:
                target[deriving_name].width = target[source_name].width
            print('{} (from {})'.format(deriving_name, source_name), end=', ')
        print()

        self.save_as(target)


class Style(_BaseFont):

    def __init__(
        self,
        family,
        name,
        weight_location = 0,
        weight_class = 400,
        is_bold = None,
        is_italic = None,
        is_oblique = None,
        _output_full_name_postscript = None,
    ):

        _BaseFont.__init__(self, family, name)
        self._abstract_directory = None

        self.weight_location = weight_location

        self.full_name = family.name + ' ' + self.name
        self.full_name_postscript = family.name_postscript + '-' + self.name_postscript

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

    @property
    def abstract_directory(self):
        return fallback(
            self._abstract_directory,
            os.path.join(constants.paths.STYLES, self.name),
        )
    @abstract_directory.setter
    def abstract_directory(self, value):
        self._abstract_directory = value

    @_BaseFont.filename.getter
    def filename(self):
        return fallback(self._filename, 'font')

    def produce(self, file_format='OTF'):
        return Product(self.family, self, file_format=file_format)


class Product(_BaseFont):

    def __init__(self, family, style, file_format='OTF'):
        _BaseFont.__init__(self, family, style.name)
        self.file_format = file_format
        self.abstract_directory = constants.paths.BUILD

    @_BaseFont.filename.getter
    def filename(self):
        return fallback(self._filename, self.full_name_postscript)


class GlyphData(object):

    @staticmethod
    def normalize(lines):
        for line in lines:
            yield '\t'.join(line.partition('#')[0].split())

    @classmethod
    def patch(cls, dictionary):
        ITFDG = []
        for glyph in ITFDG:
            dictionary.add(glyph, priority=3)
        return dictionary

    def __init__(self, glyph_order_path='glyphorder.txt', goadb_path='GlyphOrderAndAliasDB'):

        self.glyph_order_path = glyph_order_path

        self.goadb_path = goadb_path
        self.goadb_path_trimmed = tools.temp(self.goadb_path + '_trimmed')
        self.goadb_path_trimmed_ttf = tools.temp(self.goadb_path + '_trimmed_ttf')

        self.name_order = []

        self.production_names = []
        self.development_names = []
        self.u_mappings = []

        with open(relative_to_interpreter('../SharedData/AGD.txt'), 'rU') as f:
            self.agd_dictionary = agd.dictionary(f.read())

        self.itfgd_dictionary = self.patch(self.agd_dictionary)

    def generate_name_order(self):
        for section in self.name_order_raw:
            if is_agd():
                self.name_order.extend(agd.cfforder(section))
            else:
                self.name_order.extend(section)


    def generate(self, reference_font):

        goadb = []

        if os.path.exists('glyphorder.txt'):

            self.goadb_path = tools.temp(self.goadb_path)

            glyphorder = []
            with open('glyphorder.txt') as f:
                for line in self.normalize(f):
                    for development_name in line.split():
                        glyphorder.append(development_name)

            U_SCALAR_TO_U_NAME = constants.misc.get_u_scalar_to_u_name()

            AGLFN = constants.misc.get_glyph_list('aglfn.txt')
            ITFGL = constants.misc.get_glyph_list('itfgl.txt')
            ITFGL_PATCH = constants.misc.get_glyph_list('itfgl_patch.txt')

            AL5 = constants.misc.get_adobe_latin(5)

            D_NAME_TO_U_NAME = {}
            D_NAME_TO_U_NAME.update(AGLFN)
            D_NAME_TO_U_NAME.update(AL5)
            D_NAME_TO_U_NAME.update(ITFGL)
            D_NAME_TO_U_NAME.update(ITFGL_PATCH)

            U_NAME_TO_U_SCALAR = {v: k for k, v in U_SCALAR_TO_U_NAME.items()}
            AGLFN_REVERSED = {v: k for k, v in AGLFN.items()}

            PREFIXS = tuple(
                v['abbreviation']
                for v in constants.misc.SCRIPTS.values()
            )

            PRESERVED_NAMES = 'NULL CR'.split()

            SPECIAL_D_NAME_TO_U_SCALAR = {
                'NULL': '0000',
                'CR': '000D',
            }

            u_mapping_pattern = re.compile(r'uni([0-9A-F]{4})|u([0-9A-F]{5,6})$')

            tools.make_dir(constants.paths.TEMP)

            with open(self.goadb_path, 'w') as f:

                for development_name in glyphorder:

                    u_scalar = None
                    u_mapping = None
                    production_name = None

                    match = u_mapping_pattern.match(development_name)
                    if match:
                        u_scalar = filter(None, match.groups())[0]
                        u_name = U_SCALAR_TO_U_NAME[u_scalar]
                    else:
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

        else:
            with open(self.path) as f:
                for line in self.normalize(f):
                    row = line.split()
                    if len(row) == 2:
                        row.append(None)
                    production_name, development_name, u_mapping = row
                    goadb.append(
                        (production_name, development_name, u_mapping)
                    )

    def output_trimmed(self, reference_font, build_ttf=False):
        DIFFERENCES = {
            'CR CR uni000D\n': 'CR uni000D uni000D\n',
        }
        not_covered_glyphs = [
            glyph.name
            for glyph in reference_font
            if glyph.name not in self.development_names
        ]
        if not_covered_glyphs:
            raise SystemExit(
                'Some glyphs are not covered by the GOADB: ' +
                ' '.join(not_covered_glyphs)
            )
        else:
            trimmed = open(self.path_trimmed, 'w')
            if build_ttf:
                trimmed_ttf = open(self.path_trimmed_ttf, 'w')
            for row in self.table:
                if row.development_name in reference_font:
                    line = ' '.join(filter(None, row)) + '\n'
                    trimmed.write(line)
                    if build_ttf:
                        line_ttf = DIFFERENCES.get(line, line)
                        trimmed_ttf.write(line_ttf)
            trimmed.close()
            if build_ttf:
                trimmed_ttf.close()

# class DesignSpace(_BaseObject):
#     pass
