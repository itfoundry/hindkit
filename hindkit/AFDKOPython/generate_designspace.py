#! AFDKOPython

from __future__ import division, absolute_import, print_function, unicode_literals

import sys, pickle, os
from mutatorMath.ufo.document import DesignSpaceDocumentWriter

def main():
    family = pickle.load(sys.stdin)
    generate_designspace(family, 'temp/font.designspace')

def generate_designspace(family, path):

    def normalize_path(path):
        return os.path.join(family['working_directory'], path)

    doc = DesignSpaceDocumentWriter(normalize_path(path))

    for i, master in enumerate(family['masters']):

        doc.addSource(

            path = normalize_path(master['path']),
            name = 'master-' + master['name'],
            location = {'weight': master['interpolation_value']},

            copyLib    = True if i == 0 else False,
            copyGroups = True if i == 0 else False,
            copyInfo   = True if i == 0 else False,

            # muteInfo = False,
            # muteKerning = False,
            # mutedGlyphNames = None,

        )

    for style in family['styles']:

        doc.startInstance(
            name = 'instance-' + style['name'],
            location = {'weight': style['interpolation_value']},
            familyName = family['output_name'],
            styleName = style['name'],
            fileName = normalize_path(style['path']),
            postScriptFontName = style['output_full_name_postscript'],
            # styleMapFamilyName = None,
            # styleMapStyleName = None,
        )

        doc.writeInfo()

        if family['has_kerning']:
            doc.writeKerning()

        doc.endInstance()

    doc.save()

if __name__ == '__main__':
    main()
