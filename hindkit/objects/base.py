#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

class BaseObject(object):

    @staticmethod
    def fallback(*candidates):
        # if len(candidates) == 1 and isinstance(candidates[0], collections.Iterable):
        #     candidates = candidates[0]
        for i in candidates:
            if i is not None:
                return i

    def __init__(self, name):

        self.name = name
        self.file_format = None
        self.abstract_directory = ''
        self.temp = False
        self.counter = 0

        self._filename_extension = None
        self._filename = None
        self._directory = None
        self._path = None

    @property
    def filename_extension(self):
        return self.fallback(self._filename_extension, self.file_format.lower())
    @filename_extension.setter
    def filename_extension(self, value):
        self._filename_extension = value

    @property
    def filename(self):
        return self.fallback(self._filename, self.name)
    @filename.setter
    def filename(self, value):
        self._filename = value

    @property
    def directory(self):
        directory = self.abstract_directory
        if self.temp:
            directory = os.path.join(kit.constants.paths.TEMP, directory)
        return self.fallback(self._directory, directory)
    @directory.setter
    def directory(self, value):
        self._directory = value

    @property
    def path(self):
        filename = self.filename
        if self.filename_extension:
            filename += '.' + self.filename_extension
        return self.fallback(
            self._path,
            os.path.join(self.directory, filename),
        )
    @path.setter
    def path(self, value):
        self._path = value

    def prepare(self, builder, *args, **kwargs):
        path = self.path
        if os.path.exists(path):
            if not self.temp:
                self.temp = True
                copy(path, self.path)
        else:
            self.temp = True
            self.generate(builder, *args, **kwargs)

    def generate(self):
        raise NotImplementedError("Can't generate {}.".format(self.path))
