#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

FEATURES = '''\
table head {
  FontRevision 1.000;
} head;

include (../../../features/features.fea);\n'''

FMNDB_HEAD = '''\
# [PostScriptName]
#   f = Preferred Family Name
#   s = Subfamily/Style Name
#   l = Compatible Family Menu Name (Style-Linking Family Name)
#   m = 1, Macintosh Compatible Full Name (Deprecated)
'''

EXIT_MESSAGE = '''
[WARNING] Bad version of the package "{}".
          Version "{}" is specified in "build.py" while you have "{}".

[Note] Exit.
'''
