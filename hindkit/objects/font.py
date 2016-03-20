#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

from hindkit.objects.base import BaseObject

class BaseFont(BaseObject):

    @staticmethod
    def postscript(name):
        return name.replace(' ', '')

    def __init__(self, family, name):

        super(BaseFont, self).__init__(name)

        self.family = family

        self.file_format = 'UFO'

        self._name_postscript = None
        self._full_name = None
        self._full_name_postscript = None

    @property
    def name_postscript(self):
        return self.fallback(self._name_postscript, postscript(self.name))
    @name_postscript.setter
    def name_postscript(self, value):
        self._name_postscript = value

    @property
    def full_name(self):
        return self.fallback(self._full_name, self.family.name + ' ' + self.name)
    @full_name.setter
    def full_name(self, value):
        self._full_name = value

    @property
    def full_name_postscript(self):
        return self.fallback(
            self._full_name_postscript,
            postscript(self.family.name) + '-' + self.name_postscript,
        )
    @full_name_postscript.setter
    def full_name_postscript(self, value):
        self._full_name_postscript = value

    def open(self):
        if os.path.exists(self.path):
            if self.file_format == 'UFO':
                print("Opening `{}`".format(self.path))
                return kit.defcon_patched.Font(self.path)
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


class Master(BaseFont):

    def __init__(self, family, name, weight_location=0):

        super(Master, self).__init__(family, name)
        self.abstract_directory = kit.constants.paths.MASTERS

        self.weight_location = weight_location

    @BaseFont.filename.getter
    def filename(self):
        '''According to Glyphs app's convention.'''
        return self.fallback(self._filename, self.family.name + '-' + self.name)

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
        source = kit.defcon_patched.Font(source_path)

        if target_dir:
            target_filename_pattern = '{}*-{}.ufo'.format(target_dir, self.name)
            target_paths = glob.glob(target_filename_pattern)
            if target_paths:
                target_path = target_paths[0]
            else:
                raise SystemExit("`{}` is missing.".format(target_filename_pattern))
            target = kit.defcon_patched.Font(target_path)
        else:
            target = self.open()

        if importing_names:
            new_names = set(importing_names)
        else:
            new_names = set(source.keys())

        existing_names = set(target.keys())
        new_names.difference_update(existing_names)
        new_names.difference_update(set(excluding_names))
        new_names = kit.tools.sort_glyphs(source.glyphOrder, new_names)

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
            source_name = kit.constants.misc.DERIVING_MAP[deriving_name]
            target.newGlyph(deriving_name)
            if source_name:
                target[deriving_name].width = target[source_name].width
            print('{} (from {})'.format(deriving_name, source_name), end=', ')
        print()

        self.save_as(target)


class Style(BaseFont):

    def __init__(
        self,
        family,
        name,
        weight_location = 0,
        weight_class = 400,
        is_bold = None,
        is_italic = None,
        is_oblique = None,
    ):

        super(Style, self).__init__(family, name)
        self._abstract_directory = None

        self.weight_location = weight_location
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

    @property
    def abstract_directory(self):
        return self.fallback(
            self._abstract_directory,
            os.path.join(kit.constants.paths.STYLES, self.name),
        )
    @abstract_directory.setter
    def abstract_directory(self, value):
        self._abstract_directory = value

    @BaseFont.filename.getter
    def filename(self):
        return self.fallback(self._filename, 'font')

    def produce(self, file_format='OTF'):
        return Product(self.family, self, file_format=file_format)


class Product(BaseFont):

    def __init__(self, family, style, file_format='OTF'):
        super(Product, self).__init__(family, style.name)
        self.file_format = file_format
        self.abstract_directory = kit.constants.paths.BUILD

    @BaseFont.filename.getter
    def filename(self):
        return self.fallback(self._filename, self.full_name_postscript)
