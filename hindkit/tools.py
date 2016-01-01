#!/usr/bin/env AFDKOPython

from __future__ import division, absolute_import, print_function, unicode_literals

import subprocess, os, time, argparse
import defcon, mutatorMath.ufo.document, WriteFeaturesKernFDK, WriteFeaturesMarkFDK
import hindkit, hindkit.constants, hindkit.devanagari

import hindkit.patches
defcon.Glyph.insertAnchor = hindkit.patches.insertAnchor

class Builder(object):

    def __init__(
        self,
        family,
        fontrevision = '1.000',
        devanagari_offset_matrix = ((0, 0), (0, 0)),
    ):

        self.family = family
        self.fontrevision = fontrevision
        self.devanagari_offset_matrix = devanagari_offset_matrix

        for module in [
            'kerning',
            'mark_positioning',
            'mark_to_mark_positioning',
            'devanagari_matra_i_variants',
        ]:
            if self.family.__dict__['has_' + module]:
                self.__dict__['enable_' + module] = True
            else:
                self.__dict__['enable_' + module] = False

        self.prepare_styles = False
        self.prepare_features = False
        self.compile = False

        self.makeinstances = False
        self.checkoutlines = False
        self.autohint = False

        self.do_style_linking = False
        self.use_os_2_version_4 = False
        self.prefer_typo_metrics = False
        self.is_width_weight_slope_only = False

        self.keep_build_directory = False

        self.parser = argparse.ArgumentParser()
        options = self.parser.add_argument_group(
            title = 'build options',
            description = 'execute `python build.py` to run stages as specified in build.py, or append arguments to override.'
        )
        options.add_argument(
            '-s', '--stages', action = 'store',
            help = '"1" for "prepare_styles", "2" for "prepare_features", and "3" for "compile".'
        )
        options.add_argument(
            '-o', '--options', action = 'store',
            help = '"0" for none, "1" for "makeinstances", "2" for "checkoutlines", and "3" for "autohint".'
        )

        if not os.path.exists('temp'):
            subprocess.call(['mkdir', 'temp'])

        self.masters_path = hindkit.constants.paths.MASTERS
        self.instances_path = hindkit.constants.paths.INSTANCES
        self.designspace_path = hindkit.constants.paths.DESIGNSPACE
        self.fmndb_path = hindkit.constants.paths.FMNDB
        self.goadb_path = hindkit.constants.paths.GOADB
        self.build_path = hindkit.constants.paths.BUILD

    def _check_overriding(function):
        def decorator(self):
            path = self.__dict__[function.__name__[len('generate_'):] + '_path']
            if os.path.exists(path):
                print('copying')
                subprocess.call(['cp', '-fr', path, _get_temp_path(path)])
            else:
                function(self)
        return decorator

    def _parse_args(self):
        args = self.parser.parse_args()
        if args.stages:
            stages = str(args.stages)
            self.prepare_styles = True if '1' in stages else False
            self.prepare_features = True if '2' in stages else False
            self.compile = True if '3' in stages else False
        if args.options:
            options = str(args.options)
            self.makeinstances = True if '1' in options else False
            self.checkoutlines = True if '2' in options else False
            self.autohint = True if '3' in options else False

    def _check_master_files(self):
        is_missing = False
        message_lines = ['[WARNING] UFO master files missing:']
        for master in self.family.masters:
            if not os.path.exists(master.path):
                is_missing = True
                message_lines.append('\t' + master.path)
        if is_missing:
            message_lines.extend(['', '[Note] Exit.', ''])
            raise SystemExit('\n'.join(message_lines))

    def _reset_build_directory(self):
        print('[Note] Resetting the build directory...\n')
        subprocess.call(['rm', '-fr', hindkit.constants.paths.BUILD])
        subprocess.call(['mkdir', hindkit.constants.paths.BUILD])

    def set_options(self, options = []):

        for supported_option in [

            'prepare_styles',
            'prepare_features',
            'compile',

            'makeinstances',
            'checkoutlines',
            'autohint',

            'do_style_linking',
            'use_os_2_version_4',
            'prefer_typo_metrics',
            'is_width_weight_slope_only',

            'keep_build_directory',

        ]:
            if supported_option in options:
                self.__dict__[supported_option] = True

        self._parse_args()

    # @_check_overriding
    # def generate_masters(self):
    #     pass

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

            print('[NOTE] Excluding: {}'.format(excluding_names))
            print('[NOTE] Importing glyphs from `{}`...'.format(from_path))
            for new_name in new_names:
                print(new_name, end=' ')
                to_master.newGlyph(new_name)
                to_master[new_name].copyDataFromGlyph(from_master[new_name])
            else:
                print()

            print('[NOTE] Deriving glyphs...')
            for new_name in deriving_names:
                source_name = hindkit.constants.misc.DERIVING_MAP[new_name]
                print('({} =>) {}'.format(source_name, new_name), end=' ')
                to_master.newGlyph(new_name)
                if source_name:
                    to_master[new_name].width = to_master[source_name].width
            print('\n')

            subprocess.call(['rm', '-fr', save_to_path])
            to_master.save(save_to_path)

            print('[NOTE] Modified master is saved.')
            print()

    # @_check_overriding
    # def generate_instances(self):
    #     pass

    @_check_overriding
    def generate_designspace(self):

        doc = mutatorMath.ufo.document.DesignSpaceDocumentWriter(
            hindkit._unwrap_path_relative_to_cwd(self.designspace_path)
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

        for style in self.family.styles:

            doc.startInstance(
                name = 'instance-' + style.name,
                location = {'weight': style.interpolation_value},
                familyName = self.family.output_name,
                styleName = style.name,
                fileName = hindkit._unwrap_path_relative_to_cwd(style.path),
                postScriptFontName = style.output_full_name_postscript,
                # styleMapFamilyName = None,
                # styleMapStyleName = None,
            )

            doc.writeInfo()

            if self.family.has_kerning:
                doc.writeKerning()

            doc.endInstance()

        doc.save()

    @_check_overriding
    def generate_fmndb(self):

        f_name = self.family.output_name
        lines = []

        for style in self.family.styles:

            lines.append('')
            lines.append('[{}]'.format(style.output_full_name_postscript))
            lines.append('  f = {}'.format(f_name))
            lines.append('  s = {}'.format(style.name))

            l_name = style.output_full_name
            comment_lines = []

            if self.do_style_linking:
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

        with open(self.fmndb_path, 'w') as f:
            f.write(hindkit.constants.templates.FMNDB_HEAD)
            f.write('\n'.join(lines))
            f.write('\n')

    # @_check_overriding
    # def generate_build(self):
    #     pass

    def build(self, additional_arguments = []):

        print()
        print('[Note] {} Building...\n'.format(time.strftime('%H:%M:%S')))

        if self.makeinstances:
            self.enabled_styles = self.family.styles
        else:
            if len(self.family.masters) == 1 and len(self.family.styles) == 1:
                self.enabled_styles = self.family.styles
            else:
                self.enabled_styles = [self.family.styles[0], self.family.styles[-1]]

        if self.family.script in ['Devanagari', 'Gujarati']:
            hindkit.devanagari.SCRIPT_PREFIX = hindkit.constants.misc.INDIC_SCRIPTS[self.family.script.lower()]['abbreviation']

        if self.prepare_styles:

            self._check_master_files()

            if self.enable_mark_positioning:

                print('[Note] Generating the glyph class for combining marks...\n')

                glyph_classes = []

                glyph_classes.extend([('generated_MARKS', glyph_filter_marks)])

                if self.enable_devanagari_matra_i_variants:
                    print('[Note] Generating glyph classes for mI and mII matching...\n')
                    glyph_classes.extend([
                        ('generated_MATRA_I_ALTS', hindkit.devanagari.glyph_filter_matra_i_alts),
                        ('generated_BASES_ALIVE', devanagari.glyph_filter_bases_alive),
                        ('generated_BASES_DEAD', devanagari.glyph_filter_bases_dead),
                        # ('generated_BASES_FOR_WIDE_MATRA_II', hindkit.devanagari.glyph_filter_bases_for_wide_matra_ii),
                    ])

                generate_glyph_classes(
                    self.family,
                    self.family.masters[0].open_font(),
                    glyph_classes,
                    output_path = 'features/GENERATED_classes.fea'
                )

            print('[Note] Resetting instance directories...\n')
            subprocess.call(['rm', '-fr', hindkit.constants.paths.INSTANCES])
            subprocess.call(['mkdir', hindkit.constants.paths.INSTANCES])
            for style in self.enabled_styles:
                subprocess.call(['mkdir', style.directory])

            if self.makeinstances:

                print('[Note] Start interpolating masters...\n')

                # Prepare makeInstancesUFO arguments

                arguments = ['-d', self.designspace_path]

                if not self.checkoutlines:
                    arguments.append('-c')
                if not self.autohint:
                    arguments.append('-a')

                # Run makeInstancesUFO

                subprocess.call(['makeInstancesUFO'] + arguments)

                # Remove the log file

                subprocess.call(['rm', '-f', 'mutatorMath.log'])

                print()
                print('[Note] Done interpolating masters.\n')

            else:

                print('[Note] Copying masters to be instances.\n')

                for index, (master, style) in enumerate(zip(self.family.masters, self.enabled_styles)):

                    subprocess.call(['cp', '-fr', master.path, style.path])

                    font = style.open_font()
                    font.info.postscriptFontName = style.output_full_name_postscript

                    if index != 0:
                        font.groups.update(self.family.masters[0].open_font().groups)
                    font.save()

                    if self.checkoutlines:
                        subprocess.call(['checkOutlinesUFO', '-e', '-all', style.path])

                    if self.autohint:
                        subprocess.call(['autohint', '-q','-nb', style.path])

        if self.prepare_features and (self.enable_kerning or self.enable_mark_positioning):

            self._check_master_files()

            for style in self.enabled_styles:

                print('[Note] Generating features for "{}":\n'.format(style.name))

                if self.enable_kerning:
                    WriteFeaturesKernFDK.KernDataClass(
                        font = style.open_font(),
                        folderPath = style.directory,
                        minKern = 3,
                        writeTrimmed = False,
                        writeSubtables = True,
                        fileName = 'kern.fea',
                    )

                if self.enable_mark_positioning:

                    WriteFeaturesMarkFDK.kCombMarksClassName = 'generated_MARKS'

                    WriteFeaturesMarkFDK.MarkDataClass(
                        font = style.open_font(),
                        folderPath = style.directory,
                        trimCasingTags = False,
                        genMkmkFeature = self.enable_mark_to_mark_positioning,
                        writeClassesFile = True,
                        indianScriptsFormat = (
                            True if self.family.script.lower() in hindkit.constants.misc.INDIC_SCRIPTS
                            else False
                        ),
                    )

                    if self.enable_devanagari_matra_i_variants:

                        print()
                        print('\t[Note] mI matching...')

                        light, bold = self.devanagari_offset_matrix
                        light_min, light_max = light
                        bold_min, bold_max = bold

                        axis_start = self.family.masters[0].interpolation_value
                        axis_end = self.family.masters[-1].interpolation_value

                        axis_range = axis_end - axis_start

                        if axis_range == 0:
                            ratio = 1
                        else:
                            ratio = (style.interpolation_value - axis_start) / axis_range

                        offset_tuple = (
                            light_min + (bold_min - light_min) * ratio,
                            light_max + (bold_max - light_max) * ratio,
                        )

                        hindkit.devanagari.match_matra_i_alts(
                            style,
                            offset_range = offset_tuple
                        )

                print()

            print('[Note] Done generating features.\n')

        if self.compile:

            if not self.keep_build_directory:
                self._reset_build_directory()

            for style in self.enabled_styles:

                print('[Note] Compiling OTFs for "{}":'.format(style.name))

                font = style.open_font()
                if font.info.postscriptFontName != style.output_full_name_postscript:
                    font.info.postscriptFontName = style.output_full_name_postscript
                    print('\n[Note] Fixed the PostScript name.')
                    font.save()

                with open(os.path.join(style.directory, 'features'), 'w') as file:
                    file.write(hindkit.constants.templates.FEATURES)

                with open(os.path.join(style.directory, 'weightclass.fea'), 'w') as file:
                    file.write(hindkit.constants.templates.WEIGHTCLASS.format(str(style.weight_class)))

                otf_path = os.path.join(hindkit.constants.paths.BUILD, style.otf_name)

                # Prepare makeotf arguments

                arguments = [
                    '-f', style.path,
                    '-o', otf_path,
                    '-mf', self.family.fmndb_path,
                    '-gf', self.family.goadb_path,
                    '-r',
                    '-shw',
                    '-rev', self.fontrevision,
                    '-omitMacNames',
                ]

                # Style linking:

                if self.do_style_linking:
                    if style.is_bold:
                        arguments.append('-b')
                    if style.is_italic:
                        arguments.append('-i')

                # New bits in OS/2.fsSelection

                if self.use_os_2_version_4:
                    for digit, boolean in [
                        ('7', self.prefer_typo_metrics),
                        ('8', self.is_width_weight_slope_only),
                        ('9', style.is_oblique),
                    ]:
                        arguments.append('-osbOn' if boolean else '-osbOff')
                        arguments.append(digit)

                arguments.extend(additional_arguments)

                # Run makeotf

                subprocess.call(['makeotf'] + arguments)

                # Remove the project file

                project_file_path = os.path.join(style.directory, 'current.fpr')
                subprocess.call(['rm', '-f', project_file_path])

                # Copy the compiled font file to Adobe's fonts folder

                if os.path.exists(otf_path) and os.path.exists(hindkit.constants.paths.OUTPUT):
                    subprocess.call(['cp', '-f', otf_path, hindkit.constants.paths.OUTPUT])

                print()

            print('[Note] Done compiling OTFs.\n')

        print('[Note] {} Done building.\n'.format(time.strftime('%H:%M:%S')))

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

def generate_glyph_classes(family, font, glyph_classes, output_path = None):
    glyph_order = [
        development_name for
        production_name, development_name, unicode_mapping in
        family.goadb
    ]
    output_lines = []
    for class_name, filter_function in glyph_classes:
        glyph_names = [glyph.name for glyph in filter(filter_function, font)]
        glyph_names = sort_glyphs(glyph_order, glyph_names)
        font.groups.update({class_name: glyph_names})
        if output_path:
            output_lines.extend(
                compose_glyph_class_def_lines(class_name, glyph_names)
            )
    font.save()
    if output_path:
        with open(output_path, 'w') as file:
            file.write('\n'.join(output_lines))
