#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import collections, subprocess, os
import defcon

def draw(self, pen):
    """
    Draw the contour with **pen**.
    """
    # >>>
    # from ufoLib.pointPen import PointToSegmentPen
    # --- Patched with the line from defcon in FDK 64958 ---
    from robofab.pens.adapterPens import PointToSegmentPen
    # <<<
    pointPen = PointToSegmentPen(pen)
    self.drawPoints(pointPen)


def updateInstance(options, fontInstancePath):
    """
    Run checkOutlinesUFO and autohint, unless explicitly suppressed.
    """
    # >>>
    Options = collections.namedtuple("Options", "doAutoHint doOverlapRemoval allowDecimalCoords")
    options = Options(**options)
    LogMsg = collections.namedtuple("LogMsg", "log")
    logMsg = LogMsg(log=print)
    Popen = subprocess.Popen
    PIPE = subprocess.PIPE
    # <<<
    if options.doOverlapRemoval:
        logMsg.log("\tdoing overlap removal with checkOutlinesUFO %s ..." % (fontInstancePath))
        logList = []
        opList = ["-e", fontInstancePath]
        if options.allowDecimalCoords:
            opList.insert(0, "-dec")
        if os.name == "nt":
            opList.insert(0, "checkOutlinesUFO.cmd")
            proc = Popen(opList, stdout=PIPE)
        else:
            opList.insert(0, "checkOutlinesUFO")
            proc = Popen(opList, stdout=PIPE)
        while 1:
            output = proc.stdout.readline()
            if output:
                # >>>
                # print ".",
                # ---
                print(".", end=" ")
                # <<<
                logList.append(output)
            if proc.poll() != None:
                output = proc.stdout.readline()
                if output:
                    # >>>
                    # print output,
                    # ---
                    print(output, end=" ")
                    # <<<
                    logList.append(output)
                break
        log = "".join(logList)
        if not ("Done with font" in log):
            # >>>
            # print
            # ---
            print()
            # <<<
            logMsg.log(log)
            logMsg.log("Error in checkOutlinesUFO %s" % (fontInstancePath))
            raise(SnapShotError)
        else:
            # >>>
            # print
            # ---
            print()
            # <<<

    if options.doAutoHint:
        logMsg.log("\tautohinting %s ..." % (fontInstancePath))
        logList = []
        opList = ["-q", "-nb", fontInstancePath]
        if options.allowDecimalCoords:
            opList.insert(0, "-dec")
        if os.name == "nt":
            opList.insert(0, "autohint.cmd")
            proc = Popen(opList, stdout=PIPE)
        else:
            opList.insert(0, "autohint")
            proc = Popen(opList, stdout=PIPE)
        while 1:
            output = proc.stdout.readline()
            if output:
                # >>>
                # print output,
                # ---
                print(output, end=" ")
                # <<<
                logList.append(output)
            if proc.poll() != None:
                output = proc.stdout.readline()
                if output:
                    # >>>
                    # print output,
                    # ---
                    print(output, end=" ")
                    # <<<
                    logList.append(output)
                break
        log = "".join(logList)
        if not ("Done with font" in log):
            # >>>
            # print
            # ---
            print()
            # <<<
            logMsg.log(log)
            logMsg.log("Error in autohinting %s" % (fontInstancePath))
            raise(SnapShotError)
        else:
            # >>>
            # print
            # ---
            print()
            # <<<

    return
