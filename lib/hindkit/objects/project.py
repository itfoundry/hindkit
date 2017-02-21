#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, argparse, subprocess, collections
import hindkit as kit

class Project(object):

    directories = {
        "sources": "",
        "masters": "masters",
        "styles": "styles",
        "features": "features",
        "temp": "intermediates",
        "products": "products",
        "output": "/Library/Application Support/Adobe/Fonts",
    }

    def __init__(
        self,
        family,
        fontrevision = '1.000',
        options = {},
    ):

        self.family = family
        self.family.project = self

        self.fontrevision = fontrevision

        # (light_min, light_max), (bold_min, bold_max)
        self.adjustment_for_matching_mI_variants = (0, 0), (0, 0)

        self.options = {

            'prepare_masters': True,
            'prepare_styles': True,
            'prepare_features': True,
            'compile': True,

            'prepare_kerning': False,
            'prepare_mark_positioning': False,
                'prepare_mark_to_mark_positioning': True,

            'match_mI_variants': False, # 'single' or 'sequence'
                'position_marks_for_mI_variants': False,

            'run_makeinstances': True,
            'run_checkoutlines': True,
            'run_autohint': False,
            'build_ttf': False,

            'override_GDEF': True,

            'do_style_linking': False,
            'omit_mac_name_records': True,

            'use_os_2_version_4': False,
                'prefer_typo_metrics': False,
                'is_width_weight_slope_only': False,

            'additional_unicode_range_bits': [],
            'additional_code_pages': [],

        }

        self.options.update(options)

        self.glyph_data = kit.GlyphData()

        self.designspace = kit.DesignSpace(self)
        self.fmndb = kit.Fmndb(self)
        self.goadb_trimmed = kit.Goadb(self, 'GlyphOrderAndAliasDB_trimmed')
        if self.options['build_ttf']:
            self.goadb_trimmed_ttf = kit.Goadb(
                self, 'GlyphOrderAndAliasDB_trimmed_ttf', for_ttf = True,
            )

        self._finalize_options()

    def temp(self, abstract_path):
        return os.path.join(self.directories['temp'], abstract_path)

    def _finalize_options(self):

        parser = argparse.ArgumentParser(
            description = 'execute `AFDKOPython build.py` to run stages as specified in build.py, or append arguments to override.'
        )
        parser.add_argument(
            '--test', action = 'store_true',
            help = 'run a minimum and fast build process.',
        )
        parser.add_argument(
            '--stages', action = 'store',
            help = '"1" for "prepare_masters", "2" for "prepare_styles", "3" for "prepare_features", and "4" for "compile".',
        )
        parser.add_argument(
            '--options', action = 'store',
            help = '"0" for none, "1" for "makeinstances", "2" for "checkoutlines", and "3" for "autohint".',
        )
        self.args = parser.parse_args()

        if self.args.stages:
            stages = str(self.args.stages)
            self.options['prepare_masters'] = '1' in stages
            self.options['prepare_styles'] = '2' in stages
            self.options['prepare_features'] = '3' in stages
            self.options['compile'] = '4' in stages
        if self.args.options:
            options = str(self.args.options)
            self.options['run_makeinstances'] = '1' in options
            self.options['run_checkoutlines'] = '2' in options
            self.options['run_autohint'] = '3' in options
        if self.args.test:
            self.options['run_makeinstances'] = False
            self.options['run_checkoutlines'] = False
            self.options['run_autohint'] = False
            self.options['build_ttf'] = False

        if self.options['run_makeinstances']:
            styles = self.family.styles
        else:
            styles = [i for i in self.family.styles if i.master]

        self.products = [i.produce(self, file_format='OTF') for i in styles]
        if self.options['build_ttf']:
            self.products.extend(
                i.produce(self, file_format='TTF', incidental=True)
                for i in styles
            )

        if len(set(i.file_format for i in self.products)) > 1:
            for product in self.products:
                product.abstract_directory = os.path.join(
                    product.abstract_directory, product.extension,
                )

    def trim_glyph_names(self, names, reference_names):
        not_covered_glyphs = [
            name
            for name in reference_names
            if name not in names
        ]
        if not_covered_glyphs:
            print(
                "[WARNING] Some glyphs are not covered by the GOADB: " +
                " ".join(not_covered_glyphs)
            )
            if self.options['build_ttf']:
                raise SystemExit("[EXIT] GOADB must match the glyph set exactly for compiling TTFs.")
        names_trimmed = [
            name
            for name in names
            if name in reference_names
        ]
        return names_trimmed

    def update_glyphOrder(self, font):
        defcon_font = font.open()
        defcon_font.lib['public.glyphOrder'] = self.glyph_data.glyph_order_trimmed
        defcon_font.lib.pop('com.schriftgestaltung.glyphOrder', None)
        font.save()

    def reset_directory(self, name, temp=False):
        if temp:
            path = self.temp(self.directories[name])
        else:
            path = self.directories[name]
        kit.remove(path)
        kit.makedirs(path)

    def build(self):

        self.reset_directory("temp")
        for name in ["masters", "styles", "features", "products"]:
            self.reset_directory(name, temp=True)

        if self.options['prepare_masters']:

            for master in self.family.masters:
                master.prepare()
                try:
                    master.postprocess()
                except AttributeError:
                    pass

            for master in self.family.masters:
                master.save()

        if self.options['prepare_styles']:

            self.family.prepare_styles()

        if self.options['prepare_features']:

            if self.family.styles[0].file_format == "UFO":
                reference_font = self.products[0].style.open()
                self.family.info.unitsPerEm = reference_font.info.unitsPerEm

            self.feature_classes = kit.Feature(
                self, 'classes',
                filename_group = ['classes', 'classes_suffixing'],
            )
            self.feature_tables = kit.Feature(
                self, 'tables',
            )
            self.feature_languagesystems = kit.Feature(
                self, 'languagesystems',
            )
            self.feature_gsub = kit.Feature(
                self, 'GSUB',
                filename_group = ['GSUB_prefixing', 'GSUB_lookups', 'GSUB'],
            )

            self.feature_classes.prepare()
            self.feature_tables.prepare()
            self.feature_languagesystems.prepare()
            self.feature_gsub.prepare()

            for product in (i for i in self.products if i.file_format == 'OTF'):

                self.feature_kern = kit.Feature(
                    self, 'kern', product.style,
                )
                self.feature_mark = kit.Feature(
                    self, 'mark', product.style,
                )
                self.feature_matches = kit.Feature(
                    self, 'mI_variant_matches', product.style,
                )
                self.feature_weight_class = kit.Feature(
                    self, 'WeightClass', product.style,
                )
                self.features_references = kit.Feature(
                    self, 'features', product.style,
                )
                self.features_references.extension = ''

                if self.options['prepare_kerning']:
                    self.feature_kern.prepare()
                if self.options['prepare_mark_positioning']:
                    self.feature_mark.prepare()
                if self.options['match_mI_variants']:
                    self.feature_matches.prepare()
                self.feature_weight_class.prepare()
                self.features_references.prepare()

        if self.options['compile']:

            self.fmndb.prepare()

            for product in self.products:
                if not product.incidental:
                    if self.options['build_ttf']:
                        defcon_font = product.style.open()
                        defcon_font.groups.clear()
                        defcon_font.kerning.clear()
                        product.style.save()
                    if (
                        self.options['run_checkoutlines'] or
                        self.options['run_autohint']
                    ) and self.family.styles[0].file_format == "UFO":
                        options = {
                            'doOverlapRemoval': self.options['run_checkoutlines'],
                            'doAutoHint': self.options['run_autohint'],
                            'allowDecimalCoords': False,
                        }
                        _updateInstance(options, product.style.get_path())
                product.generate()

            for product in self.products:
                if product.file_format == 'TTF':
                    subprocess.call(['open', product.style.path])
            for product in self.products:
                if product.file_format == 'TTF':
                    product.prepare()

        client_data = self.family.get_client_data()

        if client_data.name == "Google Fonts":

            with open(kit.relative_to_package("data/template-OFL.txt")) as f:
                template = f.read()
            with open(kit.relative_to_cwd("OFL.txt"), "w") as f:
                f.write(template.format(client_data.tables["name"][0]))

            file_format_to_paths = collections.defaultdict(list)
            for product in products_built:
                file_format_to_paths[product.file_format].append(product.get_path(temp=False))
            for file_format, paths in file_format_to_paths.items():
                archive_filename = "{}-{}-{}.zip".format(
                    self.family.name_postscript,
                    self.fontrevision.replace(".", ""),
                    file_format,
                )
                archive_path = os.path.join(self.directories["products"], archive_filename)
                kit.remove(archive_path)
                subprocess.call(["zip", archive_path] + paths)
                subprocess.call(["ttx", "-fq"] + paths)
                for path in paths:
                    kit.remove(path)


# makeInstancesUFO.updateInstance

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
