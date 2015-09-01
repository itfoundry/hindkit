from __future__ import division, print_function, unicode_literals

__version__ = '0.2.1'

from hindkit.constants import paths, linguistics, styles, templates
from hindkit.family    import Family, Master, Style
from hindkit.builder   import Builder

def confirm_version(required_version):
    if __version__ != required_version:
        message = templates.EXIT_MESSAGE.format(required_version, __version__)
        raise SystemExit(message)
