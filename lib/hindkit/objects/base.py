#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os
import hindkit as kit

class BaseFile(object):

    _extra_filenames = ([], [])

    def __init__(
        self,
        name,
        file_format = None,
        abstract_directory = None,
        project = None,
        family = None,
        extra_filenames = None,
    ):

        self.name = name
        self.file_format = file_format

        if project and family is None:
            self.project = project
            self.family = self.project.family
        else:
            self.project = project
            self.family = family

        if abstract_directory is None and self.project:
            self.abstract_directory = kit.Project.directories["sources"]
        else:
            self.abstract_directory = abstract_directory

        if self.project and self.project.variant_tag:
            self.abstract_directory_variant = os.path.join(self.abstract_directory, self.project.variant_tag)
            if os.path.exists(self.abstract_directory_variant):
                self.abstract_directory = self.abstract_directory_variant

        self.extra_filenames = kit.fallback(extra_filenames, self._extra_filenames)
        self.file_group = []
        for filename in self.extra_filenames[0] + [self.name] + self.extra_filenames[1]:
            if filename == self.name:
                self.file_group.append(self)
            else:
                f = kit.BaseFile(
                    filename,
                    file_format = self.file_format,
                    abstract_directory = self.abstract_directory,
                    family = self.family,
                )
                self.file_group.append(f)

        self.counter = 0

        self._filename = None
        self._extension = None
        self._filename_with_extension = None
        self._directory = None
        self._path = None

    @property
    def filename(self):
        return kit.fallback(self._filename, self.name)

    @property
    def extension(self):
        return kit.fallback(
            self._extension,
            self.file_format.lower() if self.file_format else None,
        )

    @property
    def filename_with_extension(self):
        return kit.fallback(
            self._filename_with_extension,
            self.filename + (("." + self.extension) if self.extension else ""),
        )

    def get_directory(self, temp=True):
        directory = self.abstract_directory
        if temp:
            directory = kit.Project.temp(directory)
        return kit.fallback(self._directory, directory)

    def get_path(self, temp=True):
        return kit.fallback(
            self._path,
            os.path.join(self.get_directory(temp=temp), self.filename_with_extension),
        )

    def _copy(self, into_temp=True, whole_directory=False):
        if whole_directory:
            permanent = self.get_directory(temp=False)
            temp = self.get_directory()
        else:
            permanent = self.get_path(temp=False)
            temp = self.get_path()
        if into_temp:
            kit.makedirs(self.get_directory())
            kit.copy(permanent, temp)
            print("[COPIED INTO TEMP]", permanent, "=>", temp)
        else:
            kit.makedirs(self.get_directory(temp=False))
            kit.copy(temp, permanent)
            print("[COPIED OUT OF TEMP]", temp, "=>", permanent)

    def copy_into_temp(self, whole_directory=False):
        self._copy(into_temp=True, whole_directory=whole_directory)

    def copy_out_of_temp(self, whole_directory=False):
        self._copy(into_temp=False, whole_directory=whole_directory)

    def prepare(self, whole_directory=False):
        for f in self.file_group:
            if os.path.exists(f.get_path(temp=False)):
                if os.path.exists(f.get_path()):
                    print("[TEMP FILE ALREADY EXISTS]", f.get_path())
                    continue
                else:
                    f.copy_into_temp(whole_directory=whole_directory)
            else:
                try:
                    kit.makedirs(f.get_directory())
                    f.generate()
                    print("[GENERATED]", f.get_path())
                except NotImplementedError:
                    pass

    def generate(self):
        raise NotImplementedError("[CAN'T GENERATE] " + self.get_path())
