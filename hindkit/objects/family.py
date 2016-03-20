#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

class Family(object):

    def __init__(
        self,
        client = None,
        trademark = None,
        script = None,
        append_script_name = False,
        name = None,
    ):

        self.client = client

        self.trademark = trademark
        self.script = script
        self.append_script_name = append_script_name

        if name:
            self.name = name
        else:
            self.name = self.trademark
            if self.script and self.append_script_name:
                self.name += ' ' + self.script
        self.name_postscript = self.name.replace(' ', '')

        self.masters = []
        self.styles = []

        self.info = kit.defcon_patched.Font().info

    def set_masters(self, masters=None):
        if masters:
            self.masters = masters
        else:
            self.masters = [Master(self, 'Light', 0), Master(self, 'Bold', 100)]

    def set_styles(self, style_scheme=None):
        if not style_scheme:
            style_scheme = kit.constants.clients.Client(self).style_scheme
        self.styles = [
            Style(
                self,
                name = style_name,
                weight_location = weight_location,
                weight_class = weight_class,
            )
            for style_name, weight_location, weight_class in style_scheme
        ]
        if not self.masters:
            self.set_masters([
                Master(self, i.name, i.weight_location)
                for i in self.styles
            ])

    def get_styles_that_are_directly_derived_from_masters(self):
        master_positions = [
            master.weight_location for master in self.masters
        ]
        styles_that_are_directly_derived_from_masters = []
        for style in self.styles:
            if style.weight_location in master_positions:
                styles_that_are_directly_derived_from_masters.append(style)
        return styles_that_are_directly_derived_from_masters

    def _has_kerning(self): #TODO
        pass

    def _has_mark_positioning(self): #TODO
        pass

    def _has_mI_variants(self): #TODO
        pass
