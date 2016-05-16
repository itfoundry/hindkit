#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, argparse, subprocess
import fontTools.ttLib
import hindkit as kit

class Project(object):

    directories = {
        'masters': 'masters',
        'styles': 'styles',
        'features': 'features',
        'intermediates': 'intermediates',
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
        self.family.project = self

        self.fontrevision = fontrevision

        # (light_min, light_max), (bold_min, bold_max)
        # self.adjustment_for_matching_mI_variants = (0, 0), (0, 0)

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
            self.options['build_ttf'] = False

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

        # self._finalize_options()

        if self.options['prepare_masters']:

            path = self.temp(self.directories['masters'])
            kit.remove(path)
            kit.makedirs(path)

            for master in self.family.masters:
                master.prepare()
                try:
                    master.postprocess()
                except AttributeError:
                    pass

            reference_font = self.family.masters[0].open()
            self.glyph_data.glyph_order_trimmed = self.trim_glyph_names(
                self.glyph_data.glyph_order,
                reference_font.glyphOrder,
            )

            for master in self.family.masters:
                font = master.open()
                font.lib['public.glyphOrder'] = self.glyph_data.glyph_order_trimmed
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

            self.feature_classes = kit.Feature(
                self, 'classes',
                subsidiary_filenames = ['classes_suffixing'],
            )
            self.feature_tables = kit.Feature(
                self, 'tables',
            )
            self.feature_languagesystems = kit.Feature(
                self, 'languagesystems',
            )
            self.feature_gsub = kit.Feature(
                self, 'GSUB',
                subsidiary_filenames = ['GSUB_lookups', 'GSUB_prefixing'],
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
            kit.makedirs(self.directories['products'])
            self.fmndb.prepare()
            for product in self.products:
                product.style.temp = True
                if product.file_format == 'TTF':
                    subprocess.call(['open', product.style.path])
            for product in self.products:
                product.prepare()
