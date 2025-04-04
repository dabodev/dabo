# -*- coding: utf-8 -*-
#! /usr/bin/env python

"""Replace tabs with spaces in argument files.  Print names of changed files."""

import getopt
import os
import sys


def main():
    tabsize = 8
    try:
        opts, args = getopt.getopt(sys.argv[1:], "t:")
        if not args:
            raise getopt.error("At least one file argument required")
    except getopt.error as msg:
        print(msg)
        print("usage:", sys.argv[0], "[-t tabwidth] file ...")
        return
    for optname, optvalue in opts:
        if optname == "-t":
            tabsize = int(optvalue)

    for filename in args:
        process(filename, tabsize)


def process(filename, tabsize, saveBackup=True):
    try:
        f = open(filename)
        text = f.read()
        f.close()
    except IOError as msg:
        print("%r: I/O error: %s" % (filename, msg))
        return
    newtext = text.expandtabs(tabsize)
    if newtext == text:
        return
    if saveBackup:
        backup = filename + "~"
        try:
            os.unlink(backup)
        except os.error:
            pass
        try:
            os.rename(filename, backup)
        except os.error:
            pass
    f = open(filename, "w")
    f.write(newtext)
    f.close()


#     print filename

if __name__ == "__main__":
    main()
