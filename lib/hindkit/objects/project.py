import os, argparse, subprocess, collections, errno
import fontTools.ttLib
import hindkit as kit

class Version(object):
    def __init__(self, release, commit, build):
        self.release = release
        self.commit = commit
        self.build = build

class Project(object):

    directories = {
        "sources": "",
        "masters": "masters",
        "styles": "styles",
        "GOADB": "GlyphOrderAndAliasDB",
        "features": "features",
        "intermediates": "intermediates",
        "products": "products",
        "misc": "misc",
        "output": "/Library/Application Support/Adobe/Fonts",
    }

    @classmethod
    def temp(cls, abstract_path):
        return os.path.join(cls.directories["intermediates"], abstract_path)

    def __init__(
        self,
        family,
        target_tag = None,
        release_commit = None, # (65535, 999)
        fontrevision = "1.000",
        options = {},
    ):

        self.family = family
        self.family.project = self

        self.target_tag = kit.fallback(target_tag, self.family.source_tag)

        if release_commit:
            release, commit = release_commit
            self.version = Version(release, commit, 1)
            self.version_last = Version(None, None, None)
            version_record_path = kit.relative_to_cwd(
                "version{}.txt".format(
                    "-" + self.target_tag
                    if self.target_tag
                    else ""
                )
            )
            try:
                with open(version_record_path, "r") as f:
                    for line in f.read().splitlines():
                        k, _, v = line.partition(" ")
                        setattr(self.version_last, k, int(v))
            except IOError as e:
                if e.errno == errno.ENOENT:
                    pass
                else:
                    raise
            if (self.version.release, self.version.commit) == (self.version_last.release, self.version_last.commit):
                self.version.build = self.version_last.build + 1
            with open(version_record_path, "w") as f:
                for k in ["release", "commit", "build"]:
                    f.write("{} {}\n".format(k, getattr(self.version, k)))
            self.fontrevision = "{}.{}".format(
                self.version.release, str(self.version.commit).zfill(3),
            )
            self.version_string = "{}b{}".format(
                self.fontrevision, self.version.build,
            )
        else:
            self.version = None
            self.version_last = None
            self.fontrevision = fontrevision
            self.version_string = None

        # (light_min, light_max), (bold_min, bold_max)
        self.adjustment_for_matching_mI_variants = None

        self.abbrs_of_scripts_to_match_mI_variants = []
        self.script_abbr_current = None

        self.options = {

            "prepare_masters": True,
            "prepare_styles": True,
            "prepare_features": True,
            "compile": True,

            "prepare_kerning": False,
            "prepare_mark_positioning": False,
                "prepare_mark_to_mark_positioning": True,

            "match_mI_variants": 0,
                "match_mI_variants_for_scripts": None,
                "position_marks_for_mI_variants": False,

            "run_makeinstances": True,
            "do_normalize": True,
            "run_checkoutlines": True,
            "run_autohint": False,
            "build_ttf": False,

            "override_GDEF": True,
            "override_x_and_cap_heights": False,

            "do_style_linking": False,
            "use_mac_name_records": False,

            "use_os_2_version_4": False,
                "prefer_typo_metrics": False,
                "is_width_weight_slope_only": False,

            "additional_unicode_range_bits": [],
            "additional_code_pages": [],

        }

        self.options.update(options)

        self.glyph_data = kit.GlyphData()

        self.designspace = kit.DesignSpace(self)
        self.fmndb = kit.Fmndb(self)

        self._finalize_options()

    def _finalize_options(self):

        parser = argparse.ArgumentParser(
            description = "execute `AFDKOPython build.py` to run stages as specified in build.py, or append arguments to override."
        )
        parser.add_argument(
            "--test", action = "store_true",
            help = "run a minimum and fast build process.",
        )
        parser.add_argument(
            "--stages", action = "store",
            help = '"1" for "prepare_masters", "2" for "prepare_styles", "3" for "prepare_features", and "4" for "compile".',
        )
        parser.add_argument(
            "--options", action = "store",
            help = '"0" for none, "1" for "makeinstances", "2" for "checkoutlines", and "3" for "autohint".',
        )
        self.args = parser.parse_args()

        if self.args.stages:
            stages = str(self.args.stages)
            self.options["prepare_masters"] = "1" in stages
            self.options["prepare_styles"] = "2" in stages
            self.options["prepare_features"] = "3" in stages
            self.options["compile"] = "4" in stages
        if self.args.options:
            options = str(self.args.options)
            self.options["run_makeinstances"] = "1" in options
            self.options["run_checkoutlines"] = "2" in options
            self.options["run_autohint"] = "3" in options
        if self.args.test:
            self.options["run_makeinstances"] = False
            self.options["run_checkoutlines"] = False
            self.options["run_autohint"] = False
            self.options["build_ttf"] = False

        styles = self.family.styles
        if self.family.masters:
            if not self.options["run_makeinstances"]:
                styles = [i for i in self.family.styles if i.master]
        else:
            self.options["prepare_masters"] = False
            self.options["run_makeinstances"] = False

        if not styles:
            self.options["prepare_styles"] = False

        self.products = [i.produce(self, file_format="OTF") for i in styles]
        if self.options["build_ttf"]:
            self.products.extend(
                i.produce(self, file_format="TTF", subsidiary=True)
                for i in styles
            )

        if not self.products:
            self.options["compile"] = False

        for product in self.products:
            directory_parts = [
                "TEST" if self.args.test else None,
                self.family.name_postscript,
                self.fontrevision,
                self.target_tag,
                product.file_format,
            ]
            product.abstract_directory = os.path.join(
                product.abstract_directory,
                "-".join([_f for _f in directory_parts if _f]),
            )

        if self.options["match_mI_variants"]:
            self.abbrs_of_scripts_to_match_mI_variants = [
                kit.constants.SCRIPT_NAMES_TO_SCRIPTS[i].abbr
                for i in kit.fallback(
                    self.options["match_mI_variants_for_scripts"],
                    [self.family.script.name],
                )
            ]
            if len(self.abbrs_of_scripts_to_match_mI_variants) == 1:
                self.script_abbr_current = self.abbrs_of_scripts_to_match_mI_variants[0]
            else:
                raise NotImplementedError("[NOT IMPLEMENTED] Can't match mI variants for more than one script.")

    def reset_directory(self, name, temp=False):
        path = self.directories[name]
        if temp:
            path = self.temp(path)
        kit.remove(path)
        kit.makedirs(path)

    def build(self):

        self.reset_directory("intermediates")

        if self.options["prepare_masters"]:

            # self.reset_directory("masters", temp=True)

            for master in self.family.masters:
                master.prepare()
                if hasattr(master, "postprocess"):
                    master.postprocess()
                    master.refresh_groups()

            for master in self.family.masters:
                master.save()

        if self.options["prepare_styles"]:

            # self.reset_directory("styles", temp=True)

            self.family.prepare_styles()

        if self.options["prepare_features"]:

            # self.reset_directory("features", temp=True)

            if self.family.styles[0].file_format == "UFO":
                reference_font = self.products[0].style.open()
                self.family.info.unitsPerEm = reference_font.info.unitsPerEm
            elif self.family.styles[0].file_format == "OTF":
                reference_font = fontTools.ttLib.TTFont(self.products[0].style.get_path())
                self.family.info.unitsPerEm = reference_font["head"].unitsPerEm

            self.feature_classes = kit.FeatureClasses(self)
            self.feature_tables = kit.FeatureTables(self)
            self.feature_languagesystems = kit.FeatureLanguagesystems(self)
            self.feature_gsub = kit.FeatureGSUB(self)
            self.feature_gpos = kit.FeatureGPOS(self)

            self.feature_classes.prepare()
            self.feature_tables.prepare()
            self.feature_languagesystems.prepare()
            self.feature_gsub.prepare()
            self.feature_gpos.prepare()

            for product in (i for i in self.products if i.file_format == "OTF"):

                self.feature_kern = kit.FeatureKern(self, style=product.style)
                self.feature_mark = kit.FeatureMark(self, style=product.style)
                self.feature_matches = kit.FeatureMatches(self, style=product.style)
                self.feature_OS2_extension = kit.FeatureOS2Extension(self, style=product.style)
                self.feature_name_extension = kit.FeatureNameExtension(self, style=product.style)
                self.features_references = kit.FeatureReferences(self, style=product.style)
                self.features_references._extension = ""

                if self.options["prepare_kerning"]:
                    self.feature_kern.prepare()
                if self.options["prepare_mark_positioning"]:
                    self.feature_mark.prepare()
                if self.options["match_mI_variants"]:
                    self.feature_matches.prepare()
                self.feature_OS2_extension.prepare()
                self.feature_name_extension.prepare()
                self.features_references.prepare()

        if self.options["compile"]:

            # self.reset_directory("products", temp=True)

            self.fmndb.prepare()

            for product in self.products:
                if not product.subsidiary:
                    product.generate()

            for product in self.products:
                if product.file_format == "TTF":
                    subprocess.call([
                        "open",
                        "-a", "Glyphs.app",
                        product.style.get_path()
                    ])
            for product in self.products:
                if product.file_format == "TTF":
                    product.generate()

            products_built = [i for i in self.products if i.built]

        client_data = self.family.get_client_data()

        if client_data.name == "Google Fonts" and not self.args.test:

            with open(kit.relative_to_package("data/template-OFL.txt")) as f:
                template = f.read()
            with open(kit.relative_to_cwd("OFL.txt"), "w") as f:
                f.write(template.format(client_data.tables["name"][0]))

            file_format_to_paths = collections.defaultdict(list)
            for product in products_built:
                file_format_to_paths[product.file_format].append(product.get_path(temp=False))
            for file_format, paths in list(file_format_to_paths.items()):
                archive_filename = "{}-{}-{}.zip".format(
                    self.family.name_postscript,
                    self.fontrevision.replace(".", ""),
                    file_format,
                )
                archive_path = os.path.join(self.directories["products"], archive_filename)
                kit.remove(archive_path)
                subprocess.call(["zip", "-j", archive_path] + paths)
                print("[ZIPPED]", archive_path)
                subprocess.call(["ttx", "-fq"] + paths)
                print("[TTX DUMPED]")
                for path in paths:
                    kit.remove(path)
                    print("[REMOVED]", path)
