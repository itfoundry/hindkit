#!/usr/bin/env AFDKOPython

from __future__ import division, absolute_import, print_function, unicode_literals

import subprocess, os, argparse, collections
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

        self.vertical_metrics = vertical_metrics
        if self.vertical_metrics:
            self.vertical_metrics['TypoAscender'] = self.vertical_metrics['Ascender']
            self.vertical_metrics['TypoDescender'] = self.vertical_metrics['Descender']
            self.vertical_metrics['TypoLineGap'] = self.vertical_metrics['LineGap']
            self.vertical_metrics['winAscent'] = self.vertical_metrics['TypoAscender'] + int(round(self.vertical_metrics['LineGap'] / 2))
            self.vertical_metrics['winDescent'] = abs(self.vertical_metrics['TypoDescender']) + int(round(self.vertical_metrics['LineGap'] / 2))

        self.devanagari_offset_matrix = ((0, 0), (0, 0))

        self.options = {

            'prep_kerning':          self.family._has_kerning(),
            'prep_mark_positioning': self.family._has_mark_positioning(),
            'prep_mI_variants':      self.family._has_mI_variants(),

            'run_stage_prep_styles':   True,
            'run_stage_prep_features': True,
            'run_stage_compile':       True,

            'run_makeinstances': bool(self.family.masters),
            'run_checkoutlines': True,
            'run_autohint':      False,

            'override_GDEF': False,

            'do_style_linking': False,

            'use_os_2_version_4':         True,
            'prefer_typo_metrics':        True,
            'is_width_weight_slope_only': True,

        }

        self.options.update(options)

    def _prep_masters(self): # TODO
        OUTPUT = constants.paths.MASTERS
        if overriding_exists(OUTPUT):
            return
        else:
            raise SystemExit('[WARNING] Not able to prep masters yet.')

    def _prep_designspace(self):

        OUTPUT = constants.paths.DESIGNSPACE
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

            if self.options['prep_kerning']:
                doc.writeKerning()

            doc.endInstance()

        doc.save()

    def prep_styles(self): # STAGE I

        OUTPUT = constants.paths.STYLES
        if overriding_exists(OUTPUT):
            return

        if not bool(self.family.masters):
            return

        DEPENDENCIES = [i.path for i in self.family.masters]
        self._prep_masters()
        if not input_exists(DEPENDENCIES):
            raise SystemExit()

        for style in self.styles_to_be_built:
            make_dir(temp(style.directory))

        if self.options['run_makeinstances']:

            self._prep_designspace()

            arguments = ['-d', temp(constants.paths.DESIGNSPACE)]
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

    def prep_features(self):

        make_dir(temp(constants.paths.FEATURES))

        self._prep_features_classes()
        self._prep_features_tables()
        self._prep_features_languagesystems()
        self._prep_features_GSUB()
        self._prep_features_GPOS()

        for style in self.styles_to_be_built:

            directory = temp(style.directory)

            with open(os.path.join(directory, 'features'), 'w') as f:

                lines = ['table head { FontRevision 1.000; } head;']

                for file_name in ['classes', 'tables', 'languagesystems', 'lookups', 'GSUB']:
                    abstract_path = os.path.join(constants.paths.FEATURES, file_name + '.fea')
                    if os.path.exists(temp(abstract_path)):
                        lines.append('include (../../{});'.format(abstract_path))

                if os.path.exists(os.path.join(directory, WriteFeaturesKernFDK.kKernFeatureFileName)):
                    lines.append('feature kern { include ({}); } kern;'.format(WriteFeaturesKernFDK.kKernFeatureFileName))

                if os.path.exists(os.path.join(directory, WriteFeaturesMarkFDK.kMarkClassesFileName)):
                    lines.append('include ({});'.format(WriteFeaturesMarkFDK.kMarkClassesFileName))
                for feature_name, file_name in [
                    ('mark', WriteFeaturesMarkFDK.kMarkFeatureFileName),
                    ('mkmk', WriteFeaturesMarkFDK.kMkmkFeatureFileName),
                    ('abvm', WriteFeaturesMarkFDK.kAbvmFeatureFileName),
                    ('blwm', WriteFeaturesMarkFDK.kBlwmFeatureFileName),
                ]:
                    if os.path.exists(os.path.join(directory, file_name)):
                        lines.append('feature {0} { include ({1}); } {0};'.format(feature_name, file_name))

                f.writelines(i + '\n' for i in lines)

            with open(os.path.join(directory, 'WeightClass.fea'), 'w') as f:
                f.write('WeightClass {};\n'.format(str(style.weight_class)))

    def _prep_features_classes(self):

        OUTPUT = os.path.join(constants.paths.FEATURES, 'classes.fea')
        if overriding_exists(OUTPUT):
            return
        DEPENDENCIES = [i.path for i in self.styles_to_be_built]
        if not input_exists(DEPENDENCIES):
            raise SystemExit()

        lines = []

        if self.options['prep_mark_positioning']:

            glyph_classes = []
            glyph_classes.extend([(WriteFeaturesMarkFDK.kCombMarksClassName, glyph_filter_marks)])

            if self.options['prep_mI_variants']:
                glyph_classes.extend([
                    ('generated_MATRA_I_ALTS', hindkit.devanagari.glyph_filter_matra_i_alts),
                    ('generated_BASES_ALIVE', devanagari.glyph_filter_bases_alive),
                    ('generated_BASES_DEAD', devanagari.glyph_filter_bases_dead),
                    # ('generated_BASES_FOR_WIDE_MATRA_II', hindkit.devanagari.glyph_filter_bases_for_wide_matra_ii),
                ])

            style_0 = self.styles_to_be_built[0].open_font()

            glyph_order = [
                development_name for
                production_name, development_name, unicode_mapping in
                self.family.goadb
            ]
            for class_name, filter_function in glyph_classes:
                glyph_names = [glyph.name for glyph in filter(filter_function, style_0)]
                glyph_names = sort_glyphs(glyph_order, glyph_names)
                style_0.groups.update({class_name: glyph_names})
                lines.extend(
                    compose_glyph_class_def_lines(class_name, glyph_names)
                )
            style_0.save()

            for style in self.styles_to_be_built[1:]:
                font = style.open_font()
                font.groups.update(style_0.groups)
                font.save()

        if lines:
            with open(temp(OUTPUT), 'w') as f:
                f.writelines(i + '\n' for i in lines)

    def _prep_features_tables(self):

        OUTPUT = os.path.join(constants.paths.FEATURES, 'tables.fea')
        if overriding_exists(OUTPUT):
            return

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
                    # 'winAscent {winAscent}',
                    # 'winDescent {winDescent}',
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
            if self.options['prep_mark_positioning'] or os.path.exists(temp(os.path.join(constants.paths.FEATURES, 'classes.fea'))):
                GDEF_records['marks'] = '@{}'.format(WriteFeaturesMarkFDK.kCombMarksClassName)
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
            with open(temp(OUTPUT), 'w') as f:
                f.writelines(i + '\n' for i in lines)

    def _prep_features_languagesystems(self):

        OUTPUT = os.path.join(constants.paths.FEATURES, 'languagesystems.fea')
        if overriding_exists(OUTPUT):
            return

        lines = ['languagesystem DFLT dflt;']
        tag = constants.misc.SCRIPTS[self.family.script.lower()]['tag']
        if isinstance(tag, tuple):
            lines.append('languagesystem {} dflt;'.format(tag[1]))
            lines.append('languagesystem {} dflt;'.format(tag[0]))
        else:
            lines.append('languagesystem {} dflt;'.format(tag))

        if lines:
            with open(temp(OUTPUT), 'w') as f:
                f.writelines(i + '\n' for i in lines)

    def _prep_features_GSUB(self):

        OUTPUT = os.path.join(constants.paths.FEATURES, 'GSUB.fea')
        if overriding_exists(OUTPUT):
            return

        premade_feature_dir = hindkit._unwrap_path_relative_to_package_dir(
            os.path.join('resources/features', self.family.script.lower())
        )

        for file_name in ['GSUB.fea', 'lookups.fea']:
            file_path = os.path.join(premade_feature_dir, file_name)
            if os.path.exists(file_path):
                subprocess.call(['cp', '-fr', file_path, temp(os.path.join(constants.paths.FEATURES, file_name))])

    def _prep_features_GPOS(self):

        OUTPUT = os.path.join(constants.paths.FEATURES, 'GPOS.fea')
        if overriding_exists(OUTPUT):
            return
        DEPENDENCIES = [i.path for i in self.styles_to_be_built]
        if not input_exists(DEPENDENCIES):
            raise SystemExit()

        if self.options['prep_kerning']:

            for style in self.styles_to_be_built:
                WriteFeaturesKernFDK.KernDataClass(
                    font = style.open_font(is_temp=True),
                    folderPath = temp(style.directory),
                )

        if self.options['prep_mark_positioning']:
            for style in self.styles_to_be_built:
                WriteFeaturesMarkFDK.MarkDataClass(
                    font = style.open_font(is_temp=True),
                    folderPath = temp(style.directory),
                    trimCasingTags = False,
                    genMkmkFeature = self.options['prep_mark_to_mark_positioning'],
                    writeClassesFile = True,
                    indianScriptsFormat = (
                        True if self.family.script.lower() in constants.misc.SCRIPTS
                        else False
                    ),
                )
                if self.options['prep_mI_variants']:
                    hindkit.devanagari.prep_features_devanagari(self.family, style) # NOTE: not pure GPOS

    def _prep_fmndb(self):

        OUTPUT = constants.paths.FMNDB
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
            f.writelines(i + '\n' for i in lines)

    def _prep_goadb(self):

        OUTPUT = constants.paths.GOADB
        if overriding_exists(OUTPUT):
            return

        premade_feature_dir = hindkit._unwrap_path_relative_to_package_dir(
            os.path.join('resources/features', self.family.script.lower())
        )

        file_path = os.path.join(premade_feature_dir, OUTPUT)
        if os.path.exists(file_path):
            subprocess.call(['cp', '-fr', file_path, temp(OUTPUT)])

    def compile(self):

        self._prep_fmndb()
        self._prep_goadb()

        OUTPUT = constants.paths.BUILD
        remove_files(OUTPUT)
        make_dir(OUTPUT)
        DEPENDENCIES = [i.path for i in self.styles_to_be_built]
        if not input_exists(DEPENDENCIES):
            raise SystemExit()

        for style in self.styles_to_be_built:

            if style.file_name.endswith('.ufo'):
                font = style.open_font(is_temp=True)
                if font.info.postscriptFontName != style.output_full_name_postscript:
                    font.info.postscriptFontName = style.output_full_name_postscript
                    font.save()

            otf_path = os.path.join(constants.paths.BUILD, style.otf_name)

            arguments = [
                '-f', temp(style.path),
                '-o', otf_path,
                '-mf', temp(constants.paths.FMNDB),
                '-gf', temp(constants.paths.GOADB),
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
                    ('7', self.options['prefer_typo_metrics']),
                    ('8', self.options['is_width_weight_slope_only']),
                    ('9', style.is_oblique),
                ]:
                    arguments.append('-osbOn' if boolean else '-osbOff')
                    arguments.append(digit)

            subprocess.call(['makeotf'] + arguments)

            project_file_path = os.path.join(temp(style.directory), 'current.fpr')
            remove_files(project_file_path)

            if os.path.exists(otf_path) and os.path.exists(constants.paths.OUTPUT):
                subprocess.call(['cp', '-f', otf_path, constants.paths.OUTPUT])

    def _derive_options(self):

        parser = argparse.ArgumentParser(
            description = 'execute `AFDKOPython build.py` to run stages as specified in build.py, or append arguments to override.'
        )
        parser.add_argument(
            '-t', '--test', action = 'store_true',
            help = 'run a minimum and fast build process.',
        )
        parser.add_argument(
            '-s', '--stages', action = 'store',
            help = '"1" for "prep_styles", "2" for "prep_features", and "3" for "compile".',
        )
        parser.add_argument(
            '-o', '--options', action = 'store',
            help = '"0" for none, "1" for "makeinstances", "2" for "checkoutlines", and "3" for "autohint".',
        )
        args = parser.parse_args()

        if args.stages:
            stages = str(args.stages)
            self.options['run_stage_prep_styles'] = True if '1' in stages else False
            self.options['run_stage_prep_features'] = True if '2' in stages else False
            self.options['run_stage_compile'] = True if '3' in stages else False
        if args.options:
            options = str(args.options)
            self.options['run_makeinstances'] = True if '1' in options else False
            self.options['run_checkoutlines'] = True if '2' in options else False
            self.options['run_autohint'] = True if '3' in options else False
        if args.test:
            self.options['run_makeinstances'] = False
            self.options['run_checkoutlines'] = False
            self.options['run_autohint'] = False

        self.styles_to_be_built = self.family.styles
        if self.family.masters and (not self.options['run_makeinstances']):
            self.styles_to_be_built = self.family.get_styles_that_are_directly_derived_from_masters()

    def build(self):
        self._derive_options()
        remove_files(constants.paths.TEMP)
        make_dir(constants.paths.TEMP)
        if self.options['run_stage_prep_styles']:
            self.prep_styles()
        if self.options['run_stage_prep_features']:
            self.prep_features()
        if self.options['run_stage_compile']:
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

def make_dir(path):
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
        for line in message_lines:
            print(line)
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
