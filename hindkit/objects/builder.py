#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, argparse, subprocess, collections

import fontTools.ttLib, mutatorMath.ufo.document

import hindkit as kit

class Builder(object):

    directories = {
        'masters': 'masters',
        'styles': 'styles',
        'features': 'features',
        'build': 'build',
        'temp': 'temp',
        'Adobe/Fonts': '/Library/Application Support/Adobe/Fonts',
    }

    def __init__(
        self,
        family,
        fontrevision = '1.000',
        vertical_metrics = {},
        options = {},
    ):

        self.family = family
        self.fontrevision = fontrevision

        self.vertical_metrics = {}
        self.vertical_metrics['Ascender'] = vertical_metrics.get('Ascender', 800)
        self.vertical_metrics['Descender'] = vertical_metrics.get('Descender', -200)
        self.vertical_metrics['LineGap'] = vertical_metrics.get('LineGap', 0)
        self.vertical_metrics['TypoAscender'] = vertical_metrics.get('TypoAscender', self.vertical_metrics['Ascender'])
        self.vertical_metrics['TypoDescender'] = vertical_metrics.get('TypoDescender', self.vertical_metrics['Descender'])
        self.vertical_metrics['TypoLineGap'] = vertical_metrics.get('TypoLineGap', self.vertical_metrics['LineGap'])
        self.vertical_metrics['winAscent'] = vertical_metrics.get('winAscent', self.vertical_metrics['Ascender'])
        self.vertical_metrics['winDescent'] = vertical_metrics.get('winDescent', abs(self.vertical_metrics['Descender']))

        self.devanagari_offset_matrix = ((0, 0), (0, 0))

        self.options = {

            'prepare_kerning': False,

            'prepare_mark_positioning': False,
            'prepare_mark_to_mark_positioning': True,
            'match_mI_variants': False,
            'position_marks_for_mI_variants': False,

            'prepare_master': False,
            'postprocess_kerning': False,
            'postprocess_font_file': False,

            'run_stage_prepare_masters': True,
            'run_stage_prepare_styles': True,
            'run_stage_prepare_features': True,
            'run_stage_compile': True,

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

        self.goadb = kit.GlyphData()

    def temp(self, abstract_path):
        return os.path.join(self.directories['temp'], abstract_path)

    def postprocess_kerning(self, original):
        return original

    def postprocess_font_file(self, original):
        return original

    def _check_inputs(self, inputs):
        results = collections.OrderedDict(
            (path, os.path.exists(path))
            for path in inputs
        )
        if not all(results.values()):
            raise SystemExit(
                '\n'.join('{}: {}'.format(k, v) for k, v in results.items())
            )

    def generate_designspace(self, output):

        doc = mutatorMath.ufo.document.DesignSpaceDocumentWriter(
            os.path.abspath(relative_to_cwd(output))
        )

        for i, master in enumerate(self.family.masters):

            doc.addSource(

                path = os.path.abspath(relative_to_cwd(master.path)),
                name = 'master ' + master.name,
                location = {'weight': master.weight_location},

                copyLib    = i == 0,
                copyGroups = i == 0,
                copyInfo   = i == 0,

                # muteInfo = False,
                # muteKerning = False,
                # mutedGlyphNames = None,

            )

        for style in self.styles_to_produce:

            doc.startInstance(
                name = 'instance ' + style.name,
                location = {'weight': style.weight_location},
                familyName = self.family.name,
                styleName = style.name,
                fileName = os.path.abspath(
                    relative_to_cwd(style.path)
                ),
                postScriptFontName = style.full_name_postscript,
                # styleMapFamilyName = None,
                # styleMapStyleName = None,
            )

            doc.writeInfo()

            if self.options['prepare_kerning']:
                doc.writeKerning()

            doc.endInstance()

        doc.save()

    def prepare_styles(self): # STAGE I

        for style in self.styles_to_produce:
            style.temp = True
            kit.makedirs(style.directory)

        if self.options['run_makeinstances']:

            self.designspace.prepare()

            arguments = ['-d', self.temp('font.designspace')]
            if not self.options['run_checkoutlines']:
                arguments.append('-c')
            if not self.options['run_autohint']:
                arguments.append('-a')

            subprocess.call(['makeInstancesUFO'] + arguments)

        else:
            for index, (master, style) in enumerate(zip(self.family.masters, self.styles_to_produce)):
                copy(master.path, style.path)
                font = style.open()
                if font.info.postscriptFontName != style.full_name_postscript:
                    font.info.postscriptFontName = style.full_name_postscript
                    font.save()
                self._simulate_makeInstancesUFO_postprocess(style)

    def _simulate_makeInstancesUFO_postprocess(self, style):
        if self.options['run_checkoutlines'] or self.options['run_autohint']:
            options = {
                'doOverlapRemoval': self.options['run_checkoutlines'],
                'doAutoHint': self.options['run_autohint'],
                'allowDecimalCoords': False,
            }
            _updateInstance(options, style.path)

    def generate_features_GSUB(self, output):
        pass

    def _compile(self, style, build_ttf=False):

        if build_ttf:
            style.input_format = 'TTF'
            style.output_format = 'TTF'

        self._check_inputs([self.temp(style.path), self.temp(self.fmndb.output), self.temp(self.trimmed_goadb.output)])

        # if style.file_name.endswith('.ufo'):
        #     font = style.open_font(is_temp=True)
        #     if font.info.postscriptFontName != style.output_full_name_postscript:
        #         font.info.postscriptFontName = style.output_full_name_postscript
        #         font.save()

        font_path = style.font_path

        arguments = [
            '-f', self.temp(style.path),
            '-o', font_path,
            '-mf', self.temp(self.fmndb.output),
            '-gf', self.temp(self.trimmed_goadb.output),
            '-rev', self.fontrevision,
            '-ga',
            '-omitMacNames',
        ]
        if not self.args.test:
            arguments.append('-r')
        if not self.options['run_autohint']:
            arguments.append('-shw')
        if self.options['do_style_linking']:
            if style.is_bold:
                arguments.append('-b')
            if style.is_italic:
                arguments.append('-i')
        if self.options['use_os_2_version_4']:
            for digit, boolean in [
                ('7', self.options['prefer_typo_metrics']),
                ('8', self.options['is_width_weight_slope_only']),
                ('9', style.is_oblique),
            ]:
                arguments.append('-osbOn' if boolean else '-osbOff')
                arguments.append(digit)

        subprocess.call(['makeotf'] + arguments)

        if self.options['postprocess_font_file'] and os.path.exists(font_path):
            original = fontTools.ttLib.TTFont(font_path)
            postprocessed = self.postprocess_font_file(original)
            postprocessed.save(font_path, reorderTables=False)
            print('[NOTE] `postprocess_font_file` done.')

        destination = self.directories['Adobe Fonts']
        if os.path.exists(font_path) and os.path.isdir(destination):
            copy(font_path, destination)

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
            help = '"1" for "prepare_styles", "2" for "prepare_features", and "3" for "compile".',
        )
        parser.add_argument(
            '--options', action = 'store',
            help = '"0" for none, "1" for "makeinstances", "2" for "checkoutlines", and "3" for "autohint".',
        )
        self.args = parser.parse_args()

        if self.args.stages:
            stages = str(self.args.stages)
            self.options['run_stage_prepare_styles'] = '1' in stages
            self.options['run_stage_prepare_features'] = '2' in stages
            self.options['run_stage_compile'] = '3' in stages
        if self.args.options:
            options = str(self.args.options)
            self.options['run_makeinstances'] = '1' in options
            self.options['run_checkoutlines'] = '2' in options
            self.options['run_autohint'] = '3' in options
        if self.args.test:
            self.options['run_makeinstances'] = False
            self.options['run_checkoutlines'] = False
            self.options['run_autohint'] = False

        self.styles_to_produce = self.family.styles
        if self.family.masters and (not self.options['run_makeinstances']):
            self.styles_to_produce = self.family.get_styles_that_are_directly_derived_from_masters()

    def build(self):

        kit.makedirs(self.directories['temp'])

        self._finalize_options()

        if self.options['run_stage_prepare_styles']:

            if self.options['run_stage_prepare_masters']:

                path = self.temp(self.directories['masters'])
                kit.remove(path)
                kit.makedirs(path)

                for master in self.family.masters:
                    master.prepare(self)

                self.goadb.generate(self.family.masters[0].open())

                for master in self.family.masters:
                    font = master.open()
                    font.lib['public.glyphOrder'] = self.goadb.development_names
                    font.lib.pop('com.schriftgestaltung.glyphOrder', None)
                    master.save_as(font)

            path = self.temp(self.directories['styles'])
            kit.remove(path)
            kit.makedirs(path)
            self.prepare_styles()

        if self.options['run_stage_prepare_features']:

            path = self.temp(kit.paths.FEATURES)
            kit.remove(path)
            kit.makedirs(path)

            kit.objects.FeatureFile(
                'classes',
                extensions = ['classes_suffixing'],
            ).prepare(self)
            kit.objects.FeatureFile('tables').prepare(self)
            kit.objects.FeatureFile('languagesystems').prepare(self)
            kit.objects.FeatureFile(
                'GSUB',
                extensions = ['GSUB_lookups', 'GSUB_prefixing'],
            ).prepare(self)

            for style in self.styles_to_produce:

                kit.objects.FeatureFile('GPOS').prepare(self, style)

                kit.objects.FeatureFile('WeightClass').prepare(self, style)

                self.features_references = kit.objects.FeatureFile('features')
                self.features_references.filename_extension = None
                self.features_references.prepare(self, style)

        if self.options['run_stage_compile']:
            kit.makedirs(self.directories['build'])
            kit.objects.FmndbFile().prepare(self)
            self.goadb.output_trimmed(
                reference_font = self.styles_to_produce[0].open_font(is_temp=True),
                build_ttf = self.options['build_ttf'],
            )
            for style in self.styles_to_produce:
                self._compile(style)
                if self.options['build_ttf']:
                    self._compile(style, build_ttf=True)

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
