#! AFDKOPython

import sys, pickle, os, subprocess
import defcon

def main():

    family = pickle.load(sys.stdin)

    def normalize_path(path):
        return os.path.join(family['working_directory'], path)

    for master in family['masters']:

        output_path = normalize_path('masters/TEMP-{}.ufo'.format(master['name']))
        subprocess.call(['rm', '-fr', output_path])

        receiver = defcon.Font(normalize_path(master['path']))
        source = defcon.Font('resources/Hind-{}.ufo'.format(master['name']))

        receiver_names = receiver.keys()
        source_names = source.keys()

        new_names = [i for i in source_names if i not in receiver_names]
        for name in new_names:
            glyph = source[name]
            receiver.insertGlyph(glyph)

        receiver.save(output_path)

if __name__ == '__main__':
    main()
