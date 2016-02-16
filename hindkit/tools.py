#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import subprocess, os, argparse, collections
import mutatorMath.ufo.document, WriteFeaturesKernFDK, WriteFeaturesMarkFDK
import hindkit, hindkit.devanagari, hindkit.patches
import hindkit.constants as constants

class Resource(object):

    def __init__(
        self,
        builder,
        output,
        generator,
        extensions = None,
    ):
        self.builder = builder
        self.output = output
        self.generator = generator

        self.extensions = []
        if extensions:
            self.extensions.extend(extensions)

    def _temp(self, output):
        temp = None
        if output:
            temp = os.path.join(constants.paths.TEMP, output)
        return temp

    def _premade(self, output):
        premade = None
        if output:
            premade_prefix = hindkit._unwrap_path_relative_to_package_dir(
                os.path.join(
                    'data/premade',
                    self.builder.family.script.lower(),
                )
            )
            premade = os.path.join(premade_prefix, output)
        return premade

    def prepare(self, *args, **kwargs):
        if self.output and os.path.exists(self.output):
            for output in [self.output] + self.extensions:
                subprocess.call(['cp', '-fr', output, self._temp(output)])
        elif self.output and self.generator:
            self.generator(self._temp(self.output), *args, **kwargs)
            for output in [self.output] + self.extensions:
                subprocess.call(['cp', '-fr', output, self._temp(output)])
        elif self.output and os.path.exists(self._premade(self.output)):
            for output in [self.output] + self.extensions:
                subprocess.call(['cp', '-fr', self._premade(output), self._temp(output)])
        else:
            raise SystemExit("Can't prepare {}.".format(self._temp(self.output)))

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
        # if self.vertical_metrics:
        #     self.vertical_metrics['TypoAscender'] = self.vertical_metrics['Ascender']
        #     self.vertical_metrics['TypoDescender'] = self.vertical_metrics['Descender']
        #     self.vertical_metrics['TypoLineGap'] = self.vertical_metrics['LineGap']
        #     self.vertical_metrics['winAscent'] = self.vertical_metrics['TypoAscender'] + int(round(self.vertical_metrics['LineGap'] / 2))
        #     self.vertical_metrics['winDescent'] = abs(self.vertical_metrics['TypoDescender']) + int(round(self.vertical_metrics['LineGap'] / 2))

        self.devanagari_offset_matrix = ((0, 0), (0, 0))

        self.options = {

            'prepare_kerning': self.family._has_kerning(),
            'postprocess_kerning': False,
            'prepare_mark_positioning': self.family._has_mark_positioning(),
            'prepare_mark_to_mark_positioning': self.family._has_mark_positioning(),
            'prepare_mI_variants': self.family._has_mI_variants(),

            'run_stage_prepare_styles': True,
            'run_stage_prepare_features': True,
            'run_stage_compile': True,

            'run_makeinstances': bool(self.family.masters),
            'run_checkoutlines': True,
            'run_autohint': False,

            'override_GDEF': False,

            'do_style_linking': False,

            'use_os_2_version_4': True,
            'prefer_typo_metrics': True,
            'is_width_weight_slope_only': True,

        }

        self.options.update(options)

        self.designspace = Resource(
            self,
            constants.paths.DESIGNSPACE,
            self._generate_designspace,
        )
        self.styles = Resource(
            self,
            constants.paths.STYLES,
            self.prepare_styles,
        )
        self.features_classes = Resource(
            self,
            os.path.join(constants.paths.FEATURES, 'classes.fea'), #!
            self._generate_features_classes,
            extensions = [
                os.path.join(constants.paths.FEATURES, 'classes_{}.fea'.format(i))
                for i in ['suffixing']
            ],
        )
        self.features_tables = Resource(
            self,
            os.path.join(constants.paths.FEATURES, 'tables.fea'),
            self._generate_features_tables,
        )
        self.features_languagesystems = Resource(
            self,
            os.path.join(constants.paths.FEATURES, 'languagesystems.fea'),
            self._generate_features_languagesystems,
        )
        self.features_GSUB = Resource(
            self,
            os.path.join(constants.paths.FEATURES, 'GSUB.fea'), #!
            None,
            extensions = [
                os.path.join(constants.paths.FEATURES, 'GSUB_{}.fea'.format(i))
                for i in ['lookups', 'prefixing']
            ],
        )
        self.features_GPOS = Resource(
            self,
            os.path.join(constants.paths.FEATURES, 'GPOS.fea'),
            self._generate_features_GPOS,
        )
        # self.features_weight_class = Resource(
        #     self,
        #     None,
        #     self._generate_features_weight_class,
        # )
        # self.features_references = Resource(
        #     self,
        #     None,
        #     self._generate_features_references,
        # )
        self.fmndb = Resource(
            self,
            constants.paths.FMNDB,
            self._generate_fmndb,
        )
        self.goadb = Resource(
            self,
            constants.paths.GOADB,
            None,
        )

    def _check_inputs(self, inputs):
        results = collections.OrderedDict(
            (path, os.path.exists(path))
            for path in inputs
        )
        if not all(results.values()):
            raise SystemExit(
                '\n'.join('{}: {}'.format(k, v) for k, v in results.items())
            )

    def _generate_designspace(self, output):

        doc = mutatorMath.ufo.document.DesignSpaceDocumentWriter(
            hindkit._unwrap_path_relative_to_cwd(output)
        )

        for i, master in enumerate(self.family.masters):

            doc.addSource(

                path = hindkit._unwrap_path_relative_to_cwd(master.path),
                name = 'master-' + master.name,
                location = {'weight': master.interpolation_value},

                copyLib    = i == 0,
                copyGroups = i == 0,
                copyInfo   = i == 0,

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

            if self.options['prepare_kerning']:
                doc.writeKerning()

            doc.endInstance()

        doc.save()

    def prepare_styles(self, output): # STAGE I

        if not bool(self.family.masters):
            self.family.set_masters([
                hindkit.Master(self.family, i.name, i.interpolation_value)
                for i in self.family.styles
            ])
        self._check_inputs([i.path for i in self.family.masters])

        for style in self.styles_to_be_built:
            make_dir(temp(style.directory))

        if self.options['run_makeinstances']:

            self.designspace.prepare()

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
            for style in self.styles_to_be_built:
                self._simulate_makeInstancesUFO_postprocess

    def _simulate_makeInstancesUFO_postprocess(self, style):
        self._check_inputs([temp(style.path)])
        if self.options['run_checkoutlines'] or self.options['run_autohint']:
            options = {
                'doOverlapRemoval': self.options['run_checkoutlines'],
                'doAutoHint': self.options['run_autohint'],
                'allowDecimalCoords': False,
            }
            hindkit.patches.updateInstance(options, temp(style.path))

    def _generate_features_classes(self, output):

        self._check_inputs([temp(i.path) for i in self.styles_to_be_built])

        lines = []

        if self.options['prepare_mark_positioning']:

            glyph_classes = []
            glyph_classes.extend([(WriteFeaturesMarkFDK.kCombMarksClassName, glyph_filter_marks)])

            if self.options['prepare_mI_variants']:
                glyph_classes.extend([
                    ('MATRA_I_ALTS', hindkit.devanagari.glyph_filter_matra_i_alts),
                    ('BASES_ALIVE', hindkit.devanagari.glyph_filter_bases_alive),
                    ('BASES_DEAD', hindkit.devanagari.glyph_filter_bases_dead),
                    # ('BASES_FOR_WIDE_MATRA_II', hindkit.devanagari.glyph_filter_bases_for_wide_matra_ii),
                ])

            style_0 = self.styles_to_be_built[0].open_font(is_temp=True)

            glyph_order = [
                development_name for
                production_name, development_name, unicode_mapping in
                self.family.goadb
            ]
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

            for style in self.styles_to_be_built[1:]:
                font = style.open_font(is_temp=True)
                font.groups.update(style_0.groups)
                font.save()

        if lines:
            with open(output, 'w') as f:
                f.writelines(i + '\n' for i in lines)

    def _generate_features_tables(self, output):

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

    def _generate_features_languagesystems(self, output):

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

    def _generate_features_GSUB(self, output):
        pass

    def _generate_features_GPOS(self, output, style):
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
            if self.options['prepare_mI_variants']:
                hindkit.devanagari.prepare_features_devanagari(self, style) # NOTE: not pure GPOS

    def postprocess_kerning(self, original):
        postprocessed = original
        return postprocessed

    def _generate_features_weight_class(self, style):
        directory = temp(style.directory)
        with open(os.path.join(directory, 'WeightClass.fea'), 'w') as f:
            f.write('WeightClass {};\n'.format(str(style.weight_class)))

    def _generate_features_references(self, style):
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

    def _generate_fmndb(self, output):

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

        with open(output, 'w') as f:
            f.write(constants.templates.FMNDB_HEAD)
            f.writelines(i + '\n' for i in lines)

    def _generate_goadb(self, output):
        pass

    def _compile(self, style):

        self._check_inputs([temp(style.path), temp(self.fmndb.output), temp(self.goadb.output)])

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

        if not os.path.isdir(constants.paths.BUILD):
            os.makedirs(constants.paths.BUILD)

        subprocess.call(['makeotf'] + arguments)

        destination = constants.paths.ADOBE_FONTS
        if os.path.exists(otf_path) and os.path.isdir(destination):
            subprocess.call(['cp', '-f', otf_path, destination])

    def _finalize_options(self):

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
            self.options['run_stage_prepare_styles'] = '1' in stages
            self.options['run_stage_prepare_features'] = '2' in stages
            self.options['run_stage_compile'] = '3' in stages
        if args.options:
            options = str(args.options)
            self.options['run_makeinstances'] = '1' in options
            self.options['run_checkoutlines'] = '2' in options
            self.options['run_autohint'] = '3' in options
        if args.test:
            self.options['run_makeinstances'] = False
            self.options['run_checkoutlines'] = False
            self.options['run_autohint'] = False

        self.styles_to_be_built = self.family.styles
        if self.family.masters and (not self.options['run_makeinstances']):
            self.styles_to_be_built = self.family.get_styles_that_are_directly_derived_from_masters()

    def build(self):
        self._finalize_options()
        make_dir(constants.paths.TEMP)
        if self.options['run_stage_prepare_styles']:
            remove_files(temp(constants.paths.STYLES))
            make_dir(temp(constants.paths.STYLES))
            self.styles.prepare()
        if self.options['run_stage_prepare_features']:
            remove_files(temp(constants.paths.FEATURES))
            make_dir(temp(constants.paths.FEATURES))
            self.features_classes.prepare()
            self.features_tables.prepare()
            self.features_languagesystems.prepare()
            self.features_GSUB.prepare()
            for style in self.styles_to_be_built:
                self.features_GPOS.prepare(style)
                self._generate_features_weight_class(style)
                self._generate_features_references(style)
        if self.options['run_stage_compile']:
            self.fmndb.prepare()
            self.goadb.prepare()
            for style in self.styles_to_be_built:
                self._compile(style)

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
    subprocess.call(['rm', '-fr', path])

def make_dir(path):
    subprocess.call(['mkdir', '-p', path])

# ---

def overriding(abstract_path):
    return abstract_path

def temp(abstract_path):
    return os.path.join(constants.paths.TEMP, abstract_path)

# ---

import defcon
defcon.Glyph.insertAnchor = hindkit.patches.insertAnchor

def import_glyphs(
    source_paths,
    target_paths,
    save_as_paths = None,
    excluding_names = None,
    deriving_names = None,
):

    if not save_as_paths:
        save_as_paths = target_paths

    for source_path, target_path, save_as_path in zip(source_paths, target_paths, save_as_paths):

        source = defcon.Font(source_path)
        target = defcon.Font(target_path)

        new_names = set(source.keys())
        existing_names = set(target.keys())
        new_names.difference_update(existing_names)
        new_names.difference_update(set(excluding_names))
        new_names = sort_glyphs(source.glyphOrder, new_names)

        print('Imported glyphs:')
        for new_name in new_names:
            target.newGlyph(new_name)
            target[new_name].copyDataFromGlyph(source[new_name])
            print(new_name, end=', ')
        print()

        print('Derived glyphs:')
        for deriving_name in deriving_names:
            source_name = constants.misc.DERIVING_MAP[deriving_name]
            target.newGlyph(deriving_name)
            if source_name:
                target[deriving_name].width = target[source_name].width
            print(deriving_name, end=', ')
        print()

        remove_files(save_as_path)
        target.save(save_as_path)
