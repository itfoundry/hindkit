#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import os
import hindkit as kit

class BaseFile(object):

    def __init__(self, name, project=None):

        self.name = name
        self.file_format = None
        self.abstract_directory = ''

        self.temp = False
        self.temp_directory = kit.Project.directories['intermediates']

        self.project = project
        self.optional_filenames = []

        self.counter = 0

        self._filename = None
        self._extension = None
        self._filename_with_extension = None
        self._directory = None
        self._path = None

    @property
    def filename(self):
        return kit.fallback(self._filename, self.name)
    @filename.setter
    def filename(self, value):
        self._filename = value

    @property
    def extension(self):
        return kit.fallback(
            self._extension,
            self.file_format.lower() if self.file_format else None,
        )
    @extension.setter
    def extension(self, value):
        self._extension = value

    @property
    def filename_with_extension(self):
        return kit.fallback(
            self._filename_with_extension,
            self.filename + (('.' + self.extension) if self.extension else ''),
        )
    @filename_with_extension.setter
    def filename_with_extension(self, value):
        self._filename_with_extension = value

    @property
    def directory(self):
        directory = self.abstract_directory
        if self.temp:
            directory = os.path.join(self.temp_directory, directory)
        return kit.fallback(self._directory, directory)
    @directory.setter
    def directory(self, value):
        self._directory = value

    @property
    def path(self):
        return kit.fallback(
            self._path,
            os.path.join(self.directory, self.filename_with_extension),
        )
    @path.setter
    def path(self, value):
        self._path = value

    def check_override(self, *args, **kwargs):
        if self.temp == True and os.path.exists(self.path):
            return
        path_old = self.path
        self.temp = True
        if os.path.exists(path_old):
            print(path_old, 'exists.')
            path_new = self.path
            kit.copy(path_old, path_new)
        else:
            print(path_old, 'is missing.')
            self.generate(*args, **kwargs)
        for optional_filename in self.optional_filenames:
            f = kit.BaseFile(optional_filename)
            f.file_format = self.file_format
            f.abstract_directory = self.abstract_directory
            optional_path_old = f.path
            f.temp = True
            optional_path_new = f.path
            try:
                kit.copy(optional_path_old, optional_path_new)
            except IOError:
                if not os.path.exists(optional_path_old):
                    pass
                else:
                    raise

    def prepare(self, *args, **kwargs):
        self.check_override(*args, **kwargs)

    def generate(self):
        raise NotImplementedError("Can't generate {}.".format(self.path))
