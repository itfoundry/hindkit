import os, glob, subprocess, itertools, collections
import defcon, fontTools.ttLib, getKerningPairsFromFEA
from afdko.makeinstancesufo import logger, normalizeUFO, updateInstance, validateLayers
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

        self.x_height = 0
        self.cap_height = 0

        self._name_postscript = None
        self._full_name = None
        self._full_name_postscript = None

        self.defconFont = None

        self.adjustment_for_matching_mI_variants = None
        self.glyph_renaming_map = {}

    @property
    def name_postscript(self):
        return kit.fallback(self._name_postscript, kit.remove_illegal_chars_for_postscript_name_part(self.name))

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
                    self.defconFont = defcon.Font(self.get_path())
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
        import_anchors = False,
        import_kerning = False,
        import_blue_zones = False,
        import_x_and_cap_heights = False,
    ):

        g_names_included = kit.fallback(glyph_names_included, [])
        g_names_excluded = kit.fallback(glyph_names_excluded, [])
        g_names_included = set(g_names_included)
        g_names_excluded = set(g_names_excluded)

        if glyph_renaming_map is not None:
            self.glyph_renaming_map.update(glyph_renaming_map)

        if import_glyphs and source_path.endswith((".ufo", ".vfb")):
            source_file = BaseFont(
                family = self.family,
                abstract_directory = kit.Project.directories["misc"],
                file_format = source_path[-3:].upper(),
            )
            source_file._path = source_path
            source_font = source_file.open()
        elif import_kerning and source_path.endswith(".fea"):
            kern_fea_reader = getKerningPairsFromFEA.FEAKernReader([source_path])
            source_font = defcon.Font()
            source_font.groups.update(kern_fea_reader.kernClasses)
            kern_classes_reversed = {tuple(v): k for k, v in list(kern_fea_reader.kernClasses.items())}
            if len(kern_fea_reader.kernClasses) != len(kern_classes_reversed):
                raise SystemExit()
            for enum, (left, right), value in reversed(kern_fea_reader.foundKerningPairs):
                pair = []
                for side in left, right:
                    parts = side.split()
                    if tuple(parts) in kern_classes_reversed:
                        parts = [kern_classes_reversed[tuple(parts)]]
                    pair.append(parts)
                pairs = list(itertools.product(*pair))
                for pair in pairs:
                    source_font.kerning[pair] = int(value)
        else:
            raise SystemExit("The format of {} is not supported.".format(source_path))

        if target_path:
            self._path = target_path
        target_font = self.open()

        if import_blue_zones:
            target_font.info.postscriptBlueValues = source_font.info.postscriptBlueValues
            target_font.info.postscriptOtherBlues = source_font.info.postscriptOtherBlues

        if import_x_and_cap_heights:
            self.x_height = source_font.info.xHeight
            self.cap_height = source_font.info.capHeight

        if g_names_included:
            g_names_importing = g_names_included
        else:
            g_names_importing = set(source_font.keys())

        g_names_importing_renamed = {
            self.glyph_renaming_map.get(i, i) for i in g_names_importing
        }

        if import_glyphs and g_names_importing:
            print("\n[NOTE] Importing glyphs from `{}` to `{}`:".format(source_path, self.name))
            if g_names_excluded:
                g_names_importing.difference_update(g_names_excluded)
                print("Excluding: {}".format(", ".join(g_names_excluded)))
            g_names_importing_renamed
            g_names_already_existing = g_names_importing_renamed.intersection(set(target_font.keys()))
            if g_names_already_existing:
                g_names_importing.difference_update(g_names_already_existing)
                print("Already existing; will not overwrite: {}".format(", ".join(g_names_already_existing)))
            g_names_importing = (
                [i for i in source_font.glyphOrder if i in g_names_importing] +
                [i for i in g_names_importing if i not in source_font.glyphOrder]
            )
            for source_g_name in g_names_importing:
                source_g = source_font[source_g_name]
                if not import_anchors:
                    source_g.clearAnchors()
                for component in source_g.components:
                    if component.baseGlyph not in g_names_importing:
                        source_g.decomposeComponent(component)
                        print("(decomposed {} in {})".format(component.baseGlyph, source_g_name), end=" ")
                target_g_name = self.glyph_renaming_map.get(source_g_name, source_g_name)
                target_font.newGlyph(target_g_name)
                target_g = target_font[target_g_name]
                target_g.copyDataFromGlyph(source_g)
                if target_g_name == source_g_name:
                    print(target_g_name, end=", ")
                else:
                    print("{} -> {}".format(source_g_name, target_g_name), end=", ")
            print()

        # TODO: Component reference and glyph group reference both need to be updated.

        if import_kerning and source_font.kerning:
            target_font.groups.update(source_font.groups)
            target_font.kerning.update(source_font.kerning)
            print("\n[NOTE] Imported kerning.")

    def refresh_groups(self):

        font = self.open()
        groups_modified = {}
        kerning_side_renaming_map = {}

        for glyph_class_name, glyph_names in font.groups.items():

            if glyph_class_name.startswith("_KERN_"):
                glyph_class_name_modified = "@" + glyph_class_name[1:]

            glyph_names_modified = []

            for glyph_name in glyph_names:
                if glyph_name.endswith("'"):  # Kerning class key glyph.
                    glyph_name = glyph_name[:-1]
                    if glyph_class_name_modified.endswith("_1ST"):
                        kerning_side_renaming_map[(0, glyph_name)] = glyph_class_name_modified
                    elif glyph_class_name_modified.endswith("_2ND"):
                        kerning_side_renaming_map[(1, glyph_name)] = glyph_class_name_modified
                    else:
                        kerning_side_renaming_map[(0, glyph_name)] = glyph_class_name_modified
                        kerning_side_renaming_map[(1, glyph_name)] = glyph_class_name_modified
                glyph_name_modified = self.glyph_renaming_map.get(glyph_name, glyph_name)
                if glyph_name_modified in font:
                    glyph_names_modified.append(glyph_name_modified)

            if glyph_names_modified:
                groups_modified[glyph_class_name_modified] = glyph_names_modified

        font.groups.clear()
        font.groups.update(groups_modified)
        print("\n[NOTE] Refreshed glyph groups.")
        print(font.groups)

        kerning_modified = {}

        for pair, value in font.kerning.items():

            valid_side_mames = list(font.groups.keys()) + list(font.keys())
            pair_modified = []

            for side, side_name in enumerate(pair):
                side_name_modified = kerning_side_renaming_map.get((side, side_name), side_name)
                side_name_modified = self.glyph_renaming_map.get(side_name_modified, side_name_modified)
                if side_name_modified in valid_side_mames:
                    pair_modified.append(side_name_modified)
                else:
                    break
            else:
                kerning_modified[tuple(pair_modified)] = value

        font.kerning.clear()
        font.kerning.update(kerning_modified)
        print("\n[NOTE] Refreshed kerning.")

    def derive_glyphs(self, deriving_names):

        DERIVED_NAME_TO_SOURCE_NAME = {
            derived_name: source_name
            for source_name, derived_names in list(kit.constants.DERIVABLE_GLYPHS.items())
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
                source_glyph = target[source_name]
                deriving_glyph = target[deriving_name]
                deriving_glyph.width = source_glyph.width
                if len(source_glyph) > 0 or source_glyph.components:
                    component_source_glyph = deriving_glyph.instantiateComponent()
                    component_source_glyph.baseGlyph = source_name
                    deriving_glyph.appendComponent(component_source_glyph)
            print("{} -> {}".format(source_name, deriving_name), end=", ")

    def remove_glyphs(self, names):
        target = self.open()
        existing_names = list(target.keys())
        names_to_be_removed = []
        for name in names:
            if name in existing_names:
                names_to_be_removed.append(name)
            else:
                print("[NOTE] `{}` is missing.".format(name))
        print("\n[NOTE] Removing glyphs in `{}`:".format(self.name))
        for g in target:
            for component in g.components:
                if component.baseGlyph in names_to_be_removed:
                    g.decomposeComponent(component)
                    print("(decomposed {} in {})".format(component.baseGlyph, g.name), end=" ")
        for name in names_to_be_removed:
            del target[name]
            print(name, end=", ")

    def rename_glyphs(self, mapping):
        target = self.open()
        for k, v in list(mapping.items()):
            if k in target:
                target[k].name = "__temp"
                if v in target:
                    target[v].name = k
                target["__temp"].name = v


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
        filename = "{}-{}".format(self.family.name, self.name)
        filename_pattern = "*-{}".format(self.name)
        path = os.path.join(self.get_directory(temp=False), filename + ".ufo")
        path_pattern = os.path.join(self.get_directory(temp=False), filename_pattern + ".ufo")
        if self._filename is None:
            if os.path.exists(path):
                self._filename = filename
            else:
                paths = glob.glob(path_pattern)
                if paths:
                    self._filename = os.path.basename(paths[0]).partition(".")[0]
        if self._filename is None:
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

    Options = collections.namedtuple(
        "Options",
        "doNormalize doOverlapRemoval doAutoHint no_round",
    )

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

        self.goadb_trimmed = kit.Goadb(self.project, product=self)
        self.goadb_trimmed.prepare()

        if self.file_format == "OTF" and self.style.file_format == "UFO":

            defconFont = self.style.open()
            defconFont.info.postscriptFontName = self.full_name_postscript
            defconFont.lib["public.glyphOrder"] = self.goadb_trimmed.names
            for k in ["com.schriftgestaltung.glyphOrder", "com.schriftgestaltung.font.glyphOrder"]:
                defconFont.lib.pop(k, None)
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
            self.style.save()

            # from afdko/makeinstancesufo.py:
            options = self.Options(
                doNormalize = self.project.options["do_normalize"],
                doOverlapRemoval = self.project.options["run_checkoutlines"],
                doAutoHint = self.project.options["run_autohint"],
                no_round = False,
            )
            instancePath = self.style.get_path()
            if options.doNormalize:
                logger.info("Applying UFO normalization...")
                normalizeUFO(instancePath, outputPath=None, onlyModified=True,
                                writeModTimes=False)
            if options.doOverlapRemoval or options.doAutoHint:
                logger.info("Applying post-processing...")
                updateInstance(options, instancePath)
            if not options.doOverlapRemoval:
                validateLayers(instancePath)
            if options.doOverlapRemoval or options.doAutoHint:
                if options.doNormalize:
                    normalizeUFO(instancePath, outputPath=None, onlyModified=False,
                                writeModTimes=False)

        elif self.file_format == "TTF":

            # subprocess.call([
            #     "osascript", "-l", "JavaScript",
            #     kit.relative_to_package("data/generate_ttf.js"),
            #     os.path.abspath(self.style.get_path()),
            # ])

            self.style.file_format = "TTF" #TODO: Should restore the original file format afterwards. Or the styles should just seperate.

            while not os.path.exists(self.style.get_path()):
                print(
                    "\n[PROMPT] Input file {} is missing. Try again? [Y/n]: ".format(self.style.get_path()),
                    end = "",
                )
                if input().upper().startswith("N"):
                    return

        kit.makedirs(self.get_directory())

        arguments = [
            "-f", self.style.get_path(),
            "-o", self.get_path(),
            "-mf", self.project.fmndb.get_path(),
            "-gf", self.goadb_trimmed.get_path(),
            "-ga",
            "-overrideMenuNames",
        ]
        if self.project.options["run_autohint"]:
            arguments.append("-shw")
        else:
            arguments.append("-nshw")
        if self.project.options["use_mac_name_records"]:
            arguments.append("-useMacNames")
        else:
            arguments.append("-omitMacNames")
        if not self.project.args.test:
            arguments.append("-r")
        if self.project.options["do_style_linking"] and (self.is_bold or self.is_italic):
            if self.is_bold:
                arguments.append("-b")
            if self.is_italic:
                arguments.append("-i")
        else:
            arguments.extend(["-osbOn", "6"])
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

            self.font = fontTools.ttLib.TTFont(self.get_path(), recalcTimestamp=True)
            dirty = False
            for table_tag in [
                "STAT", # Introduced by Glyphs.
            ]:
                if table_tag in self.font:
                    del self.font[table_tag]
                    dirty = True
            if hasattr(self, "postprocess"):
                self.font = self.postprocess()
                dirty = True
            if dirty:
                self.font.save(self.get_path(), reorderTables=False)
                print("[FONT POSTPROCESSED]", self.get_path())

        if self.built:

            self.copy_out_of_temp()

            output_dir = self.project.directories["output"]
            if os.path.isdir(output_dir):
                kit.copy(
                    self.get_path(),
                    os.path.join(output_dir, self.filename_with_extension),
                )
                print("[COPIED TO OUPUT DIRECTORY]", self.get_path())
