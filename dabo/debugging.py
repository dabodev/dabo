# -*- coding: utf-8 -*-
import inspect
import os
import sys
import time
from io import StringIO

from . import settings
from .lib.utils import ustr


def logPoint(msg="", levels=None):
    if levels is None:
        # Default to 6, which works in most cases
        levels = 6
    stack = inspect.stack()
    # get rid of logPoint's part of the stack:
    stack = stack[1:]
    stack.reverse()
    output = StringIO()
    if msg:
        output.write(ustr(msg) + "\n")

    stackSection = stack[-1 * levels :]
    for stackLine in stackSection:
        frame, filename, line, funcname, lines, unknown = stackLine
        if filename.endswith("/unittest.py"):
            # unittest.py code is a boring part of the traceback
            continue
        if filename.startswith("./"):
            filename = filename[2:]
        output.write(f"{filename}:{line} in {funcname}:\n")
        if lines:
            output.write(f"    {''.join(lines)[:-1]}\n")
    s = output.getvalue()
    # I actually logged the result, but you could also print it:
    return s


def mainProgram():
    """Returns the name of first program in the call stack"""
    return inspect.stack()[-1][1]


def loggit(fnc):
    """Decorator function to create a log of all methods as they are called. To use
    it, modify all your methods from:

        def someMethod(...):

    to:

        @loggit
        def someMethod(...):

    Be sure to add:

    from dBug import loggit

    to the import statements for every file that uses loggit. You can set the name and
    location of the log file by overriding the setting for settings.loggitFile. By default, this
    value will be 'functionCall.log'.
    """
    try:
        loggit.fhwr
    except AttributeError:
        # ... open it
        fname = settings.loggitFile
        loggit.fhwr = open(fname, "a")

    def wrapped(*args, **kwargs):
        loggit.fhwr.write(f"\n{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        loggit.fhwr.write(f"{fnc}\n")
        if args:
            loggit.fhwr.write("\tARGS:")
            for ag in args:
                try:
                    loggit.fhwr.write(f" {ag}")
                except Exception as e:
                    loggit.fhwr.write(f" ERR: {e}")
            loggit.fhwr.write("\n")
        if kwargs:
            loggit.fhwr.write(f"\tKWARGS:{kwargs}\n")
        for stk in inspect.stack()[1:-7]:
            loggit.fhwr.write(f"\t{os.path.split(stk[1])[1]}, {stk[3]}, line {stk[2]}\n")
        result = fnc(*args, **kwargs)
        loggit.fhwr.flush()
        return result

    wrapped.__doc__ = fnc.__doc__
    return wrapped
