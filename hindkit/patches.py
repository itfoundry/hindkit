#!/usr/bin/env AFDKOPython

from __future__ import division, absolute_import, print_function, unicode_literals

# defcon.Glyph.insertAnchor

def insertAnchor(self, index, anchor):
    """
    Insert **anchor** into the glyph at index. The anchor
    must be a defcon :class:`Anchor` object or a subclass
    of that object. An error will be raised if the anchor's
    identifier conflicts with any of the identifiers within
    the glyph.

    This will post a *Glyph.Changed* notification.
    """
    # try:
    #     assert anchor.glyph != self
    # except AttributeError:
    #     pass
    if not isinstance(anchor, self._anchorClass):
        anchor = self.instantiateAnchor(anchorDict=anchor)
    assert anchor.glyph in (self, None), "This anchor belongs to another glyph."
    if anchor.glyph is None:
        if anchor.identifier is not None:
            identifiers = self._identifiers
            assert anchor.identifier not in identifiers
            identifiers.add(anchor.identifier)
        anchor.glyph = self
        anchor.beginSelfNotificationObservation()
    self.beginSelfAnchorNotificationObservation(anchor)
    self._anchors.insert(index, anchor)
    self.postNotification(notification="Glyph.AnchorsChanged")
    self.dirty = True

# makeInstancesUFO.updateInstance

import os, subprocess

def updateInstance(options, fontInstancePath):
    """
    Run checkOutlinesUFO and autohint, unless explicitly suppressed.
    """
    if options['doOverlapRemoval']:
        print("\tdoing overlap removal with checkOutlinesUFO %s ..." % (fontInstancePath))
        logList = []
        opList = ["-e", fontInstancePath]
        if options['allowDecimalCoords']:
            opList.insert(0, "-dec")
        if os.name == "nt":
            opList.insert(0, 'checkOutlinesUFO.cmd')
            proc = subprocess.Popen(opList, stdout=subprocess.PIPE)
        else:
            opList.insert(0, 'checkOutlinesUFO')
            proc = subprocess.Popen(opList, stdout=subprocess.PIPE)
        while 1:
            output = proc.stdout.readline()
            if output:
                print(".", end=' ')
                logList.append(output)
            if proc.poll() != None:
                output = proc.stdout.readline()
                if output:
                    print(output, end=' ')
                    logList.append(output)
                break
        log = "".join(logList)
        if not ("Done with font" in log):
            print()
            print(log)
            print("Error in checkOutlinesUFO %s" % (fontInstancePath))
            raise(SnapShotError)
        else:
            print()

    if options['doAutoHint']:
        print("\tautohinting %s ..." % (fontInstancePath))
        logList = []
        opList = ['-q', '-nb', fontInstancePath]
        if options['allowDecimalCoords']:
            opList.insert(0, "-dec")
        if os.name == "nt":
            opList.insert(0, 'autohint.cmd')
            proc = subprocess.Popen(opList, stdout=subprocess.PIPE)
        else:
            opList.insert(0, 'autohint')
            proc = subprocess.Popen(opList, stdout=subprocess.PIPE)
        while 1:
            output = proc.stdout.readline()
            if output:
                print(output, end=' ')
                logList.append(output)
            if proc.poll() != None:
                output = proc.stdout.readline()
                if output:
                    print(output, end=' ')
                    logList.append(output)
                break
        log = "".join(logList)
        if not ("Done with font" in log):
            print()
            print(log)
            print("Error in autohinting %s" % (fontInstancePath))
            raise(SnapShotError)
        else:
            print()

    return
