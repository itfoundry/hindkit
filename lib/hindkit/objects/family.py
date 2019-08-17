import os, subprocess
import defcon, mutatorMath.ufo.document
import hindkit as kit

class Family(object):

    def __init__(
        self,
        trademark = None,
        name_script_independent = None,
        script_name = "Latin",
        append_script_name = False,
        name = None,
        client_name = None,
        source_tag = None,
        initial_release_year = None,
    ):

        self.trademark = trademark
        self.name_script_independent = kit.fallback(name_script_independent, self.trademark)
        self.script = kit.constants.SCRIPT_NAMES_TO_SCRIPTS.get(script_name)
        if name:
            self.name = name
        else:
            self.name = self.name_script_independent
            if script_name and append_script_name:
                self.name += " " + script_name
        self.name_postscript = kit.remove_illegal_chars_for_postscript_name_part(self.name)

        self.masters = None
        self.styles = None

        self.info = defcon.Font().info

        self.client_name = client_name
        self.source_tag = source_tag
        self.initial_release_year = initial_release_year

        self.project = None

    def get_client_data(self):
        return kit.Client(self, self.client_name)

    def set_masters(self, scheme=None):
        scheme = kit.fallback(scheme, [("Light", 0), ("Bold",  100)])
        self.masters = [
            kit.Master(self, name, location)
            for name, location in scheme
        ]

    def set_styles(self, scheme=None):
        scheme = kit.fallback(scheme, self.get_client_data().style_scheme)
        self.styles = [
            kit.Style(self, name, location, weight_and_width_class)
            for name, location, weight_and_width_class in scheme
        ]
        if self.masters is None:
            self.masters = []
        for master in self.masters:
            for style in self.styles:
                if style.location == master.location:
                    style.master = master
                    break

    def _has_kerning(self):
        raise NotImplementedError()

    def _has_mark_positioning(self):
        raise NotImplementedError()

    def _has_mI_variants(self):
        raise NotImplementedError()

    def prepare_styles(self):

        p = self.project
        styles = [i.style for i in p.products if not i.subsidiary]

        if p.options["run_makeinstances"]:
            self.generate_styles()
        elif self.masters:
            for style in styles:
                kit.copy(style.master.get_path(), style.get_path())
                if style.file_format == "UFO":
                    style.open().info.postscriptFontName = style.full_name_postscript
                    style.dirty = True
        else:
            for style in styles:
                style.prepare(whole_directory=True)

        for style in styles:
            if hasattr(style, "postprocess"):
                style.postprocess()
                style.refresh_groups()
                style.dirty = True
            style.save()

    def generate_styles(self):
        self.project.designspace.prepare()
        subprocess.call([
            "makeInstancesUFO",
            "-v",
            "-d", self.project.designspace.get_path(),
            "-a",
            "-c",
            "-n",
        ])


class DesignSpace(kit.BaseFile):

    def __init__(self, project, name="font"):
        super(DesignSpace, self).__init__(
            name,
            project = project,
            file_format = "DesignSpace",
        )
        self.doc = mutatorMath.ufo.document.DesignSpaceDocumentWriter(
            os.path.abspath(kit.relative_to_cwd(self.get_path()))
        )

    def generate(self):

        for i, master in enumerate(self.project.family.masters):

            self.doc.addSource(

                path = os.path.abspath(kit.relative_to_cwd(master.get_path())),
                name = "master " + master.name,
                location = {
                    "axis " + str(axis_number): axis_position
                    for axis_number, axis_position in enumerate(master.location)
                },

                copyLib    = i == 0,
                copyGroups = i == 0,
                copyInfo   = i == 0,

                # muteInfo = False,
                # muteKerning = False,
                # mutedGlyphNames = None,

            )

        for product in self.project.products:
            if not product.subsidiary:
                style = product.style
                self.doc.startInstance(
                    name = "instance " + style.name,
                    location = {
                        "axis " + str(axis_number): axis_position
                        for axis_number, axis_position in enumerate(style.location)
                    },
                    familyName = self.project.family.name,
                    styleName = style.name,
                    fileName = os.path.abspath(
                        kit.relative_to_cwd(style.get_path())
                    ),
                    postScriptFontName = style.full_name_postscript,
                    # styleMapFamilyName = None,
                    # styleMapStyleName = None,
                )
                self.doc.writeInfo()
                if self.project.options["prepare_kerning"]:
                    self.doc.writeKerning()
                self.doc.endInstance()
        self.doc.save()


class Fmndb(kit.BaseFile):

    LINES_HEAD = [
        "# [PostScriptName]",
        "#   f = Family Name",
        "#   s = Style Name",
        "#   l = Style-Linking Family Name",
    ]

    def __init__(self, project, name="FontMenuNameDB"):
        super(Fmndb, self).__init__(name, project=project)
        self.lines = []
        self.lines.extend(self.LINES_HEAD)

    def generate(self):

        for product in self.project.products:

            if product.subsidiary:
                continue

            self.lines.append("")
            self.lines.append("[" + product.full_name_postscript + "]")
            self.lines.append("  f = " + product.family.name)
            self.lines.append("  s = " + product.name)

            comment_lines = []

            if self.project.options["do_style_linking"]:
                name_parts = product.name.split(" ")
                try:
                    name_parts.remove("Regular")
                except ValueError:
                    pass
                if product.is_bold:
                    name_parts.remove("Bold")
                    comment_lines.append("  # IsBoldStyle")
                if product.is_italic:
                    name_parts.remove("Italic")
                    comment_lines.append("  # IsItalicStyle")
                product._style_linking_family_name = " ".join(
                    [product.family.name] + name_parts
                )

            if product.style_linking_family_name != product.family.name:
                self.lines.append("  l = " + product.style_linking_family_name)

            self.lines.extend(comment_lines)

        with open(self.get_path(), "w") as f:
            f.writelines(i + "\n" for i in self.lines)
