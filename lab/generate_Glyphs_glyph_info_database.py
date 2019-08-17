import io, collections, re
import yaml, lxml.etree
import itfoundrykit.constants

class Database(object):

    @classmethod
    def from_files(cls, enabled_scripts):

        def constructor(loader, node):
            root = loader.construct_mapping(node, deep=True)
            return cls(root)

        yaml.add_constructor('!Database', constructor)
        yaml_raw = ''
        for file_name in ['_lib'] + enabled_scripts:
            with open('database/{}.yaml'.format(file_name)) as f:
                yaml_raw += f.read()
        database = yaml.load(yaml_raw)

        return database

    def __init__(self, root):

        root.pop('_lib')
        self.scripts = [Script(self, k, v) for k, v in list(root.items())]

    def export_glyphdata(self, glyphsapp_version=2):

        root = lxml.etree.Element('glyphData')

        for script in self.scripts:
            for glyph in script.glyphs:
                glyph_normalized = collections.OrderedDict()
                for k in SORT_KEYS:
                    v = glyph.__dict__[k]
                    if v is not None or k in ['name', 'category', 'description']:
                        if v is None:
                            v = ''
                        elif isinstance(v, list):
                            v = ', '.join(v)
                        glyph_normalized[k] = v
                lxml.etree.SubElement(root, 'glyph', attrib=glyph_normalized)

        dtd_string = DTD_2 if glyphsapp_version == 2 else DTD_1
        dtd_file = io.StringIO(dtd_string)
        doctype_string = DOCTYPE_TEMPLATE.format(dtd_string)

        if lxml.etree.DTD(dtd_file).validate(root) is True:
            with open('output/GlyphData.xml', 'w') as f:
                f.write(
                    lxml.etree.tostring(root, pretty_print=True, doctype=doctype_string)
                )
        else:
            print(dtd.error_log)

    def export_lists(self, export_optional_glyphs_separately = False):

        list_lines = []
        list_optional_lines = []
        for script in self.scripts:
            for glyph in script.glyphs:
                if export_optional_glyphs_separately and glyph.optional:
                    list_optional_lines.append(glyph.name)
                else:
                    list_lines.append(glyph.name)

        with open('output/list.txt', 'w') as f:
            f.write('\n'.join(list_lines) + '\n')
        with open('output/list_optional.txt', 'w') as f:
            f.write('\n'.join(list_optional_lines) + '\n')

    def export_goadb(self):

        goadb_lines = []
        for script in self.scripts:
            for glyph in script.glyphs:
                line = glyph.name + ' ' + glyph.name
                if glyph.unicode:
                    line += ' ' + 'uni' + glyph.unicode
                goadb_lines.append(line)

        with open('output/GlyphOrderAndAliasDB', 'w') as f:
            f.write('\n'.join(goadb_lines) + '\n')

class Script(object):

    def __init__(self, _database, name, glyph_tree):

        self.name = name
        self.prefix = itfoundrykit.constants.misc.SCRIPTS[self.name.title()]['abbreviation']

        glyphs = self._flatten_glyph_tree(glyph_tree)

        self.glyphs = [Glyph(self, _database, **i) for i in glyphs]

    def _flatten_glyph_tree(self, glyph_tree):
        glyphs = []
        for node in glyph_tree:
            if 'group' in node and 'inherited' in node:
                group = node.pop('group')
                inherited = node.pop('inherited')
                for node in group:
                    node.update({
                        k: v for k, v in list(inherited.items())
                        if k not in node
                    })
                    glyphs.append(node)
            else:
                glyphs.append(node)
        return glyphs

class Glyph(object):

    pattern = re.compile(r'<.*>')

    def __init__(

        self,

        _script,
        _database,

        name = None,

        category = None,
        subCategory = None,

        unicode = None,
        description = None,

        decompose = None,
        anchors = None,
        accents = None,
        script = None,

        base = None,
        optional = False,

    ):

        self.name = name
        self.optional = optional
        self.decompose = decompose

        if self.name:

            if '?' in self.name:
                self.name = self.name.replace('?', '')
                self.optional = True

            if self.decompose is None:
                match = self.pattern.search(self.name)
                if match:
                    self.name = self.pattern.sub('', self.name).strip()
                    self.decompose = match.group(0).strip('<>').split()
                # elif '_' in self.name:
                #     self.decompose = [
                #         _script.prefix + i for i in self.name[2:].split('_')
                #     ]
                # elif self.name.endswith('xA'):
                #     self.decompose = [
                #         self.name.replace('xA', 'A'), _script.prefix + 'Nukta'
                #     ]

        self.category = category
        self.subCategory = subCategory
        if self.category:
            if '> ' in self.category:
                parts = self.category.partition('> ')
                self.category    = parts[0]
                self.subCategory = parts[-1]

        self.unicode = unicode
        if self.unicode:
            if self.unicode.startswith('U+'):
                self.unicode = self.unicode[2:]
        if not self.unicode:
            self.unicode = itfoundrykit.constants.misc.NAME_TO_SCALAR_MAP.get(self.name)

        self.description = description
        if self.unicode and (not self.description):
            self.description = itfoundrykit.constants.misc.get_unicode_scalar_to_unicode_name_map()[self.unicode]

        self.anchors  = anchors
        self.accents = accents

        self.script = script
        if self.script is None:
            self.script = _script.name

        self.base = base


SORT_KEYS = '''\
script
unicode
name
decompose
category
subCategory
anchors
accents
description
'''.splitlines()

DTD_1 = '''
<!ELEMENT glyphData (glyph)+>
<!ELEMENT glyph EMPTY>
<!ATTLIST glyph
  unicode       CDATA  #IMPLIED
  unicode2      CDATA  #IMPLIED
  name          CDATA  #REQUIRED
  sortName      CDATA  #IMPLIED
  sortNameKeep  CDATA  #IMPLIED
  category      CDATA  #REQUIRED
  subCategory   CDATA  #IMPLIED
  script        CDATA  #IMPLIED
  description   CDATA  #REQUIRED
  legacy        CDATA  #IMPLIED
  alternative   CDATA  #IMPLIED
  decompose     CDATA  #IMPLIED
  anchors       CDATA  #IMPLIED
  accents       CDATA  #IMPLIED>
'''

DTD_2 = '''
<!ELEMENT glyphData (glyph)+>
<!ELEMENT glyph EMPTY>
<!ATTLIST glyph
  unicode       CDATA  #IMPLIED
  name          CDATA  #REQUIRED
  sortName      CDATA  #IMPLIED
  sortNameKeep  CDATA  #IMPLIED
  category      CDATA  #REQUIRED
  subCategory   CDATA  #IMPLIED
  script        CDATA  #IMPLIED
  description   CDATA  #REQUIRED
  production    CDATA  #IMPLIED
  altNames      CDATA  #IMPLIED
  decompose     CDATA  #IMPLIED
  anchors       CDATA  #IMPLIED
  accents       CDATA  #IMPLIED>
'''

DOCTYPE_TEMPLATE = '''\
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE glyphData [{}]>\
'''
