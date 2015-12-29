#! AFDKOPython

from __future__ import division, print_function, unicode_literals

import sys, pickle, os, subprocess
import defcon

def main():

    info = pickle.load(sys.stdin)

    def normalize_path(path):
        return os.path.join(info['working_directory'], path)

    font_source_path = normalize_path(info['source_path'])
    font_source = defcon.Font(font_source_path)

    font_target_path_old = normalize_path(info['target_path'][:-9] + '.ufo')
    font_target_path_new = normalize_path(info['target_path'])
    font_target = defcon.Font(font_target_path_old)

    new_names = set(font_source.keys())
    insider_names = set(font_target.keys())
    excluding_names = set(info['excluding'])
    deriving_names = set(info['deriving'])

    new_names.difference_update(insider_names)
    new_names.difference_update(excluding_names)

    print('[NOTE] Incerting glyphs from `{}`...'.format(info['source_path']))
    print()
    print('[NOTE] Excluding: {}'.format(info['excluding']))

    for name in new_names:
        glyph = font_source[name]
        print(glyph.name, end=' ')
        font_target.insertGlyph(glyph)
    print('\n')

    DERIVING_MAP = {
        'CR': 'space',
        'uni00A0': 'space',
        'NULL': None,
        'uni200B': None,
    }

    print('[NOTE] Deriving glyphs...')
    for glyph_target_name in deriving_names:
        glyph_source_name = DERIVING_MAP[glyph_target_name]
        print(glyph_target_name, end=' ')
        if glyph_source_name:
            font_target.newGlyph(glyph_target_name)
            font_target[glyph_target_name]._set_width(
                font_target[glyph_source_name].width
            )
        else:
            if glyph_target_name not in font_target:
                font_target.newGlyph(glyph_target_name)
    print('\n')

    subprocess.call(['rm', '-fr', font_target_path_new])
    font_target.save(font_target_path_new)

    print('[NOTE] Modified master is saved.')
    print()

if __name__ == '__main__':
    main()
