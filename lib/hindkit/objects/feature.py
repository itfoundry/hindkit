#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, collections, itertools, re
import WriteFeaturesKernFDK, WriteFeaturesMarkFDK
import hindkit as kit

class BaseFeature(kit.BaseFile):

    _name = "features"

    def __init__(self, project, name=None, style=None):
        if style:
            abstract_directory = style.abstract_directory
        else:
            abstract_directory = kit.Project.directories["features"]
        super(BaseFeature, self).__init__(
            name = kit.fallback(name, self._name),
            file_format = "FEA",
            project = project,
            extra_filenames = self._extra_filenames,
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

    _name = "classes"
    _extra_filenames = [], ["classes_suffixing"]

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
                    (m.CLASS_NAME_BASES_FOR_LONG_mII, f.bases_for_long_mII, m.BASE_NAMES_FOR_LONG_mII),
                ])
                if self.project.options["match_mI_variants"] > 1:
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
            with open(self.get_path(), "w") as f:
                f.writelines(i + "\n" for i in lines)


class FeatureTables(BaseFeature):

    _name = "tables"

    def generate(self):

        info = self.project.family.info
        client_data = self.project.family.get_client_data()

        lines = []
        tables = collections.OrderedDict([
            ("hhea", []),
            ("OS/2", []),
            ("GDEF", []),
            ("name", []),
        ])

        tables["OS/2"].append("include (OS2Extension.fea);")

        tables["OS/2"].append("fsType {};".format(client_data.tables["OS/2"]["fsType"]))

        unicode_range_bits = set(
            i for i in
            self.project.family.script.unicode_range_bits +
            self.project.options["additional_unicode_range_bits"]
            if i is not None
        )
        if unicode_range_bits:
            tables["OS/2"].append(
                "UnicodeRange {};".format(
                    " ".join(str(i) for i in sorted(unicode_range_bits))
                )
            )

        vender_id = client_data.tables["OS/2"]["Vendor"]
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

            if client_data.vertical_metrics_strategy == "Google Fonts":
                if info.openTypeOS2TypoAscender is None:
                    info.openTypeOS2TypoAscender = info.openTypeHheaAscender
                if info.openTypeOS2TypoDescender is None:
                    info.openTypeOS2TypoDescender = info.openTypeHheaDescender
                if info.openTypeOS2TypoLineGap is None:
                    info.openTypeOS2TypoLineGap = info.openTypeHheaLineGap
            elif client_data.vertical_metrics_strategy == "ITF":
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
                info.openTypeOS2WinDescent = abs(info.openTypeHheaDescender) + info.openTypeHheaLineGap

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
            if self.project.options["prepare_mark_positioning"] or os.path.exists(os.path.join(self.get_directory(), "classes.fea")):
                GDEF_records["marks"] = "@{}".format(WriteFeaturesMarkFDK.kCombMarksClassName)
            classes_suffixing_path = os.path.join(self.get_directory(), "classes_suffixing.fea")
            if os.path.exists(classes_suffixing_path):
                lines_without_comment = []
                with open(classes_suffixing_path) as f:
                    lines_without_comment = [line.partition("#")[0].strip() for line in f]
                content_without_comment = "\n".join(lines_without_comment)
                for k, v in [
                    ("bases", "@BASES_GDEF"),
                    ("marks", "@COMBINING_MARKS_GDEF"),
                ]:
                    if v in content_without_comment:
                        GDEF_records[k] = v
            tables["GDEF"].extend([
                "GlyphClassDef {bases}, {ligatures}, {marks}, {components};".format(**GDEF_records)
            ])

        tables["name"].extend(
            "nameid {} \"{}\";".format(
                name_id,
                content.encode("unicode_escape").replace("\\x", "\\00").replace("\\u", "\\")
            )
            for name_id, content in sorted(client_data.tables["name"].items())
            if content
        )

        for name, entries in tables.items():
            if entries:
                lines.append("table %s {" % name)
                lines.extend("  " + i for i in entries)
                lines.append("} %s;" % name)

        if lines:
            with open(self.get_path(), "w") as f:
                f.writelines(i + "\n" for i in lines)


class FeatureLanguagesystems(BaseFeature):

    _name = "languagesystems"

    def generate(self):
        lines = ["languagesystem DFLT dflt;"]
        for tag in self.project.family.script.tags:
            lines.append("languagesystem {} dflt;".format(tag))
        if lines:
            with open(self.get_path(), "w") as f:
                f.writelines(i + "\n" for i in lines)


class FeatureGSUB(BaseFeature):

    _name = "GSUB"
    _extra_filenames = ["GSUB_prefixing", "GSUB_lookups"], []


class FeatureKern(BaseFeature):

    _name = "kern"

    def generate(self):
        WriteFeaturesKernFDK.kKernFeatureFileName = self.filename_with_extension
        WriteFeaturesKernFDK.KernDataClass(
            font = self.style.open(),
            folderPath = self.style.get_directory(),
        )
        if hasattr(self, "postprocess"):
            kern_path = self.get_path()
            if os.path.exists(kern_path):
                with open(kern_path) as f:
                    content = f.read()
                with open(kern_path, "w") as f:
                    f.write(self.postprocess(content))


class FeatureMark(BaseFeature):

    _name = "mark"

    def generate(self):
        WriteFeaturesMarkFDK.kMarkFeatureFileName = self.filename_with_extension
        WriteFeaturesMarkFDK.MarkDataClass(
            font = self.style.open(),
            folderPath = self.style.get_directory(),
            trimCasingTags = False,
            genMkmkFeature = self.project.options["prepare_mark_to_mark_positioning"],
            writeClassesFile = True,
            indianScriptsFormat = self.project.family.script.is_indic,
        )


class FeatureOS2Extension(BaseFeature):

    _name = "OS2Extension"

    def generate(self):
        with open(self.get_path(), "w") as f:
            f.write("WeightClass {};\n".format(str(self.style.weight_class)))
            f.write("WidthClass {};\n".format(str(self.style.width_class)))
            if self.project.options["override_x_and_cap_heights"]:
                f.write("XHeight {};\n".format(str(self.style.x_height)))
                f.write("CapHeight {};\n".format(str(self.style.cap_height)))


class FeatureMatches(BaseFeature):

    _name = "mI_variant_matches"

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

    CLASS_NAME_mI_VARIANTS = "mI_VARIANTS"
    CLASS_NAME_BASES_ALIVE = "BASES_ALIVE"
    CLASS_NAME_BASES_DEAD = "BASES_DEAD"
    CLASS_NAME_BASES_FOR_LONG_mII = "BASES_FOR_LONG_mII"

    CONSONANTS_ALIVE = [
        i + "A" for i in kit.constants.CONSONANT_STEMS
    ] + "GAbar JAbar DDAbar BAbar ZHA YAheavy DDAmarwari".split()
    CONSONANTS_DEAD = kit.constants.CONSONANT_STEMS

    mI_VARIANT_NAME_PATTERN = r"mI\.\d\d"

    BASE_NAMES_ALIVE = None
    BASE_NAMES_DEAD = None
    BASE_NAMES_FOR_LONG_mII = None

    mI_ANCHOR_NAME = "abvm.i"
    POTENTIAL_abvm_ANCHOR_NAMES = ["abvm.e", "abvm"]

    def __init__(self, project, style=None):
        super(FeatureMatches, self).__init__(project, style=style)
        self._bases_alive = None
        self._bases_dead = None

    def generate(self):

        self.font = self.style.open()

        mI_variant_names = self.font.groups.get(self.CLASS_NAME_mI_VARIANTS)
        if not mI_variant_names:
            raise ValueError("[WARNING] No variants for mI.")
        # The order in glyph classes can't be trusted:
        self.matches = [self.Match(self, i) for i in sorted(mI_variant_names)]
        # self.not_matched = self.Match(self, None)

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

        adjustment = self._get_adjustment()
        if adjustment is None:
            pass
        elif isinstance(adjustment, tuple):
            extremes = adjustment
            targets = [base.target for base in self.bases]
            TARGET_MIN = min(targets)
            TARGET_MAX = max(targets)
            for i, base in enumerate(self.bases):
                ratio = (base.target - TARGET_MIN) / (TARGET_MAX - TARGET_MIN)
                adjustment = extremes[0] + (extremes[1] - extremes[0]) * ratio
                self.bases[i].target += adjustment
        else:
            for i, base in enumerate(self.bases):
                self.bases[i].target += adjustment

        self.tolerance = self._get_stem_position(
            self.font[self.style.family.script.abbr + "VA"]
        ) * 0.5

        for base in self.bases:
            match = self.match_mI_variants(base)
            if match:
                match.bases.append(base)

        self.name_default = self.style.family.script.abbr + "mI"

        self.substitute_rule_lines = []
        for match in self.matches:
            self.output_mI_variant_matches(match)
        with open(self.get_path(), "w") as f:
            f.writelines([
                "lookup %s {\n" % self.name,
                # "  lookupflag IgnoreMarks;\n",
            ])
            f.writelines("  " + l + "\n" for l in self.substitute_rule_lines)
            # f.writelines(
            #     "  # " + " ".join(g.name for g in b.glyphs) + "\n"
            #     for b in self.not_matched.bases
            # )
            f.writelines([
                # "  lookupflag 0;\n",
                "} %s;\n" % self.name,
            ])

        if self.project.options["match_mI_variants"] == 1 and self.project.options["position_marks_for_mI_variants"]:
            self.output_mark_positioning_for_mI_variants()

    def _get_adjustment(self):
        if self.style.adjustment_for_matching_mI_variants:
            return self.style.adjustment_for_matching_mI_variants
        elif self.project.family.masters and self.project.adjustment_for_matching_mI_variants:
            (light_min, light_max), (bold_min, bold_max) = self.project.adjustment_for_matching_mI_variants
            axis_start = self.project.family.masters[0].location[0]
            axis_end = self.project.family.masters[-1].location[0]
            axis_range = axis_end - axis_start
            if axis_range == 0:
                ratio = 1
            else:
                ratio = (self.style.location[0] - axis_start) / axis_range
            return (
                light_min + (bold_min - light_min) * ratio,
                light_max + (bold_max - light_max) * ratio,
            )
        else:
            return None

    def _get_abvm_position(self, glyph, in_base=True):
        anchor_name_prefix = "" if in_base else "_"
        for potential_anchor_name in self.POTENTIAL_abvm_ANCHOR_NAMES:
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
        return kit.fallback(
            self._bases_alive,
            [
                self.font[i] for i in
                self.font.groups.get(self.CLASS_NAME_BASES_ALIVE, [])
                if ".mU" not in i
            ],
        )

    @property
    def bases_dead(self):
        return kit.fallback(
            self._bases_dead,
            [self.font[i] for i in self.font.groups.get(self.CLASS_NAME_BASES_DEAD, [])]
        )

    def _base_glyph_sequences(self):
        seeds = [self.bases_dead] * (self.project.options["match_mI_variants"] - 1) + [self.bases_alive]
        for sequence in itertools.product(*seeds):
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
                (candidate_enough.overhanging - base.target) <
                (base.target - candidate_short.overhanging) / 3
            ):
                return candidate_enough
            else:
                return candidate_short
        elif base.target <= self.matches[-1].overhanging + self.tolerance:
            return self.matches[-1]
        else:
            # return self.not_matched
            return

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
            self.style.get_directory(),
            "backup--" + WriteFeaturesMarkFDK.kAbvmFeatureFileName,
        )
        abvm_path = os.path.join(
            self.style.get_directory(),
            WriteFeaturesMarkFDK.kAbvmFeatureFileName,
        )
        if os.path.exists(abvm_backup_path):
            kit.copy(abvm_backup_path, abvm_path)
        else:
            kit.copy(abvm_path, abvm_backup_path)

        pattern_begin = re.compile(r"lookup MARK_BASE_%s \{$" % self.mI_ANCHOR_NAME)
        pattern_end = re.compile(r"\} MARK_BASE_%s;$" % self.mI_ANCHOR_NAME)

        match_dict = {match.tag: match for match in self.matches}
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

    _name = "features"

    def generate(self):
        with open(self.get_path(), "w") as f:
            lines = ["table head { FontRevision %s; } head;" % self.project.fontrevision]
            for feature in [
                self.project.feature_classes,
                self.project.feature_tables,
                self.project.feature_languagesystems,
                self.project.feature_gsub,
            ]:
                for i in feature.file_group:
                    if os.path.exists(i.get_path()):
                        lines.append(
                            "include ({});".format(
                                os.path.relpath(i.get_path(), self.style.get_directory())
                            )
                        )
            if os.path.exists(self.project.feature_kern.get_path()):
                lines.append(
                    "feature %(tag)s { include (%(path)s); } %(tag)s;" % {
                        "tag": "kern", # "dist" if self.project.family.script.is_indic ?
                        "path": os.path.relpath(self.project.feature_kern.get_path(), self.style.get_directory()),
                    }
                )
            if os.path.exists(os.path.join(self.style.get_directory(), WriteFeaturesMarkFDK.kMarkClassesFileName)):
                lines.append("include ({});".format(WriteFeaturesMarkFDK.kMarkClassesFileName))
            for feature_name, filename in [
                ("mark", WriteFeaturesMarkFDK.kMarkFeatureFileName),
                ("mkmk", WriteFeaturesMarkFDK.kMkmkFeatureFileName),
                ("abvm", WriteFeaturesMarkFDK.kAbvmFeatureFileName),
                ("blwm", WriteFeaturesMarkFDK.kBlwmFeatureFileName),
            ]:
                if os.path.exists(os.path.join(self.style.get_directory(), filename)):
                    lines.append(
                        "feature %(tag)s { include (%(path)s); } %(tag)s;" % {
                            "tag": feature_name,
                            "path": filename,
                        }
                    )
            for line in lines:
                print(line)
                f.write(line + "\n")
