#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import subprocess, os, argparse, collections, shutil
from fontTools.ttLib import TTFont
import mutatorMath.ufo.document, WriteFeaturesKernFDK, WriteFeaturesMarkFDK
import hindkit, hindkit.devanagari, hindkit.patches
import hindkit.constants as constants

class Builder(object):

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

            'prepare_kerning': self.family._has_kerning(),

            'prepare_mark_positioning': self.family._has_mark_positioning(),
            'prepare_mark_to_mark_positioning': True,
            'match_mI_variants': self.family._has_mI_variants(),
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

        self.goadb = hindkit.GlyphData()

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

    def prepare_masters(self):

        for master in self.family.masters:
            master.prepare()

        self.goadb.generate(self.family.masters[0].open())

        for master in self.family.masters:
            font = master.open()
            font.lib['public.glyphOrder'] = self.goadb.development_names
            font.lib.pop('com.schriftgestaltung.glyphOrder', None)
            master.save_as(font)

    def generate_designspace(self, output):

        doc = mutatorMath.ufo.document.DesignSpaceDocumentWriter(
            os.path.abspath(hindkit.relative_to_cwd(output))
        )

        for i, master in enumerate(self.family.masters):

            doc.addSource(

                path = os.path.abspath(hindkit.relative_to_cwd(master.path)),
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
                    hindkit.relative_to_cwd(style.path)
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
            make_dir(style.directory)

        if self.options['run_makeinstances']:

            self.designspace.prepare()

            arguments = ['-d', temp(constants.paths.DESIGNSPACE)]
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
            hindkit.patches.updateInstance(options, style.path)

    def generate_features_classes(self, output):

        self._check_inputs([temp(i.path) for i in self.styles_to_produce])

        lines = []

        if self.options['prepare_mark_positioning']:

            glyph_classes = []
            glyph_classes.extend([(WriteFeaturesMarkFDK.kCombMarksClassName, glyph_filter_marks)])

            if self.options['match_mI_variants']:
                glyph_classes.extend([
                    ('MATRA_I_ALTS', hindkit.devanagari.glyph_filter_matra_i_alts),
                    ('BASES_ALIVE', hindkit.devanagari.glyph_filter_bases_alive),
                    ('BASES_DEAD', hindkit.devanagari.glyph_filter_bases_dead),
                    # ('BASES_FOR_WIDE_MATRA_II', hindkit.devanagari.glyph_filter_bases_for_wide_matra_ii),
                ])

            style_0 = self.styles_to_produce[0].open_font(is_temp=True)

            glyph_order = self.goadb.development_names
            for class_name, filter_function in glyph_classes:
                glyph_names = [
                    glyph.name for glyph in filter(
                        lambda glyph: filter_function(self.family, glyph),
                        style_0,
                    )
                ]
                glyph_names = sort_glyphs(glyph_order, glyph_names)
                style_0.groups.update({class_name: glyph_names})
                lines.extend(
                    compose_glyph_class_def_lines(class_name, glyph_names)
                )
            style_0.save()

            for style in self.styles_to_produce[1:]:
                font = style.open_font(is_temp=True)
                font.groups.update(style_0.groups)
                font.save()

        if lines:
            with open(output, 'w') as f:
                f.writelines(i + '\n' for i in lines)

    def generate_features_tables(self, output):

        lines = []
        tables = collections.OrderedDict([
            ('hhea', []),
            ('OS/2', []),
            ('GDEF', []),
            ('name', []),
        ])

        tables['OS/2'].extend([
            'include (weightclass.fea);',
            'Vendor "{}";'.format(constants.clients.Client(self.family).table_OS_2['Vendor']),
        ])

        if self.vertical_metrics:
            tables['hhea'].extend(
                i.format(**self.vertical_metrics)
                for i in [
                    'Ascender {Ascender};',
                    'Descender {Descender};',
                    'LineGap {LineGap};',
                ]
            )
            tables['OS/2'].extend(
                i.format(**self.vertical_metrics)
                for i in [
                    'TypoAscender {TypoAscender};',
                    'TypoDescender {TypoDescender};',
                    'TypoLineGap {TypoLineGap};',
                    'winAscent {winAscent};',
                    'winDescent {winDescent};',
                ]
            )

        # tables['OS/2'].extend(self.generate_UnicodeRange)
        # tables['OS/2'].extend(self.generate_CodePageRange)

        if self.options['override_GDEF']:
            GDEF_records = {
                'bases': '',
                'ligatures': '',
                'marks': '',
                'components': '',
            }
            if self.options['prepare_mark_positioning'] or os.path.exists(temp(os.path.join(constants.paths.FEATURES, 'classes.fea'))):
                GDEF_records['marks'] = '@{}'.format(WriteFeaturesMarkFDK.kCombMarksClassName)
            if os.path.exists(temp(os.path.join(constants.paths.FEATURES, 'classes_suffixing.fea'))):
                GDEF_records['marks'] = '@{}'.format('COMBINING_MARKS_GDEF')
            tables['GDEF'].extend([
                'GlyphClassDef {bases}, {ligatures}, {marks}, {components};'.format(**GDEF_records)
            ])

        tables['name'].extend(
            'nameid {} "{}";'.format(
                name_id,
                content.encode('unicode_escape').replace('\\x', '\\00').replace('\\u', '\\')
            )
            for name_id, content in constants.clients.Client(self.family).table_name.items()
            if content
        )

        for name, entries in tables.items():
            if entries:
                lines.append('table {} {{'.format(name))
                lines.extend('  ' + i for i in entries)
                lines.append('}} {};'.format(name))

        if lines:
            with open(output, 'w') as f:
                f.writelines(i + '\n' for i in lines)

    def generate_features_languagesystems(self, output):

        lines = ['languagesystem DFLT dflt;']
        tag = constants.misc.SCRIPTS[self.family.script.lower()]['tag']
        if isinstance(tag, tuple):
            lines.append('languagesystem {} dflt;'.format(tag[1]))
            lines.append('languagesystem {} dflt;'.format(tag[0]))
        else:
            lines.append('languagesystem {} dflt;'.format(tag))

        if lines:
            with open(output, 'w') as f:
                f.writelines(i + '\n' for i in lines)

    def generate_features_GSUB(self, output):
        pass

    def generate_features_GPOS(self, output, style):
        self._check_inputs([temp(style.path)])
        directory = temp(style.directory)
        if self.options['prepare_kerning']:
            WriteFeaturesKernFDK.KernDataClass(
                font = style.open_font(is_temp=True),
                folderPath = directory,
            )
            kern_path = os.path.join(directory, WriteFeaturesKernFDK.kKernFeatureFileName)
            if self.options['postprocess_kerning'] and os.path.exists(kern_path):
                with open(kern_path) as f:
                    original = f.read()
                postprocessed = self.postprocess_kerning(original)
                with open(kern_path, 'w') as f:
                    f.write(postprocessed)
        if self.options['prepare_mark_positioning']:
            WriteFeaturesMarkFDK.MarkDataClass(
                font = style.open_font(is_temp=True),
                folderPath = directory,
                trimCasingTags = False,
                genMkmkFeature = self.options['prepare_mark_to_mark_positioning'],
                writeClassesFile = True,
                indianScriptsFormat = self.family.script.lower() in constants.misc.SCRIPTS,
            )
            if self.options['match_mI_variants']:
                hindkit.devanagari.prepare_features_devanagari(
                    self.options['position_marks_for_mI_variants'],
                    self,
                    style,
                ) # NOTE: not pure GPOS

    def generate_features_weight_class(self, style):
        directory = temp(style.directory)
        with open(os.path.join(directory, 'WeightClass.fea'), 'w') as f:
            f.write('WeightClass {};\n'.format(str(style.weight_class)))

    def generate_features_references(self, style):
        directory = temp(style.directory)
        with open(os.path.join(directory, 'features'), 'w') as f:
            lines = ['table head { FontRevision 1.000; } head;']
            for file_name in [
                'classes',
                'classes_suffixing',
                'tables',
                'languagesystems',
                'GSUB_prefixing',
                'GSUB_lookups',
                'GSUB',
            ]:
                abstract_path = os.path.join(constants.paths.FEATURES, file_name + '.fea')
                if os.path.exists(temp(abstract_path)):
                    lines.append('include (../../{});'.format(abstract_path))
            if os.path.exists(os.path.join(directory, WriteFeaturesKernFDK.kKernFeatureFileName)):
                if self.family.script.lower() in constants.misc.SCRIPTS:
                    kerning_feature_name = 'dist'
                else:
                    kerning_feature_name = 'kern'
                lines.append(
                    'feature {0} {{ include ({1}); }} {0};'.format(
                        kerning_feature_name,
                        WriteFeaturesKernFDK.kKernFeatureFileName,
                    )
                )
            if os.path.exists(os.path.join(directory, WriteFeaturesMarkFDK.kMarkClassesFileName)):
                lines.append('include ({});'.format(WriteFeaturesMarkFDK.kMarkClassesFileName))
            for feature_name, file_name in [
                ('mark', WriteFeaturesMarkFDK.kMarkFeatureFileName),
                ('mkmk', WriteFeaturesMarkFDK.kMkmkFeatureFileName),
                ('abvm', WriteFeaturesMarkFDK.kAbvmFeatureFileName),
                ('blwm', WriteFeaturesMarkFDK.kBlwmFeatureFileName),
            ]:
                if os.path.exists(os.path.join(directory, file_name)):
                    lines.append('feature {0} {{ include ({1}); }} {0};'.format(feature_name, file_name))
            f.writelines(i + '\n' for i in lines)

    def generate_fmndb(self, output):

        f_name = self.family.output_name
        lines = []

        for style in self.styles_to_produce:

            lines.append('')
            lines.append('[{}]'.format(style.output_full_name_postscript))
            lines.append('  f = {}'.format(f_name))
            lines.append('  s = {}'.format(style.name))

            l_name = style.output_full_name
            comment_lines = []

            if self.options['do_style_linking']:
                if style.name == 'Regular':
                    l_name = l_name.replace(' Regular', '')
                else:
                    if style.is_bold:
                        comment_lines.append('  # IsBoldStyle')
                        l_name = l_name.replace(' Bold', '')
                    if style.is_italic:
                        comment_lines.append('  # IsItalicStyle')
                        l_name = l_name.replace(' Italic', '')

            if l_name != f_name:
                lines.append('  l = {}'.format(l_name))

            lines.extend(comment_lines)

        with open(output, 'w') as f:
            f.write(constants.templates.FMNDB_HEAD)
            f.writelines(i + '\n' for i in lines)

    def _compile(self, style, build_ttf=False):

        if build_ttf:
            style.input_format = 'TTF'
            style.output_format = 'TTF'

        self._check_inputs([temp(style.path), temp(self.fmndb.output), temp(self.trimmed_goadb.output)])

        # if style.file_name.endswith('.ufo'):
        #     font = style.open_font(is_temp=True)
        #     if font.info.postscriptFontName != style.output_full_name_postscript:
        #         font.info.postscriptFontName = style.output_full_name_postscript
        #         font.save()

        font_path = style.font_path

        arguments = [
            '-f', temp(style.path),
            '-o', font_path,
            '-mf', temp(self.fmndb.output),
            '-gf', temp(self.trimmed_goadb.output),
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

        if not os.path.isdir(constants.paths.BUILD):
            os.makedirs(constants.paths.BUILD)

        subprocess.call(['makeotf'] + arguments)

        if self.options['postprocess_font_file'] and os.path.exists(font_path):
            original = TTFont(font_path)
            postprocessed = self.postprocess_font_file(original)
            postprocessed.save(font_path, reorderTables=False)
            print('[NOTE] `postprocess_font_file` done.')

        destination = constants.paths.ADOBE_FONTS
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

        self._finalize_options()
        make_dir(constants.paths.TEMP)

        if self.options['run_stage_prepare_masters']:
            reset_dir(temp(constants.paths.MASTERS))
            self.prepare_masters()

        if self.options['run_stage_prepare_styles']:
            reset_dir(temp(constants.paths.STYLES))
            self.prepare_styles()

        if self.options['run_stage_prepare_features']:
            reset_dir(temp(constants.paths.FEATURES))
            self.prepare(
                os.path.join(constants.paths.FEATURES, 'classes.fea'), #!
                self.generate_features_classes,
                extensions = [
                    os.path.join(constants.paths.FEATURES, 'classes_{}.fea'.format(i))
                    for i in ['suffixing']
                ],
            )
            self.prepare(
                os.path.join(constants.paths.FEATURES, 'tables.fea'),
                self.generate_features_tables,
                None,
            )
            self.prepare(
                os.path.join(constants.paths.FEATURES, 'languagesystems.fea'),
                self.generate_features_languagesystems,
                None,
            )
            self.prepare(
                os.path.join(constants.paths.FEATURES, 'GSUB.fea'), #!
                None,
                extensions = [
                    os.path.join(constants.paths.FEATURES, 'GSUB_{}.fea'.format(i))
                    for i in ['lookups', 'prefixing']
                ],
            )
            for style in self.styles_to_produce:
                self.prepare(
                    os.path.join(constants.paths.FEATURES, 'GPOS.fea'),
                    self.generate_features_GPOS,
                    None,
                    style,
                )
                self.generate_features_weight_class(style)
                self.generate_features_references(style)

        if self.options['run_stage_compile']:
            self.prepare(
                constants.paths.FMNDB,
                self.generate_fmndb,
                None,
            )
            self.goadb.output_trimmed(
                reference_font = self.styles_to_produce[0].open_font(is_temp=True),
                build_ttf = self.options['build_ttf'],
            )
            for style in self.styles_to_produce:
                self._compile(style)
                if self.options['build_ttf']:
                    self._compile(style, build_ttf=True)

# ---

def sort_glyphs(glyph_order, glyph_names):
    sorted_glyphs = (
        [i for i in glyph_order if i in glyph_names] +
        [i for i in glyph_names if i not in glyph_order]
    )
    return sorted_glyphs

def compose_glyph_class_def_lines(class_name, glyph_names):
    if glyph_names:
        glyph_class_def_lines = (
            ['@{} = ['.format(class_name)] +
            ['  {}'.format(glyph_name) for glyph_name in glyph_names] +
            ['];', '']
        )
    else:
        glyph_class_def_lines = ['# @{} = [];'.format(class_name), '']
    return glyph_class_def_lines

def glyph_filter_marks(family, glyph):
    has_mark_anchor = False
    for anchor in glyph.anchors:
        if anchor.name:
            if anchor.name.startswith('_'):
                has_mark_anchor = True
                break
    return has_mark_anchor

# ---

def remove_files(path):
    subprocess.call(['rm', '-fR', path])

def make_dir(path):
    subprocess.call(['mkdir', '-p', path])

def reset_dir(path):
    remove_files(path)
    make_dir(path)

def copy(src, dst):
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy(src, src)

# ---

def overriding(abstract_path):
    return abstract_path

def temp(abstract_path):
    if abstract_path:
        temp_path = os.path.join(constants.paths.TEMP, abstract_path)
    else:
        temp_path = None
    return temp_path
