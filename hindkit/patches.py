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
