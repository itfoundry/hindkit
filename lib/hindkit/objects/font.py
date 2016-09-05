#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, glob, subprocess
import defcon, fontTools.ttLib
import hindkit as kit

def _insertAnchor(self, index, anchor):
    # try:
    #     assert anchor.glyph != self
    # except AttributeError:
    #     pass
    if not isinstance(anchor, self._anchorClass):
        anchor = self.instantiateAnchor(anchorDict=anchor)
    assert anchor.glyph in (self, None), "This anchor belongs to another glyph."
    if anchor.glyph is None:
        if anchor.identifier is not None:
            identifiers = self._identifiers
            assert anchor.identifier not in identifiers
            identifiers.add(anchor.identifier)
        anchor.glyph = self
        anchor.beginSelfNotificationObservation()
    self.beginSelfAnchorNotificationObservation(anchor)
    self._anchors.insert(index, anchor)
    self.postNotification(notification="Glyph.AnchorsChanged")
    self.dirty = True

defcon.Glyph.insertAnchor = _insertAnchor

class BaseFont(kit.BaseFile):

    @staticmethod
    def postscript(name):
        return name.replace(' ', '')

    def __init__(self, family, name, file_format='UFO', abstract_directory=''):

        super(BaseFont, self).__init__(
            name,
            file_format = file_format,
            abstract_directory = abstract_directory,
            family = family,
        )

        self._name_postscript = None
        self._full_name = None
        self._full_name_postscript = None

        self.font_in_memory = None

    @property
    def name_postscript(self):
        return kit.fallback(self._name_postscript, self.postscript(self.name))
    @name_postscript.setter
    def name_postscript(self, value):
        self._name_postscript = value

    @property
    def full_name(self):
        return kit.fallback(self._full_name, self.family.name + ' ' + self.name)
    @full_name.setter
    def full_name(self, value):
        self._full_name = value

    @property
    def full_name_postscript(self):
        return kit.fallback(
            self._full_name_postscript,
            self.postscript(self.family.name) + '-' + self.name_postscript,
        )
    @full_name_postscript.setter
    def full_name_postscript(self, value):
        self._full_name_postscript = value

    def open(self, from_disk=False):
        if not from_disk and self.font_in_memory:
            return self.font_in_memory
        else:
            if os.path.exists(self.path):
                if self.file_format == 'UFO':
                    print("\nOpening `{}`".format(self.path))
                    self.font_in_memory = defcon.Font(self.path)
                    return self.font_in_memory
                else:
                    raise SystemExit("`{}` is not supported by defcon.".format(self.path))
            else:
                raise SystemExit("`{}` is missing.".format(self.path))

    def save_temp(self, font=None, as_filename=None, temp=True):
        self.counter += 1
        if as_filename is None:
            self.filename = None
            self.filename += '--{}'.format(self.counter)
        else:
            self.filename = as_filename
        self.temp = temp
        if not font:
            font = self.font_in_memory
        print("\nSaving `{}`".format(self.path))
        font.save(self.path)

    def import_glyphs_from(
        self,
        source_path,
        target_dir = None,
        importing_names = None,
        excluding_names = None,
        import_kerning = False,
    ):

        if importing_names is None:
            importing_names = []
        if excluding_names is None:
            excluding_names = []

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
        new_names = (
            [i for i in source.glyphOrder if i in new_names] +
            [i for i in new_names if i not in source.glyphOrder]
        )

        print('\n[NOTE] Importing glyphs from `{}` to `{}`:'.format(source_path, self.name))
        for new_name in new_names:
            target.newGlyph(new_name)
            source_glyph = source[new_name]
            for component in source_glyph.components:
                if component.baseGlyph not in new_names:
                    source_glyph.decomposeComponent(component)
                    print("(decomposed {} in {})".format(component.baseGlyph, new_name), end=' ')
            target[new_name].copyDataFromGlyph(source_glyph)
            print(new_name, end=', ')
        print()

        if import_kerning:
            target.groups.update(source.groups)
            target.kerning.update(source.kerning)
            print("\n[NOTE] Imported kerning.")

    def derive_glyphs(self, deriving_names):

        if deriving_names is None:
            deriving_names = []

        target = self.open()

        print('\n[NOTE] Deriving glyphs in `{}`:'.format(self.name))
        for deriving_name in deriving_names:
            source_name = {
                'CR': 'space',
                'uni000D': 'space',
                'uni00A0': 'space',
                'NULL': None,
                'uni200B': None,
            }[deriving_name]
            target.newGlyph(deriving_name)
            if source_name:
                target[deriving_name].width = target[source_name].width
            print('{} (from {})'.format(deriving_name, source_name), end=', ')
        print()


class Master(BaseFont):

    def __init__(self, family, name, weight_location=0):

        super(Master, self).__init__(
            family,
            name,
            abstract_directory = kit.Project.directories['masters'],
        )
        self.weight_location = weight_location

    @BaseFont.filename.getter
    def filename(self):
        '''According to Glyphs app's convention.'''
        if self._filename is None:
            path_pattern = '{}/*{}.ufo'.format(self.directory, self.name)
            paths = glob.glob(path_pattern)
            if paths:
                self._filename = os.path.basename(paths[0]).partition('.')[0]
                return self._filename
            else:
                raise SystemExit("`{}` is missing.".format(path_pattern))
        else:
            return self._filename


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

        self.is_bold = kit.fallback(is_bold, 'Bold' in self.name.split())
        self.is_italic = kit.fallback(is_italic, 'Italic' in self.name.split())
        self.is_oblique = kit.fallback(is_oblique, 'Oblique' in self.name.split())

        # self.products = []

    @property
    def abstract_directory(self):
        return kit.fallback(
            self._abstract_directory,
            os.path.join('styles', self.name),
        )
    @abstract_directory.setter
    def abstract_directory(self, value):
        self._abstract_directory = value

    @BaseFont.filename.getter
    def filename(self):
        return kit.fallback(self._filename, 'font')

    def produce(self, project, file_format='OTF'):
        return Product(project, self, file_format=file_format)


class Product(BaseFont):

    def __init__(self, project, style, file_format='OTF'):

        self.style = style
        self.weight_location = self.style.weight_location
        self.weight_class = self.style.weight_class
        self.is_bold = self.style.is_bold
        self.is_italic = self.style.is_italic
        self.is_oblique = self.style.is_oblique

        super(Product, self).__init__(
            self.style.family,
            self.style.name,
            file_format = file_format,
            abstract_directory = kit.Project.directories['products'],
        )

        self.project = project

    @BaseFont.filename.getter
    def filename(self):
        return kit.fallback(self._filename, self.full_name_postscript)

    def prepare(self, project=None):
        if project:
            self.project = project
        self.generate()

    def generate(self):

        style = self.style

        if self.file_format == 'OTF':
            self.style.file_format = 'UFO'
            goadb = self.project.goadb_trimmed
        elif self.file_format == 'TTF':
            self.style.file_format = 'TTF'
            goadb = self.project.goadb_trimmed_ttf

        goadb.prepare(self.project.glyph_data.glyph_order_trimmed)

        while not os.path.exists(self.style.path):
            print(
                "\n[PROMPT] Input file {} is missing. Try again? [Y/n]: ".format(style.path),
                end = '',
            )
            if raw_input().upper().startswith('N'):
                return

        if self.style.file_format == 'UFO':
            font = self.style.open()
            i = font.info
            i.familyName = None
            i.styleName = None
            i.styleMapStyleName = None
            i.openTypeNamePreferredFamilyName = None
            i.openTypeNamePreferredSubfamilyName = None
            font.info.postscriptFontName = self.full_name_postscript
            font.save()

        arguments = [
            '-f', self.style.path,
            '-o', self.path,
            '-mf', self.project.fmndb.path,
            '-gf', goadb.path,
            '-rev', self.project.fontrevision,
            '-ga',
            '-omitMacNames',
        ]
        if not self.project.args.test:
            arguments.append('-r')
        if not self.project.options['run_autohint']:
            arguments.append('-shw')
        if self.project.options['do_style_linking']:
            if self.is_bold:
                arguments.append('-b')
            if self.is_italic:
                arguments.append('-i')
        if self.project.options['use_os_2_version_4']:
            for digit, boolean in [
                ('7', self.project.options['prefer_typo_metrics']),
                ('8', self.project.options['is_width_weight_slope_only']),
                ('9', self.is_oblique),
            ]:
                arguments.append('-osbOn' if boolean else '-osbOff')
                arguments.append(digit)

        subprocess.call(['makeotf'] + arguments)

        try:
            self.postprocess
        except AttributeError:
            pass
        else:
            if os.path.exists(self.path):
                original = fontTools.ttLib.TTFont(self.path)
                postprocessed = self.postprocess(original)
                if postprocessed:
                    postprocessed.save(self.path, reorderTables=False)

        destination = self.project.directories['output']
        if os.path.exists(self.path) and os.path.isdir(destination):
            kit.copy(self.path, destination)
