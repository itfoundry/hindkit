#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, argparse, subprocess, collections
import fontTools.ttLib
import hindkit as kit

class Project(object):

    directories = {
        'masters': 'masters',
        'styles': 'styles',
        'features': 'features',
        'temp': 'intermediates',
        'products': 'products',
        'output': '/Library/Application Support/Adobe/Fonts',
    }

    def __init__(
        self,
        family,
        fontrevision = '1.000',
        options = {},
    ):

        self.family = family
        self.family.builder = self

        self.fontrevision = fontrevision

        self.devanagari_offset_matrix = ((0, 0), (0, 0))

        self.options = {

            'prepare_masters': True,
            'prepare_styles': True,
            'prepare_features': True,
            'compile': True,

            'prepare_kerning': False,
            'prepare_mark_positioning': False,
            'prepare_mark_to_mark_positioning': True,
            'match_mI_variants': False,
            'position_marks_for_mI_variants': False,

            'run_makeinstances': len(self.family.styles) > len(self.family.masters),
            'run_checkoutlines': True,
            'run_autohint': False,
            'build_ttf': False,

            'override_GDEF': True,

            'do_style_linking': False,

            'use_os_2_version_4': False,
            'prefer_typo_metrics': False,
            'is_width_weight_slope_only': False,

        }

        self.options.update(options)

        self.glyphdata = kit.GlyphData('glyphorder.txt')
        self.glyph_order = self.glyphdata.glyph_order
        self.glyph_order_trimmed = None

        self.designspace = kit.DesignSpace(self)
        self.feature_classes = kit.Feature(
            self,
            'classes',
            optional_file_names = ['classes_suffixing'],
        )
        self.feature_tables = kit.Feature(self, 'tables')
        self.feature_languagesystems = kit.Feature(self, 'languagesystems')
        self.feature_gsub = kit.Feature(
            self,
            'GSUB',
            optional_file_names = ['GSUB_lookups', 'GSUB_prefixing'],
        )
        self.feature_gpos = kit.Feature(self, 'GPOS')
        self.feature_weight_class = kit.Feature(self, 'WeightClass')
        self.features_references = kit.Feature(self, 'features')
        self.features_references.filename_extension = None
        self.fmndb = kit.Fmndb(self)
        self.goadb_trimmed = kit.Goadb(
            self,
            self.glyphdata,
            'GlyphOrderAndAliasDB_trimmed',
        )
        if self.options['build_ttf']:
            self.goadb_trimmed_ttf = kit.Goadb(
                self,
                self.glyphdata,
                'GlyphOrderAndAliasDB_trimmed_ttf',
                for_ttf = True,
            )

    def temp(self, abstract_path):
        return os.path.join(self.directories['intermediates'], abstract_path)

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

        if self.options['run_makeinstances']:
            styles = self.family.styles
        else:
            styles = self.family.get_styles_that_are_directly_derived_from_masters()

        self.products = [style.produce(self, file_format='OTF') for style in styles]
        if self.options['build_ttf']:
            self.products.extend(style.produce(self, file_format='TTF') for style in styles)

    def trim_glyph_names(self, names, reference_names):
        not_covered_glyphs = [
            name
            for name in reference_names
            if name not in names
        ]
        if not_covered_glyphs:
            raise SystemExit(
                'Some glyphs are not covered by the GOADB: ' +
                ' '.join(not_covered_glyphs)
            )
        names_trimmed = [
            name
            for name in names
            if name in reference_names
        ]
        return names_trimmed

    def build(self):

        kit.makedirs(self.directories['intermediates'])

        self._finalize_options()

        if self.options['prepare_masters']:

            path = self.temp(self.directories['masters'])
            kit.remove(path)
            kit.makedirs(path)

            for master in self.family.masters:
                master.prepare()

            reference_font = self.family.masters[0].open()
            self.glyph_order_trimmed = self.trim_glyph_names(
                self.glyph_order,
                reference_font.glyphOrder
            )

            for master in self.family.masters:
                font = master.open()
                font.lib['public.glyphOrder'] = self.glyph_order_trimmed
                font.lib.pop('com.schriftgestaltung.glyphOrder', None)
                master.save_as(font)

        if self.options['prepare_styles']:

            path = self.temp(self.directories['styles'])
            kit.remove(path)
            kit.makedirs(path)
            self.family.prepare_styles()

        if self.options['prepare_features']:

            path = self.temp(self.directories['features'])
            kit.remove(path)
            kit.makedirs(path)

            for product in self.products:
                product.style.temp = True

            reference_font = self.products[0].style.open()
            self.family.info.unitsPerEm = reference_font.info.unitsPerEm

            self.feature_classes.prepare()
            self.feature_tables.prepare()
            self.feature_languagesystems.prepare()
            self.feature_gsub.prepare()

            for product in self.products:
                style = product.style
                self.feature_gpos.prepare(style=style)
                self.feature_weight_class.prepare(style=style)
                self.features_references.prepare(style=style)

        if self.options['compile']:
            kit.makedirs(self.directories['products'])
            self.fmndb.prepare()
            for product in self.products:
                product.style.temp = True
                product.prepare()


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
