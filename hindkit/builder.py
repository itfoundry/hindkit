from __future__ import division, print_function, unicode_literals

import subprocess, os, pickle, time, argparse
import WriteFeaturesKernFDK, WriteFeaturesMarkFDK
import hindkit as kit

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

        ]:
            if supported_option in options:
                self.__dict__[supported_option] = True

    def generate_designspace(self):

        process = subprocess.Popen(
            ['AFDKOPython', 'AFDKOPython/generate_designspace.py'],
            stdin = subprocess.PIPE,
            cwd = kit.__path__[0],
        )
        process.communicate(pickle.dumps(self.family.dump()))

    def generate_fmndb(self):

        lines = []
        for style in self.family.styles:
            lines.append('')
            lines.append('[{}]'.format(style.output_full_name_postscript))
            lines.append('  f = {}'.format(self.family.output_name))
            lines.append('  s = {}'.format(style.name))

            if self.do_style_linking and (
                style.name == 'Regular' or style.is_bold or style.is_italic
            ):
                if style.is_bold:
                    lines.append('  # IsBoldStyle')
                if style.is_italic:
                    lines.append('  # IsItalicStyle')
            else:
                lines.append('  l = {}'.format(style.output_full_name))

        with open(kit.paths.FMNDN, 'w') as f:
            f.write(kit.templates.FMNDB_HEAD)
            f.write('\n'.join(lines))
            f.write('\n')

    def build(self, additional_arguments = []):

        self._parse_args()

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
            from hindkit.scripts import devanagari
            devanagari.SCRIPT_PREFIX = kit.linguistics.INDIC_SCRIPTS[self.family.script.lower()]['abbreviation']

        if self.prepare_styles:

            self._check_master_files()

            if self.enable_mark_positioning:

                print('[Note] Generating the glyph class for combining marks...\n')

                glyph_classes = []

                glyph_classes.extend([('generated_MARKS', glyph_filter_marks)])

                if self.enable_devanagari_matra_i_variants:
                    print('[Note] Generating glyph classes for mI and mII matching...\n')
                    glyph_classes.extend([
                        ('generated_MATRA_I_ALTS', devanagari.glyph_filter_matra_i_alts),
                        ('generated_BASES_FOR_MATRA_I', devanagari.glyph_filter_bases_for_matra_i),
                        ('generated_BASES_FOR_WIDE_MATRA_II', devanagari.glyph_filter_bases_for_wide_matra_ii),
                    ])

                generate_glyph_classes(
                    self.family,
                    self.family.masters[0].open_font(),
                    glyph_classes,
                    output_path = 'features/GENERATED_classes.fea'
                )

            print('[Note] Resetting instance directories...\n')
            subprocess.call(['rm', '-fr', kit.paths.INSTANCES])
            subprocess.call(['mkdir', kit.paths.INSTANCES])
            for style in self.enabled_styles:
                subprocess.call(['mkdir', style.directory])

            if self.makeinstances:

                print('[Note] Start interpolating masters...\n')

                # Prepare makeInstancesUFO arguments

                arguments = ['-d', 'font.designspace']

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
                            True if self.family.script.lower() in kit.linguistics.INDIC_SCRIPTS
                            else False
                        ),
                    )

                    if self.enable_devanagari_matra_i_variants:

                        print()
                        print('\t[Note] mI matching...')

                        light, bold = self.devanagari_offset_matrix
                        light_min, light_max = light
                        bold_min, bold_max = bold

                        ratio = style.interpolation_value / self.family.masters[-1].interpolation_value

                        offset_tuple = (
                            light_min + (bold_min - light_min) * ratio,
                            light_max + (bold_max - light_max) * ratio,
                        )

                        devanagari.match_matra_i_alts(
                            style,
                            offset_range = offset_tuple
                        )

                print()

            print('[Note] Done generating features.\n')

        if self.compile:

            print('[Note] Resetting the build directory...\n')
            subprocess.call(['rm', '-fr', kit.paths.BUILD])
            subprocess.call(['mkdir', kit.paths.BUILD])

            for style in self.enabled_styles:

                print('[Note] Compiling OTFs for "{}":'.format(style.name))

                font = style.open_font()
                if font.info.postscriptFontName != style.output_full_name_postscript:
                    font.info.postscriptFontName = style.output_full_name_postscript
                    print('\n[Note] Fixed the PostScript name.')
                    font.save()

                with open(os.path.join(style.directory, 'features'), 'w') as file:
                    file.write(kit.templates.FEATURES)

                with open(os.path.join(style.directory, 'weightclass.fea'), 'w') as file:
                    file.write(kit.templates.WEIGHTCLASS.format(str(style.weight_class)))

                otf_name = style.output_full_name_postscript + '.otf'
                otf_path = os.path.join(kit.paths.BUILD, otf_name)

                # Prepare makeotf arguments

                arguments = [
                    '-f', style.path,
                    '-o', otf_path,
                    '-mf', kit.paths.FMNDN,
                    '-gf', self.family.goadb_path,
                    '-r',
                    '-shw',
                    '-rev', self.fontrevision
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

                if os.path.exists(otf_path) and os.path.exists(kit.paths.OUTPUT):
                    subprocess.call(['cp', '-f', otf_path, kit.paths.OUTPUT])

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
