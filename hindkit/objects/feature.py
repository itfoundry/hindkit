#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

from hindkit.objects.base import BaseObject

class Feature(BaseObject):

    def __init__(self, name, builder, style):

        super(FeatureFile, self).__init__(name)

        self.file_format = 'FEA'
        self.abstract_directory = kit.constants.paths.FEATURES

    def generate(self, builder):

        if self.name == 'classes':
            self.generate_classes(builder)
        elif self.name == 'tables':
            self.generate_tables(builder)

    def generate_classes(self, builder):

        builder._check_inputs([temp(i.path) for i in self.styles_to_produce])

        lines = []

        if builder.options['prepare_mark_positioning']:

            glyph_classes = []
            glyph_classes.extend([(WriteFeaturesMarkFDK.kCombMarksClassName, glyph_filter_marks)])

            if builder.options['match_mI_variants']:
                glyph_classes.extend([
                    ('MATRA_I_ALTS', devanagari.glyph_filter_matra_i_alts),
                    ('BASES_ALIVE', devanagari.glyph_filter_bases_alive),
                    ('BASES_DEAD', devanagari.glyph_filter_bases_dead),
                    # ('BASES_FOR_WIDE_MATRA_II', devanagari.glyph_filter_bases_for_wide_matra_ii),
                ])

            style_0 = builder.styles_to_produce[0].open_font(is_temp=True)

            glyph_order = builder.goadb.development_names
            for class_name, filter_function in glyph_classes:
                glyph_names = [
                    glyph.name for glyph in filter(
                        lambda glyph: filter_function(builder.family, glyph),
                        style_0,
                    )
                ]
                glyph_names = sort_glyphs(glyph_order, glyph_names)
                style_0.groups.update({class_name: glyph_names})
                lines.extend(
                    compose_glyph_class_def_lines(class_name, glyph_names)
                )
            style_0.save()

            for style in builder.styles_to_produce[1:]:
                font = style.open_font(is_temp=True)
                font.groups.update(style_0.groups)
                font.save()

        if lines:
            with open(self.path, 'w') as f:
                f.writelines(i + '\n' for i in lines)

    def generate_tables(self, builder):

        lines = []
        tables = collections.OrderedDict([
            ('hhea', []),
            ('OS/2', []),
            ('GDEF', []),
            ('name', []),
        ])

        tables['OS/2'].extend([
            'include (weightclass.fea);',
            'Vendor "{}";'.format(kit.constants.clients.Client(builder.family).table_OS_2['Vendor']),
        ])

        if builder.vertical_metrics:
            tables['hhea'].extend(
                i.format(**builder.vertical_metrics)
                for i in [
                    'Ascender {Ascender};',
                    'Descender {Descender};',
                    'LineGap {LineGap};',
                ]
            )
            tables['OS/2'].extend(
                i.format(**builder.vertical_metrics)
                for i in [
                    'TypoAscender {TypoAscender};',
                    'TypoDescender {TypoDescender};',
                    'TypoLineGap {TypoLineGap};',
                    'winAscent {winAscent};',
                    'winDescent {winDescent};',
                ]
            )

        # tables['OS/2'].extend(builder.generate_UnicodeRange)
        # tables['OS/2'].extend(builder.generate_CodePageRange)

        if builder.options['override_GDEF']:
            GDEF_records = {
                'bases': '',
                'ligatures': '',
                'marks': '',
                'components': '',
            }
            if builder.options['prepare_mark_positioning'] or os.path.exists(temp(os.path.join(kit.constants.paths.FEATURES, 'classes.fea'))):
                GDEF_records['marks'] = '@{}'.format(WriteFeaturesMarkFDK.kCombMarksClassName)
            if os.path.exists(temp(os.path.join(kit.constants.paths.FEATURES, 'classes_suffixing.fea'))):
                GDEF_records['marks'] = '@{}'.format('COMBINING_MARKS_GDEF')
            tables['GDEF'].extend([
                'GlyphClassDef {bases}, {ligatures}, {marks}, {components};'.format(**GDEF_records)
            ])

        tables['name'].extend(
            'nameid {} "{}";'.format(
                name_id,
                content.encode('unicode_escape').replace('\\x', '\\00').replace('\\u', '\\')
            )
            for name_id, content in kit.constants.clients.Client(builder.family).table_name.items()
            if content
        )

        for name, entries in tables.items():
            if entries:
                lines.append('table {} {{'.format(name))
                lines.extend('  ' + i for i in entries)
                lines.append('}} {};'.format(name))

        if lines:
            with open(self.path, 'w') as f:
                f.writelines(i + '\n' for i in lines)

    def generate_languagesystems(self, builder):

        lines = ['languagesystem DFLT dflt;']
        tag = kit.constants.misc.SCRIPTS[builder.family.script.lower()]['tag']
        if isinstance(tag, tuple):
            lines.append('languagesystem {} dflt;'.format(tag[1]))
            lines.append('languagesystem {} dflt;'.format(tag[0]))
        else:
            lines.append('languagesystem {} dflt;'.format(tag))

        if lines:
            with open(self.path, 'w') as f:
                f.writelines(i + '\n' for i in lines)

    def generate_GPOS(self, builder, style):
        directory = temp(style.directory)
        if builder.options['prepare_kerning']:
            WriteFeaturesKernFDK.KernDataClass(
                font = style.open_font(is_temp=True),
                folderPath = directory,
            )
            kern_path = os.path.join(directory, WriteFeaturesKernFDK.kKernFeatureFileName)
            if builder.options['postprocess_kerning'] and os.path.exists(kern_path):
                with open(kern_path) as f:
                    original = f.read()
                postprocessed = builder.postprocess_kerning(original)
                with open(kern_path, 'w') as f:
                    f.write(postprocessed)
        if builder.options['prepare_mark_positioning']:
            WriteFeaturesMarkFDK.MarkDataClass(
                font = style.open_font(is_temp=True),
                folderPath = directory,
                trimCasingTags = False,
                genMkmkFeature = builder.options['prepare_mark_to_mark_positioning'],
                writeClassesFile = True,
                indianScriptsFormat = builder.family.script.lower() in kit.constants.misc.SCRIPTS,
            )
            if builder.options['match_mI_variants']:
                devanagari.prepare_features_devanagari(
                    builder.options['position_marks_for_mI_variants'],
                    builder,
                    style,
                ) # NOTE: not pure GPOS

    def generate_weight_class(self, builder, style):
        directory = temp(style.directory)
        with open(os.path.join(directory, 'WeightClass.fea'), 'w') as f:
            f.write('WeightClass {};\n'.format(str(style.weight_class)))

    def generate_references(self, builder, style):
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
                abstract_path = os.path.join(kit.constants.paths.FEATURES, file_name + '.fea')
                if os.path.exists(temp(abstract_path)):
                    lines.append('include (../../{});'.format(abstract_path))
            if os.path.exists(os.path.join(directory, WriteFeaturesKernFDK.kKernFeatureFileName)):
                if builder.family.script.lower() in kit.constants.misc.SCRIPTS:
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
