#!/usr/bin/env AFDKOPython

from __future__ import division, absolute_import, print_function, unicode_literals

import subprocess, os, argparse
import mutatorMath.ufo.document, WriteFeaturesKernFDK, WriteFeaturesMarkFDK
import hindkit, hindkit.devanagari, hindkit.patches
import hindkit.constants as constants

class Builder(object):

    def __init__(
        self,
        family,
        fontrevision = '1.000',
        vertical_metrics = {}
        options = [],
    ):

        self.family = family
        self.fontrevision = fontrevision

        self.abstract_paths = {
            'masters': constants.paths.MASTERS,
            'designspace': constants.paths.DESIGNSPACE,
            'styles': constants.paths.STYLES,
            'fmndb': constants.paths.FMNDB,
            'goadb': self.family.goadb_path,
            'build': constants.paths.BUILD,
        }

        self.vertical_metrics = vertical_metrics
        if self.vertical_metrics:
            self.vertical_metrics['TypoAscender'] = self.vertical_metrics['Ascender']
            self.vertical_metrics['TypoDescender'] = self.vertical_metrics['Descender']
            self.vertical_metrics['TypoLineGap'] = self.vertical_metrics['LineGap']
            self.vertical_metrics['winAscent'] = self.vertical_metrics['TypoAscender'] + self.vertical_metrics['LineGap'] / 2
            self.vertical_metrics['winDescent'] = abs(self.vertical_metrics['TypoDescender']) + self.vertical_metrics['LineGap'] / 2


        self.devanagari_offset_matrix = ((0, 0), (0, 0))

        self.options = {
            'stage_prepare_styles': True,
            'stage_prepare_features': True,
            'stage_compile': True,
        }
        for predefined_option in [
            'run_makeinstances',
            'run_checkoutlines',
            'run_autohint',
            'do_style_linking',
            'use_os_2_version_4',
            'prefer_typo_metrics',
            'is_width_weight_slope_only',
            'override_GDEF',
        ]:
            if predefined_option in options:
                self.options[predefined_option] = True
            else:
                self.options[predefined_option] = False

        parser = argparse.ArgumentParser(
            description = 'execute `AFDKOPython build.py` to run stages as specified in build.py, or append arguments to override.'
        )
        parser.add_argument(
            '-t', '--test', action = 'store_true',
            help = 'run a minimum and fast build process.',
        )
        parser.add_argument(
            '-s', '--stages', action = 'store',
            help = '"1" for "prepare_styles", "2" for "prepare_features", and "3" for "compile".',
        )
        parser.add_argument(
            '-o', '--options', action = 'store',
            help = '"0" for none, "1" for "makeinstances", "2" for "checkoutlines", and "3" for "autohint".',
        )
        args = parser.parse_args()

        if args.stages:
            stages = str(args.stages)
            self.options['stage_prepare_styles'] = True if '1' in stages else False
            self.options['stage_prepare_features'] = True if '2' in stages else False
            self.options['stage_compile'] = True if '3' in stages else False
        if args.options:
            options = str(args.options)
            self.options['run_makeinstances'] = True if '1' in options else False
            self.options['run_checkoutlines'] = True if '2' in options else False
            self.options['run_autohint'] = True if '3' in options else False
        if args.test:
            self.options['run_makeinstances'] = False

        if self.options['run_makeinstances']:
            self.styles_to_be_built = self.family.styles()
        else:
            self.styles_to_be_built = self.family.get_styles_that_are_directly_derived_from_masters()

        if not ('kerning' or 'mark_positioning') in self.family.modules:
            self.options['stage_prepare_features'] = False

    def _prepare_masters(self): # TODO
        OUTPUT = self.abstract_paths('masters')
        if overriding_exists(OUTPUT):
            return
        else:
            raise SystemExit('[WARNING] Not able to prepare masters yet.')

    def _prepare_designspace(self):

        OUTPUT = self.abstract_paths('designspace')
        if overriding_exists(OUTPUT):
            return

        doc = mutatorMath.ufo.document.DesignSpaceDocumentWriter(
            hindkit._unwrap_path_relative_to_cwd(temp(OUTPUT))
        )

        for i, master in enumerate(self.family.masters):

            doc.addSource(

                path = hindkit._unwrap_path_relative_to_cwd(master.path),
                name = 'master-' + master.name,
                location = {'weight': master.interpolation_value},

                copyLib    = True if i == 0 else False,
                copyGroups = True if i == 0 else False,
                copyInfo   = True if i == 0 else False,

                # muteInfo = False,
                # muteKerning = False,
                # mutedGlyphNames = None,

            )

        for style in self.styles_to_be_built:

            doc.startInstance(
                name = 'instance-' + style.name,
                location = {'weight': style.interpolation_value},
                familyName = self.family.output_name,
                styleName = style.name,
                fileName = hindkit._unwrap_path_relative_to_cwd(
                    temp(style.path)
                ),
                postScriptFontName = style.output_full_name_postscript,
                # styleMapFamilyName = None,
                # styleMapStyleName = None,
            )

            doc.writeInfo()

            if 'kerning' in self.family.modules:
                doc.writeKerning()

            doc.endInstance()

        doc.save()

    def prepare_styles(self): # STAGE I

        DEPENDENCIES = [i.path for i in self.family.masters]
        OUTPUT = self.abstract_paths('styles')
        if overriding_exists(OUTPUT):
            return
        self._prepare_masters()
        if not input_exists(DEPENDENCIES):
            raise SystemExit()

        reset_dir(temp(OUTPUT))
        for style in self.styles_to_be_built:
            subprocess.call(['mkdir', temp(style.directory)])

        if self.options['run_makeinstances']:

            self._prepare_designspace()

            arguments = ['-d', temp(self.abstract_paths('designspace'))]
            if not self.options['run_checkoutlines']:
                arguments.append('-c')
            if not self.options['run_autohint']:
                arguments.append('-a')

            subprocess.call(['makeInstancesUFO'] + arguments)

        else:
            for index, (master, style) in enumerate(zip(self.family.masters, self.styles_to_be_built)):
                subprocess.call(['cp', '-fr', master.path, temp(style.path)])
                font = style.open_font(is_temp=True)
                font.info.postscriptFontName = style.output_full_name_postscript
                font.save()
            self._simulate_makeInstancesUFO_postprocess(self.styles_to_be_built)

    def _simulate_makeInstancesUFO_postprocess(self, styles):

        DEPENDENCIES = [i.path for i in self.styles_to_be_built]
        if not input_exists(DEPENDENCIES):
            return

        newInstancesList = [temp(i.path) for i in styles]
        if self.options['run_checkoutlines'] or self.options['run_autohint']:
            options = {
                'doOverlapRemoval': self.run_checkoutlines,
                'doAutoHint': self.run_autohint,
                'allowDecimalCoords': False,
            }
            for instancePath in newInstancesList:
                hindkit.patches.updateInstance(options, instancePath)

    def prepare_features(self):
        self._prepare_features_general()
        self._prepare_features_style_dependent()

    def _prepare_features_general(self):

        lines = []

        # START

        tables = collections.OrderedDict(
            'hhea': [],
            'OS/2': [],
            'GDEF': [],
            'name': [],
        )

        GDEF_records = {
            'bases': '',
            'ligatures': '',
            'marks': '',
            'components': '',
        }

        if 'mark_positioning' in self.family.modules:
            lines.append('include (../../../{});'.format(constants.paths.CLASSES))
            GDEF_records['marks'] = '@{}'.format(constants.misc.MARKS_CLASS_NAME)

        tables['OS/2'].extend(
            'include (weightclass.fea);',
            'Vendor "{}";'.format(Vendor),
        )

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
                    'winAscent {winAscent}',
                    'winDescent {winDescent}',
                ]
            ]

        # tables['OS/2'].extend(self.generate_UnicodeRange)
        # tables['OS/2'].extend(self.generate_CodePageRange)

        if 'override_GDEF' in self.options:
            tables['GDEF'].extend(
                'GlyphClassDef {bases}, {ligatures}, {marks}, {components};'.format(**GDEF_records)
            )

                # self.family
                # self.family.client
                # self.family.trademark
                # self.family.script

        tables['name'].extend(
            [
                'nameid  0 "Copyright {} Indian Type Foundry. All rights reserved.";'.format(time.year),
                'nameid  7 "{} is a trademark of the Indian Type Foundry.";'.format(self.family.trademark),
                'nameid  8 "Indian Type Foundry";',
                'nameid  9 "{}";'.format(self.family.designers),
                'nameid 10 "{}";'.format(self.family.description),
                'nameid 11 "http://www.indiantypefoundry.com";',
                'nameid 12 "";',
                'nameid 13 "This Font Software is protected under domestic and international trademark and copyright law. You agree to identify the ITF fonts by name and credit the ITF\'s ownership of the trademarks and copyrights in any design or production credits.";',
                'nameid 14 "http://www.indiantypefoundry.com/licensing/eula/";',
                'nameid 19 "{}";'.format(constants.misc.SAMPLE_TEXT[self.family.script]),
            ]
        )

        for name, entries in tables.items():
            if entries:
                lines.append('table {} {'.format(name))
                lines.extend('  ' + i for i in entries)
                lines.append('} {};'.format(name))

        # END

        # GPOS

        for style in self.styles_to_be_built:
            directory = temp(style.directory)
            with open(os.path.join(directory, 'features'), 'w') as f:
                lines = [
                    'table head { FontRevision 1.000; } head;',
                    'include (../../../features/generated_features_start.fea);',
                    'include (../../../features/features.fea);',
                    'include (../../../features/generated_features_end.fea);',
                ]
                f.write('\n'.join(lines) + '\n')
            with open(os.path.join(directory, 'WeightClass.fea'), 'w') as f:
                f.write(constants.templates.WEIGHTCLASS.format(str(style.weight_class)))

    def _prepare_features_style_dependent(self):

        DEPENDENCIES = [i.path for i in self.styles_to_be_built]
        if not input_exists(DEPENDENCIES):
            raise SystemExit()

        if 'kerning' in self.family.modules:
            self._prepare_features_kerning()
        if 'mark_positioning' in self.family.modules:
            self._prepare_features_mark_positioning()

    def _prepare_features_kerning(self):
        for style in self.styles_to_be_built:
            WriteFeaturesKernFDK.KernDataClass(
                font = style.open_font(is_temp=True),
                folderPath = temp(style.directory),
                minKern = 3,
                writeTrimmed = False,
                writeSubtables = True,
                fileName = 'kern.fea',
            )

    def _prepare_features_mark_positioning(self):

        glyph_classes = []
        glyph_classes.extend([(constants.misc.MARKS_CLASS_NAME, glyph_filter_marks)])

        if 'devanagari_matra_i_variants' in self.family.modules:
            glyph_classes.extend([
                ('generated_MATRA_I_ALTS', hindkit.devanagari.glyph_filter_matra_i_alts),
                ('generated_BASES_ALIVE', devanagari.glyph_filter_bases_alive),
                ('generated_BASES_DEAD', devanagari.glyph_filter_bases_dead),
                # ('generated_BASES_FOR_WIDE_MATRA_II', hindkit.devanagari.glyph_filter_bases_for_wide_matra_ii),
            ])

        style_0 = self.styles_to_be_built[0].open_font()
        self._generate_glyph_classes(style_0, glyph_classes)

        for style in self.styles_to_be_built[1:]:
            font = style.open_font()
            font.groups.update(style_0.groups)
            font.save()

        for style in self.styles_to_be_built:

            WriteFeaturesMarkFDK.kCombMarksClassName = constants.misc.MARKS_CLASS_NAME
            WriteFeaturesMarkFDK.MarkDataClass(
                font = style.open_font(is_temp=True),
                folderPath = temp(style.directory),
                trimCasingTags = False,
                genMkmkFeature = 'mark_to_mark_positioning' in self.family.modules,
                writeClassesFile = True,
                indianScriptsFormat = (
                    True if self.family.script.lower() in constants.misc.INDIC_SCRIPTS
                    else False
                ),
            )

            if 'devanagari_matra_i_variants' in self.family.modules:
                hindkit.devanagari.prepare_features_devanagari(self.family, style)

    def _generate_glyph_classes(self, font, glyph_classes):
        output_path = constants.paths.CLASSES
        glyph_order = [
            development_name for
            production_name, development_name, unicode_mapping in
            self.family.goadb
        ]
        output_lines = []
        for class_name, filter_function in glyph_classes:
            glyph_names = [glyph.name for glyph in filter(filter_function, font)]
            glyph_names = sort_glyphs(glyph_order, glyph_names)
            font.groups.update({class_name: glyph_names})
            output_lines.extend(
                compose_glyph_class_def_lines(class_name, glyph_names)
            )
        font.save()
        with open(output_path, 'w') as file:
            file.write('\n'.join(output_lines))

    def prepare_fmndb(self):

        OUTPUT = self.abstract_paths('fmndb')
        if overriding_exists(OUTPUT):
            return

        f_name = self.family.output_name
        lines = []

        for style in self.styles_to_be_built:

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

        with open(temp(OUTPUT), 'w') as f:
            f.write(constants.templates.FMNDB_HEAD)
            f.write('\n'.join(lines))
            f.write('\n')

    def prepare_goadb(self): # TODO
        OUTPUT = self.abstract_paths('goadb')
        if overriding_exists(OUTPUT):
            return
        else:
            raise SystemExit('[WARNING] Not able to prepare GOADB yet.')

    def compile(self):

        DEPENDENCIES = [i.path for i in self.styles_to_be_built]
        if not input_exists(DEPENDENCIES):
            raise SystemExit()

        OUTPUT = self.abstract_paths('build')
        reset_dir(OUTPUT)

        for style in self.styles_to_be_built:

            if style.file_name.endswith('.ufo'):
                font = style.open_font(is_temp=True)
                if font.info.postscriptFontName != style.output_full_name_postscript:
                    font.info.postscriptFontName = style.output_full_name_postscript
                    font.save()

            otf_path = os.path.join(self.build_path, style.otf_name)

            arguments = [
                '-f', temp(style.path),
                '-o', otf_path,
                '-mf', temp(self.abstract_paths('fmndb')),
                '-gf', temp(self.abstract_paths('goadb')),
                '-r',
                '-shw',
                '-rev', self.fontrevision,
                '-omitMacNames',
            ]
            if self.options['do_style_linking']:
                if style.is_bold:
                    arguments.append('-b')
                if style.is_italic:
                    arguments.append('-i')
            if self.options['use_os_2_version_4']:
                for digit, boolean in [
                    ('7', self.prefer_typo_metrics),
                    ('8', self.is_width_weight_slope_only),
                    ('9', style.is_oblique),
                ]:
                    arguments.append('-osbOn' if boolean else '-osbOff')
                    arguments.append(digit)

            subprocess.call(['makeotf'] + arguments)

            project_file_path = os.path.join(temp(style.directory), 'current.fpr')
            remove_files(project_file_path)

            if os.path.exists(otf_path) and os.path.exists(constants.paths.OUTPUT):
                subprocess.call(['cp', '-f', otf_path, constants.paths.OUTPUT])

    def build(self):
        if 'stage_prepare_styles' in self.options:
            self.prepare_styles()
        if 'stage_prepare_features' in self.options:
            self.prepare_features()
        if 'stage_compile' in self.options:
            self.prepare_fmndb()
            self.prepare_goadb()
            self.compile()

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

def glyph_filter_marks(glyph):
    has_mark_anchor = False
    for anchor in glyph.anchors:
        if anchor.name.startswith('_'):
            has_mark_anchor = True
            break
    return has_mark_anchor

# ---

def remove_files(path):
    subprocess.call(['rm', '-fr', path])

def reset_dir(path):
    remove_files(path)
    subprocess.call(['mkdir', path])

# ---

def overriding(abstract_path):
    return os.path.join(constants.paths.OVERRIDING, abstract_path)

def temp(abstract_path):
    return os.path.join(constants.paths.TEMP, abstract_path)

def overriding_exists(overriding_path):
    overriding_path = overriding(overriding_path)
    if os.path.exists(overriding_path):
        subprocess.call(['cp', '-fr', overriding_path, temp(overriding_path)])
        exists = True
    else:
        exists = False
    return exists

def input_exists(paths):
    exists = True
    message_lines = ['[WARNING] Files missing:']
    for path in paths:
        if not os.path.exists(path):
            exists = False
            message_lines.append('\t' + path)
    if not exists:
        message_lines.extend(['', '[Note] Exit.', ''])
        print('\n'.join(message_lines))
    return exists

# ---

import defcon
defcon.Glyph.insertAnchor = hindkit.patches.insertAnchor

def import_glyphs(
    self,
    from_masters,
    to_masters,
    save_to_masters,
    excluding_names=[],
    deriving_names=[],
):

    for from_path, to_path, save_to_path in zip(from_masters, to_masters, save_to_masters):

        from_master = defcon.Font(from_path)
        to_master = defcon.Font(to_path)

        new_names = set(from_master.keys())
        existing_names = set(to_master.keys())
        new_names.difference_update(existing_names)
        new_names.difference_update(set(excluding_names))
        new_names = sort_glyphs(from_master.glyphOrder, new_names)

        for new_name in new_names:
            to_master.newGlyph(new_name)
            to_master[new_name].copyDataFromGlyph(from_master[new_name])
        else:
            pass

        for new_name in deriving_names:
            source_name = constants.misc.DERIVING_MAP[new_name]
            to_master.newGlyph(new_name)
            if source_name:
                to_master[new_name].width = to_master[source_name].width

        remove_files(save_to_path)
        to_master.save(save_to_path)
