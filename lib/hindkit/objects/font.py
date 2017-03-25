#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, glob, subprocess
import fontTools.ttLib
import hindkit as kit

class BaseFont(kit.BaseFile):

    def __init__(
        self,
        family,
        name,
        file_format = "UFO",
        abstract_directory = "",
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

        self.defconFont = None

    @property
    def name_postscript(self):
        return kit.fallback(self._name_postscript, self.name.replace(" ", ""))

    @property
    def full_name(self):
        return kit.fallback(self._full_name, self.family.name + " " + self.name)

    @property
    def full_name_postscript(self):
        return kit.fallback(
            self._full_name_postscript,
            self.family.name_postscript + "-" + self.name_postscript,
        )

    def open(self, from_disk=False):
        if not from_disk and self.defconFont:
            return self.defconFont
        else:
            if os.path.exists(self.get_path()):
                if self.file_format == "UFO":
                    self.defconFont = kit.patched.defcon.Font(self.get_path())
                    print("[OPENED]", self.get_path())
                    return self.defconFont
                else:
                    raise SystemExit("`{}` is not supported by defcon.".format(self.get_path()))
            else:
                raise SystemExit("`{}` is missing.".format(self.get_path()))

    def save(self, defconFont=None, as_filename=None):
        if not defconFont:
            if self.defconFont:
                defconFont = self.defconFont
            else:
                return
        self.counter += 1
        if as_filename is None:
            self._filename = None
            self._filename = self.filename + "--{}".format(self.counter)
        else:
            self._filename = as_filename
        defconFont.save(self.get_path())
        self.defconFont = None
        print("[SAVED]", self.get_path())

    def import_glyphs_from(
        self,
        source_path,
        target_dir = None,
        importing_names = None,
        excluding_names = None,
        import_kerning = False,
        renaming_dict = None,
    ):

        if importing_names is None:
            importing_names = []
        if excluding_names is None:
            excluding_names = []
        if renaming_dict is None:
            renaming_dict = {}

        source = kit.patched.defcon.Font(source_path)

        if target_dir:
            target_filename_pattern = "{}*-{}.ufo".format(target_dir, self.name)
            target_paths = glob.glob(target_filename_pattern)
            if target_paths:
                target_path = target_paths[0]
            else:
                raise SystemExit("`{}` is missing.".format(target_filename_pattern))
            target = kit.patched.defcon.Font(target_path)
        else:
            target = self.open()

        if importing_names:
            names_imported = set(importing_names)
        else:
            names_imported = set(source.keys())

        names_imported.difference_update(set(target.keys()))
        names_imported.difference_update(set(excluding_names))
        names_imported = (
            [i for i in source.glyphOrder if i in names_imported] +
            [i for i in names_imported if i not in source.glyphOrder]
        )

        print("\n[NOTE] Importing glyphs from `{}` to `{}`:".format(source_path, self.name))
        for name_source in names_imported:
            name_target = renaming_dict.get(name_source, name_source)
            target.newGlyph(name_target)
            source_glyph = source[name_source]
            for component in source_glyph.components:
                if component.baseGlyph not in names_imported:
                    source_glyph.decomposeComponent(component)
                    print("(decomposed {} in {})".format(component.baseGlyph, name_source), end=" ")
            target[name_target].copyDataFromGlyph(source_glyph)
            if name_target == name_source:
                print(name_target, end=", ")
            else:
                print("{} -> {}".format(name_source, name_target), end=", ")

        if import_kerning:
            target.groups.update(source.groups)
            target.kerning.update(source.kerning)
            print("\n[NOTE] Imported kerning.")

    def derive_glyphs(self, deriving_names):

        DERIVED_NAME_TO_SOURCE_NAME = {
            derived_name: source_name
            for source_name, derived_names in kit.constants.DERIVABLE_GLYPHS.items()
            for derived_name in derived_names
        }

        if deriving_names is None:
            deriving_names = []

        target = self.open()

        print("\n[NOTE] Deriving glyphs in `{}`:".format(self.name))
        for deriving_name in deriving_names:
            source_name = DERIVED_NAME_TO_SOURCE_NAME[deriving_name]
            target.newGlyph(deriving_name)
            if source_name:
                target[deriving_name].width = target[source_name].width
            print("{} -> {}".format(source_name, deriving_name), end=", ")


class Master(BaseFont):

    def __init__(self, family, name, location=0):

        super(Master, self).__init__(
            family,
            name,
            abstract_directory = kit.Project.directories["masters"],
            location = location,
        )

    @BaseFont.filename.getter
    def filename(self):
        """According to the Glyphs app's convention."""
        if self._filename is None:
            path_pattern = "{}/*-{}.ufo".format(self.get_directory(temp=False), self.name)
            paths = glob.glob(path_pattern)
            if paths:
                self._filename = os.path.basename(paths[0]).partition(".")[0]
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
        self.abstract_directory = os.path.join(kit.Project.directories["styles"], self.name)

        self.master = None
        self.dirty = False

        # self.products = []

    @BaseFont.filename.getter
    def filename(self):
        return kit.fallback(self._filename, "font")

    def produce(self, project, file_format="OTF", subsidiary=False):
        return Product(project, self, file_format=file_format, subsidiary=subsidiary)


class Product(BaseFont):

    def __init__(self, project, style, file_format="OTF", subsidiary=False):

        self.style = style
        self.location = self.style.location
        self.weight_class = self.style.weight_class
        self.width_class = self.style.width_class

        super(Product, self).__init__(
            self.style.family,
            self.style.name,
            file_format = file_format,
            abstract_directory = kit.Project.directories["products"],
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

        if self.file_format == "OTF":

            goadb = self.project.goadb_trimmed

            if self.style.file_format == "UFO":

                defconFont = self.style.open()
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
                    setattr(defconFont.info, i, None)
                defconFont.groups.clear()
                defconFont.kerning.clear()
                defconFont.info.postscriptFontName = self.full_name_postscript
                self.style.save()

                if self.project.options["run_checkoutlines"] or self.project.options["run_autohint"]:
                    options = {
                        "doOverlapRemoval": self.project.options["run_checkoutlines"],
                        "doAutoHint": self.project.options["run_autohint"],
                        "allowDecimalCoords": False,
                    }
                    kit.patched.updateInstance(options, self.style.get_path())

        elif self.file_format == "TTF":

            goadb = self.project.goadb_trimmed_ttf

            subprocess.call([
                "osascript", "-l", "JavaScript",
                kit.relative_to_package("data/generate_ttf.js"),
                os.path.abspath(self.style.get_path()),
            ])

            self.style.file_format = "TTF" #TODO: Should restore the original file format afterwards. Or the styles should just seperate.

            while not os.path.exists(self.style.get_path()):
                print(
                    "\n[PROMPT] Input file {} is missing. Try again? [Y/n]: ".format(self.style.get_path()),
                    end = "",
                )
                if raw_input().upper().startswith("N"):
                    return

        goadb.prepare()
        kit.makedirs(self.get_directory())

        arguments = [
            "-f", self.style.get_path(),
            "-o", self.get_path(),
            "-mf", self.project.fmndb.get_path(),
            "-gf", goadb.get_path(),
            "-rev", self.project.fontrevision,
            "-ga",
        ]
        if self.project.options["omit_mac_name_records"]:
            arguments.append("-omitMacNames")
        if not self.project.args.test:
            arguments.append("-r")
        if not self.project.options["run_autohint"]:
            arguments.append("-shw")
        if self.family.is_serif is not None:
            arguments.append("-serif" if self.family.is_serif else "-sans")
        if self.project.options["do_style_linking"]:
            if self.is_bold:
                arguments.append("-b")
            if self.is_italic:
                arguments.append("-i")
        if self.project.options["use_os_2_version_4"]:
            for digit, boolean in [
                ("7", self.project.options["prefer_typo_metrics"]),
                ("8", self.project.options["is_width_weight_slope_only"]),
                ("9", self.is_oblique),
            ]:
                arguments.append("-osbOn" if boolean else "-osbOff")
                arguments.append(digit)

        subprocess.call(["makeotf"] + arguments)

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
