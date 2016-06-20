#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, collections, itertools, re
import WriteFeaturesKernFDK, WriteFeaturesMarkFDK
import hindkit as kit

class BaseFeature(kit.BaseFile):

    def __init__(self, project, name, style, filename_group):
        if style:
            abstract_directory = style.abstract_directory
        else:
            abstract_directory = kit.Project.directories["features"]
        super(BaseFeature, self).__init__(
            name,
            file_format = "FEA",
            project = project,
            filename_group = filename_group,
            abstract_directory = abstract_directory,
        )
        self.style = style

    @staticmethod
    def sort_names(names, order):
        return (
            [i for i in order if i in names] +
            [i for i in names if i not in order]
        )

    @staticmethod
    def compose_glyph_class_def_lines(class_name, glyph_names):
        if glyph_names:
            glyph_class_def_lines = (
                ["@{} = [".format(class_name)] +
                ["  {}".format(glyph_name) for glyph_name in glyph_names] +
                ["];", ""]
            )
        else:
            glyph_class_def_lines = ["# @{} = [];".format(class_name), ""]
        return glyph_class_def_lines


class FeatureClasses(BaseFeature):

    def generate(self):

        lines = []

        if self.project.options["prepare_mark_positioning"]:

            f = kit.filters
            glyph_classes = [
                (WriteFeaturesMarkFDK.kCombMarksClassName, f.marks, None),
            ]
            if self.project.options["match_mI_variants"]:
                m = FeatureMatches
                glyph_classes.extend([
                    (m.CLASS_NAME_mI_VARIANTS, f.mI_variants, None),
                    (m.CLASS_NAME_BASES_ALIVE, f.bases_alive, m.BASE_NAMES_ALIVE),
                    (m.CLASS_NAME_BASES_FOR_LONG_mI, f.bases_for_long_mII, m.BASE_NAMES_FOR_LONG_mII),
                ])
                if self.project.options["match_mI_variants"] == "sequence":
                    glyph_classes.extend([
                        (m.CLASS_NAME_BASES_DEAD, f.bases_dead, m.BASE_NAMES_DEAD),
                    ])

            font_0 = self.project.products[0].style.open()

            glyph_order = self.project.glyph_data.glyph_order
            for class_name, filter_function, overriding in glyph_classes:
                glyph_names = kit.fallback(
                    overriding,
                    [i.name for i in font_0 if filter_function(self.project.family, i)],
                )
                glyph_names = self.sort_names(glyph_names, glyph_order)
                if glyph_names:
                    font_0.groups.update({class_name: glyph_names})
                lines.extend(
                    self.compose_glyph_class_def_lines(class_name, glyph_names)
                )
            font_0.save()

            for style in (i.style for i in self.project.products[1:]):
                font = style.open()
                font.groups.update(font_0.groups)
                font.save()

        if lines:
            with open(self.path, "w") as f:
                f.writelines(i + "\n" for i in lines)


class FeatureTables(BaseFeature):

    def generate(self):

        info = self.project.family.info
        client = self.project.family.client

        lines = []
        tables = collections.OrderedDict([
            ("hhea", []),
            ("OS/2", []),
            ("GDEF", []),
            ("name", []),
        ])

        tables["OS/2"].append("include (WeightClass.fea);")
        tables["OS/2"].append("fsType {};".format(client.tables["OS/2"]["fsType"]))

        unicode_range_bits = set(
            i for i in
            [self.project.family.script.unicode_range_bit] +
            self.project.options["additional_unicode_range_bits"]
            if i
        )
        if unicode_range_bits:
            tables["OS/2"].append(
                "UnicodeRange {};".format(
                    " ".join(str(i) for i in sorted(unicode_range_bits))
                )
            )

        vender_id = client.tables["OS/2"]["Vendor"]
        if vender_id:
            tables["OS/2"].append("Vendor \"{}\";".format(vender_id))

        set_vertical_metrics = False
        for field in (
            info.openTypeHheaAscender,
            info.openTypeHheaDescender,
            info.openTypeHheaLineGap,
            info.openTypeOS2TypoAscender,
            info.openTypeOS2TypoDescender,
            info.openTypeOS2TypoLineGap,
            info.openTypeOS2WinAscent,
            info.openTypeOS2WinDescent,
        ):
            if field is not None:
                set_vertical_metrics = True
                break

        if set_vertical_metrics:

            if info.unitsPerEm is None:
                raise SystemExit("`family.info.unitsPerEm` is unavailable.")

            if info.openTypeHheaAscender is None:
                info.openTypeHheaAscender = 800
            if info.openTypeHheaDescender is None:
                info.openTypeHheaDescender = -200
            if info.openTypeHheaLineGap is None:
                info.openTypeHheaLineGap = 0

            if client.vertical_metrics_strategy == "Google Fonts":
                if info.openTypeOS2TypoAscender is None:
                    info.openTypeOS2TypoAscender = info.openTypeHheaAscender
                if info.openTypeOS2TypoDescender is None:
                    info.openTypeOS2TypoDescender = info.openTypeHheaDescender
                if info.openTypeOS2TypoLineGap is None:
                    info.openTypeOS2TypoLineGap = info.openTypeHheaLineGap
            elif client.vertical_metrics_strategy == "ITF":
                extra_height = info.openTypeHheaAscender - info.openTypeHheaDescender - info.unitsPerEm
                if info.openTypeOS2TypoAscender is None:
                    info.openTypeOS2TypoAscender = info.openTypeHheaAscender - int(round(extra_height / 2))
                if info.openTypeOS2TypoDescender is None:
                    info.openTypeOS2TypoDescender = info.openTypeOS2TypoAscender - info.unitsPerEm
                if info.openTypeOS2TypoLineGap is None:
                    info.openTypeOS2TypoLineGap = info.openTypeHheaLineGap + extra_height

            if info.openTypeOS2WinAscent is None:
                info.openTypeOS2WinAscent = info.openTypeHheaAscender
            if info.openTypeOS2WinDescent is None:
                info.openTypeOS2WinDescent = abs(info.openTypeHheaDescender)

            tables["hhea"].extend([
                "Ascender {};".format(info.openTypeHheaAscender),
                "Descender {};".format(info.openTypeHheaDescender),
                "LineGap {};".format(info.openTypeHheaLineGap),
            ])
            tables["OS/2"].extend([
                "TypoAscender {};".format(info.openTypeOS2TypoAscender),
                "TypoDescender {};".format(info.openTypeOS2TypoDescender),
                "TypoLineGap {};".format(info.openTypeOS2TypoLineGap),
                "winAscent {};".format(info.openTypeOS2WinAscent),
                "winDescent {};".format(info.openTypeOS2WinDescent),
            ])

        code_pages = set(
            i for i in self.project.options["additional_code_pages"] if i
        )
        if code_pages:
            tables["OS/2"].append(
                "CodePageRange {};".format(
                    " ".join(str(i) for i in sorted(code_pages))
                )
            )

        if self.project.options["override_GDEF"]:
            GDEF_records = {
                "bases": "",
                "ligatures": "",
                "marks": "",
                "components": "",
            }
            if self.project.options["prepare_mark_positioning"] or os.path.exists(os.path.join(self.directory, "classes.fea")):
                GDEF_records["marks"] = "@{}".format(WriteFeaturesMarkFDK.kCombMarksClassName)
            if os.path.exists(os.path.join(self.directory, "classes_suffixing.fea")):
                GDEF_records["marks"] = "@{}".format("COMBINING_MARKS_GDEF")
            tables["GDEF"].extend([
                "GlyphClassDef {bases}, {ligatures}, {marks}, {components};".format(**GDEF_records)
            ])

        tables["name"].extend(
            "nameid {} \"{}\";".format(
                name_id,
                content.encode("unicode_escape").replace("\\x", "\\00").replace("\\u", "\\")
            )
            for name_id, content in sorted(client.tables["name"].items())
            if content
        )

        for name, entries in tables.items():
            if entries:
                lines.append("table %s {" % name)
                lines.extend("  " + i for i in entries)
                lines.append("} %s;" % name)

        if lines:
            with open(self.path, "w") as f:
                f.writelines(i + "\n" for i in lines)


class FeatureLanguagesystems(BaseFeature):
    def generate(self):
        lines = ["languagesystem DFLT dflt;"]
        for tag in self.project.family.script.tags:
            lines.append("languagesystem {} dflt;".format(tag))
        if lines:
            with open(self.path, "w") as f:
                f.writelines(i + "\n" for i in lines)


class FeatureMark(BaseFeature):
    def generate(self):
        WriteFeaturesMarkFDK.kMarkFeatureFileName = self.filename_with_extension
        WriteFeaturesMarkFDK.MarkDataClass(
            font = self.style.open(),
            folderPath = self.style.directory,
            trimCasingTags = False,
            genMkmkFeature = self.project.options["prepare_mark_to_mark_positioning"],
            writeClassesFile = True,
            indianScriptsFormat = self.project.family.script.is_indic,
        )


class FeatureKern(BaseFeature):
    def generate(self):
        WriteFeaturesKernFDK.kKernFeatureFileName = self.filename_with_extension
        WriteFeaturesKernFDK.KernDataClass(
            font = self.style.open(),
            folderPath = self.style.directory,
        )
        try:
            self.project.postprocess_kerning
        except AttributeError:
            pass
        else:
            kern_path = self.path
            if os.path.exists(kern_path):
                with open(kern_path) as f:
                    content = f.read()
                with open(kern_path, "w") as f:
                    f.write(self.project.postprocess_kerning(content))


class FeatureWeightClass(BaseFeature):
    def generate(self):
        with open(self.path, "w") as f:
            f.write("WeightClass {};\n".format(str(self.style.weight_class)))


class FeatureMatches(BaseFeature):

    class Base(object):
        def __init__(self, feature, base_glyph_sequence):
            self.glyphs = base_glyph_sequence
            self.target = None
            for g in reversed(self.glyphs):
                #TODO: Kerning.
                if self.target is None:
                    self.target = feature._get_stem_position(g)
                else:
                    self.target += g.width

    class Match(object):
        def __init__(self, feature, mI_variant_name):
            self.name = mI_variant_name
            if self.name:
                self.mI_variant = feature.font[self.name]
                self.tag = self.mI_variant.name.partition(".")[2]
                self.overhanging = abs(self.mI_variant.rightMargin)
            self.bases = []

    # POTENTIAL_MODES = [
    #     "single glyph", "glyph sequence",
    #     "position marks", "ligate marks",
    # ]

    CLASS_NAME_mI_VARIANTS = "mI_VARIANTS"
    CLASS_NAME_BASES_ALIVE = "BASES_ALIVE"
    CLASS_NAME_BASES_DEAD = "BASES_DEAD"
    CLASS_NAME_BASES_FOR_LONG_mI = "BASES_FOR_LONG_mI"

    CONSONANTS_ALIVE = [
        i + "A" for i in kit.constants.CONSONANT_STEMS
    ] + "GAbar JAbar DDAbar BAbar ZHA YAheavy DDAmarwari".split()
    CONSONANTS_DEAD = kit.constants.CONSONANT_STEMS

    mI_VARIANT_NAME_PATTERN = r"mI\.\d\d"

    BASE_NAMES_ALIVE = None
    BASE_NAMES_DEAD = None
    BASE_NAMES_FOR_LONG_mII = None

    mI_ANCHOR_NAME = "abvm.i"

    BASE_GLYPH_SEQUENCE_LENGTH = 2

    def __init__(self, project, name, style, filename_group):
        super(FeatureMatches, self).__init__(project, name, style, filename_group)
        self._bases_alive = None
        self._bases_dead = None

    def generate(self):

        self.font = self.style.open()

        self.matches = [self.Match(self, i) for i in self.font.groups[self.CLASS_NAME_mI_VARIANTS]]
        if not self.matches:
            raise ValueError("[WARNING] No variants for mI.")
        self.not_matched = self.Match(self, None)

        abvm_position_in_mE = self._get_abvm_position(
            self.font[self.style.family.script.abbr + "mE"],
            in_base = False,
        )
        if abvm_position_in_mE is None:
            raise SystemExit("[WARNING] Can't find the abvm anchor in glyph `mE`!")
        else:
            self.abvm_right_margin = abs(abvm_position_in_mE)

        self.bases = [self.Base(self, i) for i in self._base_glyph_sequences()]
        if not self.bases:
            raise ValueError("[WARNING] No bases.")

        self.adjustment_extremes = self._get_adjustment_extremes()
        if self.adjustment_extremes:
            targets = [base.target for base in self.bases]
            target_min = min(targets)
            target_max = max(targets)
            for i, target in enumerate(targets):
                ratio = (target - target_min) / (target_max - target_min)
                ae = self.adjustment_extremes
                adjustment = ae[0] + (ae[-1] - ae[0]) * ratio
                targets[i] += adjustment
            print()

        self.tolerance = self._get_stem_position(
            self.font[self.style.family.script.abbr + "VA"]
        ) * 0.5

        for base in self.bases:
            match = self.match_mI_variants(base)
            match.bases.append(base)

        self.name_default = self.style.family.script.abbr + "mI"

        self.substitute_rule_lines = []
        for match in self.matches:
            self.output_mI_variant_matches(match)
        with open(self.path, "w") as f:
            f.writelines([
                "lookup %s {\n" % self.name,
                # "  lookupflag IgnoreMarks;\n",
            ])
            f.writelines("  " + l + "\n" for l in self.substitute_rule_lines)
            f.writelines([
                # "  lookupflag 0;\n",
                "} %s;\n" % self.name,
            ])

        if self.project.options["position_marks_for_mI_variants"] and \
        self.project.options["match_mI_variants"] == "single":
            self.output_mark_positioning_for_mI_variants()

    def _get_adjustment_extremes(self):
        try:
            light, bold = self.project.adjustment_for_matching_mI_variants
        except AttributeError:
            return None
        else:
            light_min, light_max = light
            bold_min, bold_max = bold
            axis_start = self.project.family.masters[0].weight_location
            axis_end = self.project.family.masters[-1].weight_location
            axis_range = axis_end - axis_start
            if axis_range == 0:
                ratio = 1
            else:
                ratio = (self.style.weight_location - axis_start) / axis_range
            return (
                light_min + (bold_min - light_min) * ratio,
                light_max + (bold_max - light_max) * ratio,
            )

    def _get_abvm_position(self, glyph, in_base=True):
        anchor_name_prefix = "" if in_base else "_"
        for potential_anchor_name in ["abvm.candra", "abvm.e", "abvm"]:
            for anchor in glyph.anchors:
                if anchor.name == anchor_name_prefix + potential_anchor_name:
                    return anchor.x

    def _get_stem_position(self, glyph):
        abvm_position = self._get_abvm_position(glyph)
        if abvm_position is None:
            return glyph.width - self.abvm_right_margin
        else:
            return abvm_position

    @property
    def bases_alive(self):
        if self._bases_alive is None:
            base_names = kit.fallback(
                self.BASE_NAMES_ALIVE,
                self.font.groups[self.CLASS_NAME_BASES_ALIVE],
            )
            return [self.font[i] for i in base_names]
        else:
            return self._bases_alive
    @bases_alive.setter
    def bases_alive(self, value):
        self._bases_alive = value

    @property
    def bases_dead(self):
        if self._bases_dead is None:
            base_names = kit.fallback(
                self.BASE_NAMES_DEAD,
                self.font.groups[self.CLASS_NAME_BASES_DEAD],
            )
            return [self.font[i] for i in base_names]
        else:
            return self._bases_dead
    @bases_dead.setter
    def bases_dead(self, value):
        self._bases_dead = value

    def _base_glyph_sequences(self):

        bases_alive = self.bases_alive
        if self.project.options["match_mI_variants"] == "single":
            bases_dead = [None]
        elif self.project.options["match_mI_variants"] == "sequence":
            bases_dead = [None] + self.bases_dead
        else:
            raise ValueError("[WARNING] Project.options[\"match_mI_variants\"] is not set to \"single\" or \"sequence\".")

        seeds = [bases_dead] * (self.BASE_GLYPH_SEQUENCE_LENGTH - 1) + [bases_alive]
        for raw_sequence in itertools.product(*seeds):
            sequence = [i for i in raw_sequence if i is not None]
            if sequence:
                yield sequence

    def match_mI_variants(self, base):
        if base.target <= self.matches[0].overhanging:
            return self.matches[0]
        elif base.target < self.matches[-1].overhanging:
            i = 0
            while self.matches[i].overhanging < base.target:
                candidate_short = self.matches[i]
                i += 1
            candidate_enough = self.matches[i]
            if (
                abs(candidate_enough.overhanging - base.target) <
                abs(candidate_short.overhanging - base.target)
            ):
                return candidate_enough
            else:
                return candidate_short
        elif base.target <= self.matches[-1].overhanging + self.tolerance:
            return self.matches[-1]
        else:
            return self.not_matched

    def output_mI_variant_matches(self, match):

        if not match.bases:
            print("\t\t`{}` is not used.".format(match.name))
            self.substitute_rule_lines.append(
                "# sub {}' _ by {};".format(self.name_default, match.name),
            )
            return

        single_glyph_bases = []
        multiple_glyph_bases = []
        for base in match.bases:
            if len(base.glyphs) == 1:
                single_glyph_bases.append(base)
            else:
                multiple_glyph_bases.append(base)

        if single_glyph_bases:
            self.substitute_rule_lines.append(
                "sub {}' [{}] by {};".format(
                    self.name_default,
                    " ".join(i.glyphs[0].name for i in single_glyph_bases),
                    match.name,
                ),
            )

        def compress(raw):
            compressed = {}
            for k, v in raw:
                if k in compressed:
                    compressed[k].extend(v)
                else:
                    compressed[k] = v
            return compressed

        # self.BASE_GLYPH_SEQUENCE_LENGTH = 2

        compressed = compress(
            (tuple(i.glyphs[:1]), i.glyphs[1:]) for i in multiple_glyph_bases
        )
        compressed = compress(
            (tuple(v), list(k)) for k, v in compressed.items()
        )

        for rule in ([v, list(k)] for k, v in compressed.items()):
            self.substitute_rule_lines.append(
                "sub {}' {} by {};".format(
                    self.name_default,
                    " ".join(
                        i[0].name if len(i) == 1
                        else "[{}]".format(" ".join(j.name for j in i))
                        for i in rule
                    ),
                    match.name,
                ),
            )

    def output_mark_positioning_for_mI_variants(self):

        abvm_backup_path = os.path.join(
            self.style.directory,
            "backup--" + WriteFeaturesMarkFDK.kAbvmFeatureFileName,
        )
        abvm_path = os.path.join(
            self.style.directory,
            WriteFeaturesMarkFDK.kAbvmFeatureFileName,
        )
        if os.path.exists(abvm_backup_path):
            kit.copy(abvm_backup_path, abvm_path)
        else:
            kit.copy(abvm_path, abvm_backup_path)

        pattern_begin = re.compile(r"lookup MARK_BASE_%s \{$" % self.mI_ANCHOR_NAME)
        pattern_end = re.compile(r"\} MARK_BASE_%s;$" % self.mI_ANCHOR_NAME)

        match_dict = {match.tag: match for match in self.matches}
        print(match_dict)
        def _modify(matchobj):
            match = match_dict[matchobj.group(1).partition(".")[2]]
            if match.bases:
                prefix = ""
                names = "[{}]".format(" ".join(i.glyphs[0].name for i in match.bases))
            else:
                prefix = "# "
                names = "_"
            x = int(matchobj.group(2))
            x_with_offset = x - self.matches[0].mI_variant.width
            return "{}pos base {} <anchor {}".format(prefix, names, x_with_offset)

        with open(abvm_path, "r") as f:
            lines_modified = []
            is_inside_the_lookup = False
            for line in f:
                if is_inside_the_lookup:
                    if pattern_end.match(line):
                        is_inside_the_lookup = False
                        line_modified = line
                    else:
                        line_modified = re.sub(
                            r"pos base ({}{}) <anchor (-?\d+)".format(
                                self.style.family.script.abbr,
                                self.mI_VARIANT_NAME_PATTERN,
                            ),
                            _modify,
                            line,
                        )
                else:
                    if pattern_begin.match(line):
                        is_inside_the_lookup = True
                        line_modified = line
                    else:
                        line_modified = line
                lines_modified.append(line_modified)

        with open(abvm_path, "w") as f:
            f.writelines(lines_modified)


class FeatureReferences(BaseFeature):
    def generate(self):
        with open(self.path, "w") as f:
            lines = ["table head { FontRevision 1.000; } head;"]
            for feature in [
                self.project.feature_classes,
                self.project.feature_tables,
                self.project.feature_languagesystems,
                self.project.feature_gsub,
            ]:
                for i in feature.file_group:
                    if os.path.exists(i.path):
                        lines.append(
                            "include ({});".format(
                                os.path.relpath(i.path, self.style.directory)
                            )
                        )
            if os.path.exists(self.project.feature_kern.path):
                lines.append(
                    "feature %(tag)s { include (%(path)s); } %(tag)s;" % {
                        "tag": "dist" if self.project.family.script.is_indic else "kern",
                        "path": os.path.relpath(self.project.feature_kern.path, self.style.directory),
                    }
                )
            if os.path.exists(os.path.join(self.style.directory, WriteFeaturesMarkFDK.kMarkClassesFileName)):
                lines.append("include ({});".format(WriteFeaturesMarkFDK.kMarkClassesFileName))
            for feature_name, filename in [
                ("mark", WriteFeaturesMarkFDK.kMarkFeatureFileName),
                ("mkmk", WriteFeaturesMarkFDK.kMkmkFeatureFileName),
                ("abvm", WriteFeaturesMarkFDK.kAbvmFeatureFileName),
                ("blwm", WriteFeaturesMarkFDK.kBlwmFeatureFileName),
            ]:
                if os.path.exists(os.path.join(self.style.directory, filename)):
                    lines.append(
                        "feature %(tag)s { include (%(path)s); } %(tag)s;" % {
                            "tag": feature_name,
                            "path": filename,
                        }
                    )
            f.writelines(i + "\n" for i in lines)


class Feature(object):
    NAME_TO_CLASS_MAP = {
        "classes": FeatureClasses,
        "tables": FeatureTables,
        "languagesystems": FeatureLanguagesystems,
        "kern": FeatureKern,
        "mark": FeatureMark,
        "mI_variant_matches": FeatureMatches,
        "WeightClass": FeatureWeightClass,
        "features": FeatureReferences,
    }
    def __new__(cls, project, name, style=None, filename_group=None):
        F = cls.NAME_TO_CLASS_MAP.get(name, BaseFeature)
        return F(project, name, style, filename_group)
