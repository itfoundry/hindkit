#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, glob, subprocess
import fontTools.ttLib
import hindkit as kit

class BaseFont(kit.BaseFile):

    def __init__(
        self,
        family = None,
        name = "",
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
                if self.file_format in ["UFO", "VFB"]:
                    if self.file_format == "VFB":
                        kit.makedirs(self.get_directory())
                        input_path = self.get_path()
                        self._path = None
                        self._filename = os.path.basename(input_path)
                        self.file_format = "UFO"
                        subprocess.call([
                            "vfb2ufo", "-fo", input_path, self.get_path(),
                        ])
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

    def import_from_font(
        self,
        source_path,
        target_path = None,
        import_glyphs = True,
        glyph_names_included = None,
        glyph_names_excluded = None,
        glyph_renaming_map = None,
        import_kerning = True,
    ):

        glyph_names_included = kit.fallback(glyph_names_included, [])
        glyph_names_excluded = kit.fallback(glyph_names_excluded, [])
        glyph_renaming_map = kit.fallback(glyph_renaming_map, {})

        if source_path.endswith(".ufo"):
            source_format = "UFO"
        elif source_path.endswith(".vfb"):
            source_format = "VFB"
        else:
            raise SystemExit("The format of {} is not supported.".format(source_path))
        source_file = BaseFont(
            family = self.family,
            abstract_directory = kit.Project.directories["misc"],
            file_format = source_format,
        )
        source_file._path = source_path
        source_font = source_file.open()
        if target_path:
            target_file = BaseFont()
            target_file._path = target_path
            target_font = target_file.open()
        else:
            target_font = self.open()

        if glyph_names_included:
            glyph_names_importing = set(glyph_names_included)
        else:
            glyph_names_importing = set(source_font.keys())

        if import_glyphs and glyph_names_importing:
            glyph_names_importing.difference_update(set(glyph_names_excluded))
            glyph_names_importing.difference_update(set(target_font.keys()))
            glyph_names_importing = (
                [i for i in source_font.glyphOrder if i in glyph_names_importing] +
                [i for i in glyph_names_importing if i not in source_font.glyphOrder]
            )
            print("\n[NOTE] Importing glyphs from `{}` to `{}`:".format(source_path, self.name))
            for source_glyph_name in glyph_names_importing:
                source_glyph = source_font[source_glyph_name]
                for component in source_glyph.components:
                    if component.baseGlyph not in glyph_names_importing:
                        source_glyph.decomposeComponent(component)
                        print("(decomposed {} in {})".format(component.baseGlyph, source_glyph_name), end=" ")
                target_glyph_name = glyph_renaming_map.get(source_glyph_name, source_glyph_name) # TODO: Might break component reference.
                target_glyph = target_font.newGlyph(target_glyph_name)
                target_glyph.copyDataFromGlyph(source_glyph)
                if target_glyph_name == source_glyph_name:
                    print(target_glyph_name, end=", ")
                else:
                    print("{} -> {}".format(source_glyph_name, target_glyph_name), end=", ")

        if import_kerning and source_font.kerning:
            target_font.groups.update(source_font.groups)
            target_font.kerning.update(source_font.kerning)
            for key, group_value in target_font.groups.items():
                if key.startswith(("public.kern", "_KERN_")):
                    if key.startswith("public.kern"):
                        key_modified = key[13:]
                        target_font.groups[key_modified] = group_value
                        for (key_l, key_r), value in target_font.kerning.items():
                            if key in (key_l, key_r):
                                if key_l == key:
                                    target_font.kerning[key_modified, key_r] = value
                                elif key_r == key:
                                    target_font.kerning[key_l, key_modified] = value
                                del target_font.kerning[key_l, key_r]
                    elif key.startswith("_KERN_"):
                        parts = key.split("_")
                        if len(parts) == 3:
                            _, _, name= parts
                            key_modified = "@MMK_L_" + name, "@MMK_R_" + name
                        else:
                            _, _, name, side = parts
                            if side == "1ST":
                                key_modified = "@MMK_L_" + name, None
                            elif side == "2ND":
                                key_modified = None, "@MMK_R_" + name
                        key_l_modified, key_r_modified = key_modified
                        if key_l_modified:
                            target_font.groups[key_l_modified] = group_value
                        if key_r_modified:
                            target_font.groups[key_r_modified] = group_value
                        for (key_l, key_r), value in target_font.kerning.items():
                            if name in (key_l, key_r):
                                if key_l_modified and key_r_modified and key_l == name and key_r == name:
                                    target_font.kerning[key_l_modified, key_r_modified] = value
                                elif key_l_modified and key_l == name:
                                    target_font.kerning[key_l_modified, key_r] = value
                                elif key_r_modified and key_r == name:
                                    target_font.kerning[key_l, key_r_modified] = value
                                del target_font.kerning[key_l, key_r]
                    del target_font.groups[key]
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

    def remove_glyphs(self, names):
        defconFont = self.open()
        print("\n[NOTE] Removing glyphs in `{}`:".format(self.name))
        for glyph in defconFont:
            for component in glyph.components:
                if component.baseGlyph in names:
                    glyph.decomposeComponent(component)
                    print("(decomposed {} in {})".format(component.baseGlyph, glyph.name), end=" ")
        for name in names:
            del defconFont[name]
            print(name, end=", ")


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
            abstract_directory = os.path.join(kit.Project.directories["styles"], name),
            location = location,
            weight_and_width_class = weight_and_width_class,
        )

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
            if hasattr(self, "postprocess"):
                original = fontTools.ttLib.TTFont(self.get_path(), recalcTimestamp=True)
                postprocessed = self.postprocess(original)
                postprocessed.save(self.get_path(), reorderTables=False)
                print("[FONT POSTPROCESSED]", self.get_path())
