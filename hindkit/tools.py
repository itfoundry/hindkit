#!/usr/bin/env AFDKOPython

from __future__ import division, absolute_import, print_function, unicode_literals

import subprocess, os, argparse
import defcon, mutatorMath.ufo.document, WriteFeaturesKernFDK, WriteFeaturesMarkFDK
import hindkit, hindkit.constants, hindkit.devanagari

import hindkit.patches
defcon.Glyph.insertAnchor = hindkit.patches.insertAnchor

class Builder(object):

    def __init__(
        self,
        family,
        fontrevision = '1.000',
        options = [],
    ):

        self.family = family
        self.fontrevision = fontrevision

        _reset(hindkit.constants.paths.TEMP)

        self.masters_path = hindkit.constants.paths.MASTERS
        self.styles_path = hindkit.constants.paths.INSTANCES
        self.designspace_path = hindkit.constants.paths.DESIGNSPACE
        self.fmndb_path = hindkit.constants.paths.FMNDB
        self.goadb_path = self.family.goadb_path
        self.build_path = hindkit.constants.paths.BUILD

        for supported_option in [

            'run_makeinstances',
            'run_checkoutlines',
            'run_autohint',

            'do_style_linking',
            'use_os_2_version_4',
            'prefer_typo_metrics',
            'is_width_weight_slope_only',

            # 'keep_build_directory',

        ]:
            if supported_option in options:
                self.__dict__[supported_option] = True
            else:
                self.__dict__[supported_option] = False

        # argparse

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

        self.allow_stage_prepare_styles = True
        self.allow_stage_prepare_features = True
        self.allow_stage_compile = True

        if args.stages:
            stages = str(args.stages)
            self.allow_stage_prepare_styles = True if '1' in stages else False
            self.allow_stage_prepare_features = True if '2' in stages else False
            self.allow_stage_compile = True if '3' in stages else False
        if args.options:
            options = str(args.options)
            self.run_makeinstances = True if '1' in options else False
            self.run_checkoutlines = True if '2' in options else False
            self.run_autohint = True if '3' in options else False
        if args.test:
            self.run_makeinstances = False

        if self.run_makeinstances:
            self.styles_to_be_built = self.family.styles()
        else:
            self.styles_to_be_built = self.family.get_styles_that_are_directly_derived_from_masters()

    def _check_overriding(function):
        def decorator(self):
            path = self.__dict__[function.__name__[len('prepare_'):] + '_path']
            if os.path.exists(path):
                subprocess.call(['cp', '-fr', path, _temp(path)])
                if function.__name__ == 'prepare_instances':
                    function(self, is_passing=True)
                else:
                    pass
            else:
                function(self)
        return decorator

    def _try_files(self, styles):
        is_missing = False
        message_lines = ['[WARNING] Files missing:']
        for style in styles:
            if not os.path.exists(style.path):
                is_missing = True
                message_lines.append('\t' + style.path)
        if is_missing:
            message_lines.extend(['', '[Note] Exit.', ''])
            raise SystemExit('\n'.join(message_lines))

    @_check_overriding
    def prepare_masters(self):
        print('[WARNING] No masters!')

    @_check_overriding
    def prepare_designspace(self):

        doc = mutatorMath.ufo.document.DesignSpaceDocumentWriter(
            hindkit._unwrap_path_relative_to_cwd(
                _temp(self.designspace_path)
            )
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
                    _temp(style.path)
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

    @_check_overriding
    def prepare_fmndb(self):

        f_name = self.family.output_name
        lines = []

        for style in self.styles_to_be_built:

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

        with open(_temp(self.fmndb_path), 'w') as f:
            f.write(hindkit.constants.templates.FMNDB_HEAD)
            f.write('\n'.join(lines))
            f.write('\n')

    @_check_overriding
    def prepare_goadb(self):
        print('[WARNING] Not able to prepare GOADB yet.')

    def _generate_glyph_classes(self, style, glyph_classes):
        font = style.open_font()
        output_path = hindkit.constants.paths.CLASSES
        glyph_order = [
            development_name for
            production_name, development_name, unicode_mapping in
            self.goadb_path
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

    @_check_overriding
    def prepare_styles(self): # STAGE I

        if not self.allow_stage_prepare_styles:
            return
        self.prepare_masters()
        self._try_files(self.family.masters)

        # print('[Note] Resetting instance directories...\n')
        _reset(_temp(self.styles_path))
        for style in self.styles_to_be_built:
            subprocess.call(['mkdir', _temp(style.directory)])

        if self.run_makeinstances:
            self._prepare_instances()
        else:
            # print('[Note] Copying masters to be instances.\n')
            for index, (master, style) in enumerate(zip(self.family.masters, self.styles_to_be_built)):
                subprocess.call(['cp', '-fr', master.path, _temp(style.path)])
                font = style.open_font(is_temp=True)
                font.info.postscriptFontName = style.output_full_name_postscript
                font.save()

    def _post_prepare_styles(self):
        if not run_makeinstances:
            self._simulate_makeInstancesUFO_postprocess(self.styles_to_be_built)

    def _prepare_instances(self, is_passing=False):

        self.prepare_designspace()

        # print('[Note] Start interpolating masters...\n')

        arguments = ['-d', _temp(self.designspace_path)]
        if not self.run_checkoutlines:
            arguments.append('-c')
        if not self.run_autohint:
            arguments.append('-a')

        subprocess.call(['makeInstancesUFO'] + arguments)

        # print()
        # print('[Note] Done interpolating masters.\n')

    def _simulate_makeInstancesUFO_postprocess(self, styles):
        self._try_files(self.styles_to_be_built)
        newInstancesList = [_temp(i.path) for i in styles]
        if self.run_checkoutlines or self.run_autohint:
            # print("Applying post-processing...")
            options = {
                'doOverlapRemoval': self.run_checkoutlines,
                'doAutoHint': self.run_autohint,
                'allowDecimalCoords': False,
            }
            for instancePath in newInstancesList:
                hindkit.patches.updateInstance(options, instancePath)

    def _pre_prepare_features(self):

        if not 'mark_positioning' in self.family.modules:
            return
        self._try_files(self.styles_to_be_built)

        # print('[Note] Generating the glyph class for combining marks...\n')
        for i, style in enumerate(self.styles_to_be_built):
            if i == 0:
                glyph_classes = []
                glyph_classes.extend([('generated_MARKS', glyph_filter_marks)])
                if 'devanagari_matra_i_variants' in self.family.modules:
                    # print('[Note] Generating glyph classes for mI and mII matching...\n')
                    glyph_classes.extend([
                        ('generated_MATRA_I_ALTS', hindkit.devanagari.glyph_filter_matra_i_alts),
                        ('generated_BASES_ALIVE', devanagari.glyph_filter_bases_alive),
                        ('generated_BASES_DEAD', devanagari.glyph_filter_bases_dead),
                        # ('generated_BASES_FOR_WIDE_MATRA_II', hindkit.devanagari.glyph_filter_bases_for_wide_matra_ii),
                    ])
                self._generate_glyph_classes(style, glyph_classes)
            else:
                font = style.open_font()
                font.groups.update(self.styles_to_be_built[0].open_font().groups)
                font.save()

    def _prepare_features_devanagari(self):

        light, bold = devanagari_offset_matrix
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

    # @_check_overriding
    def prepare_features(
        self,
        devanagari_offset_matrix = ((0, 0), (0, 0)),
    ):

        if not self.allow_stage_prepare_features:
            return
        if not ('kerning' or 'mark_positioning') in self.family.modules:
            return
        self._try_files(self.family.styles)

        # INPUTS

        self._pre_prepare_features()

        for style in self.styles_to_be_built:

            if 'kerning' in self.family.modules:
                WriteFeaturesKernFDK.KernDataClass(
                    font = style.open_font(is_temp=True),
                    folderPath = _temp(style.directory),
                    minKern = 3,
                    writeTrimmed = False,
                    writeSubtables = True,
                    fileName = 'kern.fea',
                )

            if 'mark_positioning' in self.family.modules:
                WriteFeaturesMarkFDK.kCombMarksClassName = 'generated_MARKS'
                WriteFeaturesMarkFDK.MarkDataClass(
                    font = style.open_font(is_temp=True),
                    folderPath = _temp(style.directory),
                    trimCasingTags = False,
                    genMkmkFeature = 'mark_to_mark_positioning' in self.family.modules,
                    writeClassesFile = True,
                    indianScriptsFormat = (
                        True if self.family.script.lower() in hindkit.constants.misc.INDIC_SCRIPTS
                        else False
                    ),
                )

                if 'devanagari_matra_i_variants' in self.family.modules:
                    self._prepare_features_devanagari()

    def compile(self):

        if not self.allow_stage_compile:
            return

        # INPUTS

        self.prepare_styles()
        self.prepare_features()
        self.prepare_fmndb()
        self.prepare_goadb()

        # BODY

        self._try_files(self.styles_to_be_built)
        _reset(self.build_path)

        for style in self.styles_to_be_built:

            _check_ps_name(style)

            with open(os.path.join(_temp(style.directory), 'features'), 'w') as file:
                file.write(hindkit.constants.templates.FEATURES)
            with open(os.path.join(_temp(style.directory), 'weightclass.fea'), 'w') as file:
                file.write(hindkit.constants.templates.WEIGHTCLASS.format(str(style.weight_class)))

            otf_path = os.path.join(self.build_path, style.otf_name)

            arguments = [
                '-f', _temp(style.path),
                '-o', otf_path,
                '-mf', _temp(self.fmndb_path),
                '-gf', _temp(self.goadb_path),
                '-r',
                '-shw',
                '-rev', self.fontrevision,
                '-omitMacNames',
            ]
            if self.do_style_linking:
                if style.is_bold:
                    arguments.append('-b')
                if style.is_italic:
                    arguments.append('-i')
            if self.use_os_2_version_4:
                for digit, boolean in [
                    ('7', self.prefer_typo_metrics),
                    ('8', self.is_width_weight_slope_only),
                    ('9', style.is_oblique),
                ]:
                    arguments.append('-osbOn' if boolean else '-osbOff')
                    arguments.append(digit)

            subprocess.call(['makeotf'] + arguments)

            project_file_path = os.path.join(_temp(style.directory), 'current.fpr')
            subprocess.call(['rm', '-f', project_file_path])

            if os.path.exists(otf_path) and os.path.exists(hindkit.constants.paths.OUTPUT):
                subprocess.call(['cp', '-f', otf_path, hindkit.constants.paths.OUTPUT])

    def build(self):
        self.compile()

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

def _temp(path):
    return os.path.join(hindkit.constants.paths.TEMP, path)

def _reset(path):
    subprocess.call(['rm', '-fr', path])
    subprocess.call(['mkdir', path])

def _check_ps_name(style):
    if style.file_name.endswith('.ufo'):
        font = style.open_font(is_temp=True)
        if font.info.postscriptFontName != style.output_full_name_postscript:
            font.info.postscriptFontName = style.output_full_name_postscript
            # print('\n[Note] Fixed the PostScript name.')
            font.save()

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

        # print('[NOTE] Excluding: {}'.format(excluding_names))
        # print('[NOTE] Importing glyphs from `{}`...'.format(from_path))
        for new_name in new_names:
            # print(new_name, end=' ')
            to_master.newGlyph(new_name)
            to_master[new_name].copyDataFromGlyph(from_master[new_name])
        else:
            # print()

        # print('[NOTE] Deriving glyphs...')
        for new_name in deriving_names:
            source_name = hindkit.constants.misc.DERIVING_MAP[new_name]
            # print('({} =>) {}'.format(source_name, new_name), end=' ')
            to_master.newGlyph(new_name)
            if source_name:
                to_master[new_name].width = to_master[source_name].width
        # print('\n')

        subprocess.call(['rm', '-fr', save_to_path])
        to_master.save(save_to_path)

        # print('[NOTE] Modified master is saved.')
        # print()
