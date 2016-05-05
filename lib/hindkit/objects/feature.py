#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os, collections
import WriteFeaturesKernFDK, WriteFeaturesMarkFDK
import hindkit as kit

def glyph_filter_marks(family, glyph):
    has_mark_anchor = False
    for anchor in glyph.anchors:
        if anchor.name:
            if anchor.name.startswith('_'):
                has_mark_anchor = True
                break
    return has_mark_anchor

def sort_names(names, order=None):
    sorted_names = (
        [i for i in order if i in names] +
        [i for i in names if i not in order]
    )
    return sorted_names

class Feature(kit.BaseFile):

    def __init__(self, project, name, optional_filenames=None):
        super(Feature, self).__init__(name, project=project)
        self.optional_filenames = kit.fallback(optional_filenames, [])
        self.file_format = 'FEA'
        self.abstract_directory = kit.Project.directories['features']

    @staticmethod
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

    def generate(self, style=None):

        if self.name == 'classes':
            self.generate_classes()
        elif self.name == 'tables':
            self.generate_tables()
        elif self.name == 'languagesystems':
            self.generate_languagesystems()
        elif self.name == 'GPOS':
            self.generate_gpos(style)
        elif self.name == 'WeightClass':
            self.generate_weight_class(style)
        elif self.name == 'features':
            self.generate_references(style)

    def generate_classes(self):

        lines = []

        if self.project.options['prepare_mark_positioning']:

            glyph_classes = []
            glyph_classes.extend([(WriteFeaturesMarkFDK.kCombMarksClassName, glyph_filter_marks)])

            if self.project.options['match_mI_variants']:
                glyph_classes.extend([
                    ('MATRA_I_ALTS', kit.misc.glyph_filter_matra_i_alts),
                    ('BASES_ALIVE', kit.misc.glyph_filter_bases_alive),
                    ('BASES_DEAD', kit.misc.glyph_filter_bases_dead),
                    # ('BASES_FOR_WIDE_MATRA_II', kit.misc.glyph_filter_bases_for_wide_matra_ii),
                ])

            style_0 = self.project.products[0].style.open()

            glyph_order = self.project.glyph_data.glyph_order
            for class_name, filter_function in glyph_classes:
                glyph_names = [
                    glyph.name for glyph in filter(
                        lambda glyph: filter_function(self.project.family, glyph),
                        style_0,
                    )
                ]
                glyph_names = sort_names(glyph_names, glyph_order)
                style_0.groups.update({class_name: glyph_names})
                lines.extend(
                    self.compose_glyph_class_def_lines(class_name, glyph_names)
                )
            style_0.save()

            for style in (product.style for product in self.project.products[1:]):
                font = style.open()
                font.groups.update(style_0.groups)
                font.save()

        if lines:
            with open(self.path, 'w') as f:
                f.writelines(i + '\n' for i in lines)

    def generate_tables(self):

        info = self.project.family.info
        client = kit.Client(self.project.family)

        lines = []
        tables = collections.OrderedDict([
            ('hhea', []),
            ('OS/2', []),
            ('GDEF', []),
            ('name', []),
        ])

        tables['OS/2'].extend([
            'include (weightclass.fea);',
            'fsType {};'.format(client.table_OS_2['fsType']),
            'Vendor "{}";'.format(client.table_OS_2['Vendor']),
        ])

        set_vertical_metrics = False
        for field in (
            info.openTypeHheaAscender,
            info.openTypeHheaDescender,
            info.openTypeHheaLineGap,
            info.openTypeOS2TypoAscender,
            info.openTypeOS2TypoDescender,
            info.openTypeOS2TypoLineGap,
            info.openTypeOS2WinAscent,
            info.openTypeOS2WinDescent,
        ):
            if field is not None:
                set_vertical_metrics = True
                break

        if set_vertical_metrics:

            if info.unitsPerEm is None:
                raise SystemExit("`family.info.unitsPerEm` is unavailable.")

            if info.openTypeHheaAscender is None:
                info.openTypeHheaAscender = 800
            if info.openTypeHheaDescender is None:
                info.openTypeHheaDescender = -200
            if info.openTypeHheaLineGap is None:
                info.openTypeHheaLineGap = 0

            if client.vertical_metrics_strategy == 'Google Fonts':
                if info.openTypeOS2TypoAscender is None:
                    info.openTypeOS2TypoAscender = info.openTypeHheaAscender
                if info.openTypeOS2TypoDescender is None:
                    info.openTypeOS2TypoDescender = info.openTypeHheaDescender
                if info.openTypeOS2TypoLineGap is None:
                    info.openTypeOS2TypoLineGap = info.openTypeHheaLineGap
            elif client.vertical_metrics_strategy == 'ITF':
                extra_height = info.openTypeHheaAscender - info.openTypeHheaDescender - info.unitsPerEm
                if info.openTypeOS2TypoAscender is None:
                    info.openTypeOS2TypoAscender = info.openTypeHheaAscender - int(round(extra_height / 2))
                if info.openTypeOS2TypoDescender is None:
                    info.openTypeOS2TypoDescender = info.openTypeOS2TypoAscender - info.unitsPerEm
                if info.openTypeOS2TypoLineGap is None:
                    info.openTypeOS2TypoLineGap = info.openTypeHheaLineGap + extra_height

            if info.openTypeOS2WinAscent is None:
                info.openTypeOS2WinAscent = info.openTypeHheaAscender
            if info.openTypeOS2WinDescent is None:
                info.openTypeOS2WinDescent = abs(info.openTypeHheaDescender)

            tables['hhea'].extend([
                'Ascender {};'.format(info.openTypeHheaAscender),
                'Descender {};'.format(info.openTypeHheaDescender),
                'LineGap {};'.format(info.openTypeHheaLineGap),
            ])
            tables['OS/2'].extend([
                'TypoAscender {};'.format(info.openTypeOS2TypoAscender),
                'TypoDescender {};'.format(info.openTypeOS2TypoDescender),
                'TypoLineGap {};'.format(info.openTypeOS2TypoLineGap),
                'winAscent {};'.format(info.openTypeOS2WinAscent),
                'winDescent {};'.format(info.openTypeOS2WinDescent),
            ])

        # tables['OS/2'].extend(self.project.generate_UnicodeRange)
        # tables['OS/2'].extend(self.project.generate_CodePageRange)

        if self.project.options['override_GDEF']:
            GDEF_records = {
                'bases': '',
                'ligatures': '',
                'marks': '',
                'components': '',
            }
            if self.project.options['prepare_mark_positioning'] or os.path.exists(os.path.join(self.directory, 'classes.fea')):
                GDEF_records['marks'] = '@{}'.format(WriteFeaturesMarkFDK.kCombMarksClassName)
            if os.path.exists(os.path.join(self.directory, 'classes_suffixing.fea')):
                GDEF_records['marks'] = '@{}'.format('COMBINING_MARKS_GDEF')
            tables['GDEF'].extend([
                'GlyphClassDef {bases}, {ligatures}, {marks}, {components};'.format(**GDEF_records)
            ])

        tables['name'].extend(
            'nameid {} "{}";'.format(
                name_id,
                content.encode('unicode_escape').replace('\\x', '\\00').replace('\\u', '\\')
            )
            for name_id, content in client.table_name.items()
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

    def generate_languagesystems(self):

        lines = ['languagesystem DFLT dflt;']
        for tag in self.project.family.script.tags:
            lines.append('languagesystem {} dflt;'.format(tag))

        if lines:
            with open(self.path, 'w') as f:
                f.writelines(i + '\n' for i in lines)

    def generate_gpos(self, style):

        directory = style.directory

        if self.project.options['prepare_kerning']:

            WriteFeaturesKernFDK.KernDataClass(
                font = style.open(),
                folderPath = directory,
            )

            try:
                self.project.postprocess_kerning
            except AttributeError:
                pass
            else:
                kern_path = os.path.join(
                    directory,
                    WriteFeaturesKernFDK.kKernFeatureFileName,
                )
                if os.path.exists(kern_path):
                    with open(kern_path) as f:
                        content = f.read()
                    with open(kern_path, 'w') as f:
                        f.write(self.project.postprocess_kerning(content))

        if self.project.options['prepare_mark_positioning']:
            WriteFeaturesMarkFDK.MarkDataClass(
                font = style.open(),
                folderPath = directory,
                trimCasingTags = False,
                genMkmkFeature = self.project.options['prepare_mark_to_mark_positioning'],
                writeClassesFile = True,
                indianScriptsFormat = self.project.family.script.is_indic,
            )
            if self.project.options['match_mI_variants']:
                kit.misc.prepare_features_devanagari(style)
                # NOTE: not pure GPOS

    def generate_weight_class(self, style):
        with open(os.path.join(style.directory, 'WeightClass.fea'), 'w') as f:
            f.write('WeightClass {};\n'.format(str(style.weight_class)))

    def generate_references(self, style):
        with open(os.path.join(style.directory, 'features'), 'w') as f:
            lines = ['table head { FontRevision 1.000; } head;']
            for filename in [
                'classes',
                'classes_suffixing',
                'tables',
                'languagesystems',
                'GSUB_prefixing',
                'GSUB_lookups',
                'GSUB',
            ]:
                path = os.path.join(self.directory, filename + '.fea')
                if os.path.exists(path):
                    lines.append('include ({});'.format(os.path.relpath(path, style.directory)))
            if os.path.exists(os.path.join(style.directory, WriteFeaturesKernFDK.kKernFeatureFileName)):
                if self.project.family.script.is_indic:
                    kerning_feature_name = 'dist'
                else:
                    kerning_feature_name = 'kern'
                lines.append(
                    'feature {0} {{ include ({1}); }} {0};'.format(
                        kerning_feature_name,
                        WriteFeaturesKernFDK.kKernFeatureFileName,
                    )
                )
            if os.path.exists(os.path.join(style.directory, WriteFeaturesMarkFDK.kMarkClassesFileName)):
                lines.append('include ({});'.format(WriteFeaturesMarkFDK.kMarkClassesFileName))
            for feature_name, filename in [
                ('mark', WriteFeaturesMarkFDK.kMarkFeatureFileName),
                ('mkmk', WriteFeaturesMarkFDK.kMkmkFeatureFileName),
                ('abvm', WriteFeaturesMarkFDK.kAbvmFeatureFileName),
                ('blwm', WriteFeaturesMarkFDK.kBlwmFeatureFileName),
            ]:
                if os.path.exists(os.path.join(style.directory, filename)):
                    lines.append('feature {0} {{ include ({1}); }} {0};'.format(feature_name, filename))
            f.writelines(i + '\n' for i in lines)
