#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, glob, subprocess
import defcon, fontTools.ttLib
import hindkit as kit

# defcon.Glyph.insertAnchor

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

# defcon.Glyph.insertAnchor = _insertAnchor


class BaseFont(kit.BaseFile):

    # makeInstancesUFO.updateInstance
    @staticmethod
    def _updateInstance(options, fontInstancePath):
        if options['doOverlapRemoval']:
            print("\tdoing overlap removal with checkOutlinesUFO %s ..." % (fontInstancePath))
            logList = []
            opList = ["-e", fontInstancePath]
            if options['allowDecimalCoords']:
                opList.insert(0, "-dec")
            if os.name == "nt":
                opList.insert(0, 'checkOutlinesUFO.cmd')
                proc = subprocess.Popen(opList, stdout=subprocess.PIPE)
            else:
                opList.insert(0, 'checkOutlinesUFO')
                proc = subprocess.Popen(opList, stdout=subprocess.PIPE)
            while 1:
                output = proc.stdout.readline()
                if output:
                    print(".", end=' ')
                    logList.append(output)
                if proc.poll() != None:
                    output = proc.stdout.readline()
                    if output:
                        print(output, end=' ')
                        logList.append(output)
                    break
            log = "".join(logList)
            if not ("Done with font" in log):
                print()
                print(log)
                print("Error in checkOutlinesUFO %s" % (fontInstancePath))
                # raise(SnapShotError)
            else:
                print()

        if options['doAutoHint']:
            print("\tautohinting %s ..." % (fontInstancePath))
            logList = []
            opList = ['-q', '-nb', fontInstancePath]
            if options['allowDecimalCoords']:
                opList.insert(0, "-dec")
            if os.name == "nt":
                opList.insert(0, 'autohint.cmd')
                proc = subprocess.Popen(opList, stdout=subprocess.PIPE)
            else:
                opList.insert(0, 'autohint')
                proc = subprocess.Popen(opList, stdout=subprocess.PIPE)
            while 1:
                output = proc.stdout.readline()
                if output:
                    print(output, end=' ')
                    logList.append(output)
                if proc.poll() != None:
                    output = proc.stdout.readline()
                    if output:
                        print(output, end=' ')
                        logList.append(output)
                    break
            log = "".join(logList)
            if not ("Done with font" in log):
                print()
                print(log)
                print("Error in autohinting %s" % (fontInstancePath))
                # raise(SnapShotError)
            else:
                print()

        return

    def __init__(
        self,
        family,
        name,
        file_format = 'UFO',
        abstract_directory = '',
        location = 0,
        weight_and_width_class = (400, 5),
    ):

        super(BaseFont, self).__init__(
            name,
            file_format = file_format,
            abstract_directory = abstract_directory,
            family = family,
        )

        if isinstance(location, tuple):
            self.location = location
        else:
            self.location = (location,)

        if isinstance(weight_and_width_class, tuple):
            self.weight_class, self.width_class = weight_and_width_class
        else:
            self.weight_class = weight_and_width_class
            self.width_class = 5

        self._name_postscript = None
        self._full_name = None
        self._full_name_postscript = None

        self.font_in_memory = None

    @property
    def name_postscript(self):
        return kit.fallback(self._name_postscript, self.name.replace(' ', ''))

    @property
    def full_name(self):
        return kit.fallback(self._full_name, self.family.name + ' ' + self.name)

    @property
    def full_name_postscript(self):
        return kit.fallback(
            self._full_name_postscript,
            self.family.name_postscript + '-' + self.name_postscript,
        )

    def open(self, from_disk=False):
        if not from_disk and self.font_in_memory:
            return self.font_in_memory
        else:
            if os.path.exists(self.get_path()):
                if self.file_format == 'UFO':
                    self.font_in_memory = defcon.Font(self.get_path())
                    print("[OPENED]", self.get_path())
                    return self.font_in_memory
                else:
                    raise SystemExit("`{}` is not supported by defcon.".format(self.get_path()))
            else:
                raise SystemExit("`{}` is missing.".format(self.get_path()))

    def save(self, defcon_font=None, as_filename=None):
        if not defcon_font:
            if self.font_in_memory:
                defcon_font = self.font_in_memory
            else:
                return
        self.counter += 1
        if as_filename is None:
            self._filename = None
            self._filename = self.filename + '--{}'.format(self.counter)
        else:
            self._filename = as_filename
        defcon_font.save(self.get_path())
        self.font_in_memory = None
        print("[SAVED]", self.get_path())

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
                'nonbreakingspace': 'space',
                'uni00A0': 'space',
                'NULL': None,
                'zerowidthspace': None,
                'uni200B': None,
            }[deriving_name]
            target.newGlyph(deriving_name)
            if source_name:
                target[deriving_name].width = target[source_name].width
            print('{} (from {})'.format(deriving_name, source_name), end=', ')


class Master(BaseFont):

    def __init__(self, family, name, location=0):

        super(Master, self).__init__(
            family,
            name,
            abstract_directory = kit.Project.directories['masters'],
            location = location,
        )

    @BaseFont.filename.getter
    def filename(self):
        '''According to the Glyphs app's convention.'''
        if self._filename is None:
            path_pattern = '{}/*-{}.ufo'.format(self.get_directory(temp=False), self.name)
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
        location = 0,
        weight_and_width_class = (400, 5),
    ):

        super(Style, self).__init__(
            family,
            name,
            location = location,
            weight_and_width_class = weight_and_width_class,
        )
        self.abstract_directory = os.path.join(kit.Project.directories['styles'], self.name)

        self.master = None
        self.dirty = False

        # self.products = []

    @BaseFont.filename.getter
    def filename(self):
        return kit.fallback(self._filename, 'font')

    def produce(self, project, file_format='OTF', subsidiary=False):
        return Product(project, self, file_format=file_format, subsidiary=subsidiary)


class Product(BaseFont):

    def __init__(self, project, style, file_format='OTF', subsidiary=False):

        self.style = style
        self.location = self.style.location
        self.weight_class = self.style.weight_class
        self.width_class = self.style.width_class

        super(Product, self).__init__(
            self.style.family,
            self.style.name,
            file_format = file_format,
            abstract_directory = kit.Project.directories['products'],
        )

        self.project = project
        self.subsidiary = subsidiary
        self.built = False

        name_parts = self.name.split(" ")
        self.is_bold = "Bold" in name_parts
        self.is_italic = "Italic" in name_parts
        self.is_oblique = "Oblique" in name_parts

        self._style_linking_family_name = None

    @BaseFont.filename.getter
    def filename(self):
        return kit.fallback(self._filename, self.full_name_postscript)

    @property
    def style_linking_family_name(self):
        return kit.fallback(self._style_linking_family_name, self.full_name)

    def generate(self):

        if self.file_format == 'OTF':

            goadb = self.project.goadb_trimmed

            if self.style.file_format == 'UFO':

                defcon_font = self.style.open()
                for i in """
                    versionMajor
                    versionMinor
                    copyright
                    familyName
                    styleName
                    styleMapFamilyName
                    styleMapStyleName
                    postscriptWeightName
                    openTypeHeadCreated
                    openTypeNamePreferredFamilyName
                    openTypeNamePreferredSubfamilyName
                    openTypeNameDesigner
                    openTypeOS2WeightClass
                    openTypeOS2WidthClass
                """.split():
                    setattr(defcon_font.info, i, None)
                defcon_font.groups.clear()
                defcon_font.kerning.clear()
                defcon_font.info.postscriptFontName = self.full_name_postscript
                self.style.save()

                if self.project.options['run_checkoutlines'] or self.project.options['run_autohint']:
                    options = {
                        'doOverlapRemoval': self.project.options['run_checkoutlines'],
                        'doAutoHint': self.project.options['run_autohint'],
                        'allowDecimalCoords': False,
                    }
                    self._updateInstance(options, self.style.get_path())

        elif self.file_format == 'TTF':

            goadb = self.project.goadb_trimmed_ttf

            subprocess.call([
                "osascript", "-l", "JavaScript",
                kit.relative_to_package("data/generate_ttf.js"),
                os.path.abspath(self.style.get_path()),
            ])

            self.style.file_format = 'TTF' #TODO: Should restore the original file format afterwards. Or the styles should just seperate.

            while not os.path.exists(self.style.get_path()):
                print(
                    "\n[PROMPT] Input file {} is missing. Try again? [Y/n]: ".format(self.style.get_path()),
                    end = '',
                )
                if raw_input().upper().startswith('N'):
                    return

        goadb.prepare()
        kit.makedirs(self.get_directory())

        arguments = [
            '-f', self.style.get_path(),
            '-o', self.get_path(),
            '-mf', self.project.fmndb.get_path(),
            '-gf', goadb.get_path(),
            '-rev', self.project.fontrevision,
            '-ga',
        ]
        if self.project.options['omit_mac_name_records']:
            arguments.append('-omitMacNames')
        if not self.project.args.test:
            arguments.append('-r')
        if not self.project.options['run_autohint']:
            arguments.append('-shw')
        if self.family.is_serif is not None:
            arguments.append('-serif' if self.family.is_serif else '-sans')
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

        if os.path.exists(self.get_path()):
            self.built = True
            print("[FONT SUCCESSFULLY BUILT]", self.get_path())
            try:
                self.postprocess
            except AttributeError:
                pass
            else:
                original = fontTools.ttLib.TTFont(self.get_path(), recalcTimestamp=True)
                postprocessed = self.postprocess(original)
                postprocessed.save(self.get_path(), reorderTables=False)
                print("[FONT POSTPROCESSED]", self.get_path())
