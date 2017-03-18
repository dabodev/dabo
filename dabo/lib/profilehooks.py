# -*- coding: utf-8 -*-
"""
Profiling hooks

This module contains a couple of decorators (`profile` and `coverage`) that
can be used to wrap functions and/or methods to produce profiles and line
coverage reports.

Usage example (Python 2.4 or newer)::

    from profilehooks import profile, coverage

    @profile    # or @coverage
    def fn(n):
        if n < 2: return 1
        else: return n * fn(n-1)

    print fn(42)

Usage example (Python 2.3 or older)::

    from profilehooks import profile, coverage

    def fn(n):
        if n < 2: return 1
        else: return n * fn(n-1)

    # Now wrap that function in a decorator
    fn = profile(fn) # or coverage(fn)

    print fn(42)

Reports for all thusly decorated functions will be printed to sys.stdout
on program termination.  You can alternatively request for immediate
reports for each call by passing immediate=True to the profile decorator.

There's also a @timecall decorator for printing the time to sys.stderr
every time a function is called, when you just want to get a rough measure
instead of a detailed (but costly) profile.

Caveats

  A thread on python-dev convinced me that hotshot produces bogus numbers.
  See http://mail.python.org/pipermail/python-dev/2005-November/058264.html

  I don't know what will happen if a decorated function will try to call
  another decorated function.  All decorators probably need to explicitly
  support nested profiling (currently TraceFuncCoverage is the only one that
  supports this, while HotShotFuncProfile has support for recursive functions.)

  Profiling with hotshot creates temporary files (\*.prof and \*.prof.pickle for
  profiling, \*.cprof for coverage) in the current directory.  These files are
  not cleaned up.  (In fact, the \*.pickle versions are intentionally written
  out in case you want to look at the profiler results without having to parse
  the big \*.prof file with hotshot.stats.load, which takes ages.  Just unpickle
  the file and you'll get a pstats object.)

  Coverage analysis with hotshot seems to miss some executions resulting in
  lower line counts and some lines errorneously marked as never executed.  For
  this reason coverage analysis now uses trace.py which is slower, but more
  accurate.

  Decorating functions causes doctest.testmod() to ignore doctests in those
  functions.

Copyright (c) 2004--2006 Marius Gedminas <marius@pov.lt>

Released under the MIT licence since December 2006:

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.

(Previously it was distributed under the GNU General Public Licence.)
"""
# $Id: profilehooks.py 54 2006-12-05 23:10:37Z mg $

__author__ = "Marius Gedminas (marius@gedmin.as)"
__copyright__ = "Copyright 2004-2006, Marius Gedminas"
__license__ = "MIT"
__version__ = "1.0"
__date__ = "2006-12-06"


import atexit
import inspect
import sys
import re
import pickle as pickle

# For profiling
from profile import Profile
import pstats

# For hotshot profiling (inaccurate!)
import hotshot
import hotshot.stats

# For trace.py coverage
import trace

# For hotshot coverage (inaccurate!; uses undocumented APIs; might break)
import _hotshot
import hotshot.log

# For timecall
import time


def profile(fn=None, skip=0, filename=None, immediate=False):
    """
    Mark `fn` for profiling.

    If `immediate` is False, profiling results will be printed to sys.stdout on
    program termination.  Otherwise results will be printed after each call.

    If `skip` is > 0, first `skip` calls to `fn` will not be profiled.

    If `filename` is specified, the profile stats will be pickled and stored in
    a file.

    Usage::

        def fn(...):
            ...
        fn = profile(fn, skip=1)

    If you are using Python 2.4, you should be able to use the decorator
    syntax::

        @profile(skip=3)
        def fn(...):
            ...

    or just::

        @profile
        def fn(...):
            ...

    """
    if fn is None: # @profile() syntax -- we are a decorator maker
        def decorator(fn):
            return profile(fn, skip=skip, filename=filename,
                           immediate=immediate)
        return decorator
    # @profile syntax -- we are a decorator.
    fp = FuncProfile(fn, skip=skip, filename=filename, immediate=immediate)
         # or HotShotFuncProfile
    # We cannot return fp or fp.__call__ directly as that would break method
    # definitions, instead we need to return a plain function.
    def new_fn(*args, **kw):
        return fp(*args, **kw)
    new_fn.__doc__ = fn.__doc__
    return new_fn


def coverage(fn):
    """
    Mark `fn` for line coverage analysis.

    Results will be printed to sys.stdout on program termination.

    Usage::

        def fn(...):
            ...
        fn = coverage(fn)

    If you are using Python 2.4, you should be able to use the decorator
    syntax::

        @coverage
        def fn(...):
            ...

    """
    fp = TraceFuncCoverage(fn) # or HotShotFuncCoverage
    # We cannot return fp or fp.__call__ directly as that would break method
    # definitions, instead we need to return a plain function.
    def new_fn(*args, **kw):
        return fp(*args, **kw)
    new_fn.__doc__ = fn.__doc__
    return new_fn


def coverage_with_hotshot(fn):
    """
    Mark `fn` for line coverage analysis.

    Uses the 'hotshot' module for fast coverage analysis.

    BUG: Produces inaccurate results.

    See the docstring of `coverage` for usage examples.
    """
    fp = HotShotFuncCoverage(fn)
    # We cannot return fp or fp.__call__ directly as that would break method
    # definitions, instead we need to return a plain function.
    def new_fn(*args, **kw):
        return fp(*args, **kw)
    new_fn.__doc__ = fn.__doc__
    return new_fn


class FuncProfile:
    """Profiler for a function (uses profile)."""

    # This flag is shared between all instances
    in_profiler = False

    def __init__(self, fn, skip=0, filename=None, immediate=False):
        """
        Creates a profiler for a function.

        Every profiler has its own log file (the name of which is derived from
        the function name).

        HotShotFuncProfile registers an atexit handler that prints profiling
        information to sys.stderr when the program terminates.

        The log file is not removed and remains there to clutter the current
        working directory.
        """
        self.fn = fn
        self.filename = filename
        self.immediate = immediate
        self.stats = pstats.Stats(Profile())
        self.ncalls = 0
        self.skip = skip
        self.skipped = 0
        atexit.register(self.atexit)

    def __call__(self, *args, **kw):
        """Profile a singe call to the function."""
        self.ncalls += 1
        if self.skip > 0:
            self.skip -= 1
            self.skipped += 1
            return self.fn(*args, **kw)
        if FuncProfile.in_profiler:
            # handle recursive calls
            return self.fn(*args, **kw)
        # You cannot reuse the same profiler for many calls and accumulate
        # stats that way.  :-/
        profiler = Profile()
        try:
            FuncProfile.in_profiler = True
            return profiler.runcall(self.fn, *args, **kw)
        finally:
            FuncProfile.in_profiler = False
            self.stats.add(profiler)
            if self.immediate:
                self.print_stats()
                self.reset_stats()

    def print_stats(self):
        """Print profile information to sys.stdout."""
        funcname = self.fn.__name__
        filename = self.fn.__code__.co_filename
        lineno = self.fn.__code__.co_firstlineno
        print()
        print("*** PROFILER RESULTS ***")
        print("%s (%s:%s)" % (funcname, filename, lineno))
        print("function called %d times" % self.ncalls, end=' ')
        if self.skipped:
            print("(%d calls not profiled)" % self.skipped)
        else:
            print()
        print()
        stats = self.stats
        if self.filename:
            pickle.dump(stats, file(self.filename, 'w'))
        stats.strip_dirs()
        stats.sort_stats('cumulative', 'time', 'calls')
        stats.print_stats(40)

    def reset_stats(self):
        """Reset accumulated profiler statistics."""
        self.stats = pstats.Stats(Profile())
        self.ncalls = 0
        self.skipped = 0

    def atexit(self):
        """
        Stop profiling and print profile information to sys.stdout.

        This function is registered as an atexit hook.
        """
        if not self.immediate:
            self.print_stats()


class HotShotFuncProfile:
    """Profiler for a function (uses hotshot)."""

    # This flag is shared between all instances
    in_profiler = False

    def __init__(self, fn, skip=0, filename=None):
        """
        Creates a profiler for a function.

        Every profiler has its own log file (the name of which is derived from
        the function name).

        HotShotFuncProfile registers an atexit handler that prints profiling
        information to sys.stderr when the program terminates.

        The log file is not removed and remains there to clutter the current
        working directory.
        """
        self.fn = fn
        self.filename = filename
        if self.filename:
            self.logfilename = filename + ".raw"
        else:
            self.logfilename = fn.__name__ + ".prof"
        self.profiler = hotshot.Profile(self.logfilename)
        self.ncalls = 0
        self.skip = skip
        self.skipped = 0
        atexit.register(self.atexit)

    def __call__(self, *args, **kw):
        """Profile a singe call to the function."""
        self.ncalls += 1
        if self.skip > 0:
            self.skip -= 1
            self.skipped += 1
            return self.fn(*args, **kw)
        if HotShotFuncProfile.in_profiler:
            # handle recursive calls
            return self.fn(*args, **kw)
        try:
            HotShotFuncProfile.in_profiler = True
            return self.profiler.runcall(self.fn, *args, **kw)
        finally:
            HotShotFuncProfile.in_profiler = False

    def atexit(self):
        """
        Stop profiling and print profile information to sys.stderr.

        This function is registered as an atexit hook.
        """
        self.profiler.close()
        funcname = self.fn.__name__
        filename = self.fn.__code__.co_filename
        lineno = self.fn.__code__.co_firstlineno
        print()
        print("*** PROFILER RESULTS ***")
        print("%s (%s:%s)" % (funcname, filename, lineno))
        print("function called %d times" % self.ncalls, end=' ')
        if self.skipped:
            print("(%d calls not profiled)" % self.skipped)
        else:
            print()
        print()
        stats = hotshot.stats.load(self.logfilename)
        # hotshot.stats.load takes ages, and the .prof file eats megabytes, but
        # a pickled stats object is small and fast
        if self.filename:
            pickle.dump(stats, file(self.filename, 'w'))
        # it is best to pickle before strip_dirs
        stats.strip_dirs()
        stats.sort_stats('cumulative', 'time', 'calls')
        stats.print_stats(40)


class HotShotFuncCoverage:
    """
    Coverage analysis for a function (uses _hotshot).

    HotShot coverage is reportedly faster than trace.py, but it appears to
    have problems with exceptions; also line counts in coverage reports
    are generally lower from line counts produced by TraceFuncCoverage.
    Is this my bug, or is it a problem with _hotshot?
    """

    def __init__(self, fn):
        """
        Creates a profiler for a function.

        Every profiler has its own log file (the name of which is derived from
        the function name).

        HotShotFuncCoverage registers an atexit handler that prints profiling
        information to sys.stderr when the program terminates.

        The log file is not removed and remains there to clutter the current
        working directory.
        """
        self.fn = fn
        self.logfilename = fn.__name__ + ".cprof"
        self.profiler = _hotshot.coverage(self.logfilename)
        self.ncalls = 0
        atexit.register(self.atexit)

    def __call__(self, *args, **kw):
        """Profile a singe call to the function."""
        self.ncalls += 1
        return self.profiler.runcall(self.fn, args, kw)

    def atexit(self):
        """
        Stop profiling and print profile information to sys.stderr.

        This function is registered as an atexit hook.
        """
        self.profiler.close()
        funcname = self.fn.__name__
        filename = self.fn.__code__.co_filename
        lineno = self.fn.__code__.co_firstlineno
        print()
        print("*** COVERAGE RESULTS ***")
        print("%s (%s:%s)" % (funcname, filename, lineno))
        print("function called %d times" % self.ncalls)
        print()
        fs = FuncSource(self.fn)
        reader = hotshot.log.LogReader(self.logfilename)
        for what, (filename, lineno, funcname), tdelta in reader:
            if filename != fs.filename:
                continue
            if what == hotshot.log.LINE:
                fs.mark(lineno)
            if what == hotshot.log.ENTER:
                # hotshot gives us the line number of the function definition
                # and never gives us a LINE event for the first statement in
                # a function, so if we didn't perform this mapping, the first
                # statement would be marked as never executed
                if lineno == fs.firstlineno:
                    lineno = fs.firstcodelineno
                fs.mark(lineno)
        reader.close()
        print(fs)


class TraceFuncCoverage:
    """
    Coverage analysis for a function (uses trace module).

    HotShot coverage analysis is reportedly faster, but it appears to have
    problems with exceptions.
    """

    # Shared between all instances so that nested calls work
    tracer = trace.Trace(count=True, trace=False,
                         ignoredirs=[sys.prefix, sys.exec_prefix])

    # This flag is also shared between all instances
    tracing = False

    def __init__(self, fn):
        """
        Creates a profiler for a function.

        Every profiler has its own log file (the name of which is derived from
        the function name).

        TraceFuncCoverage registers an atexit handler that prints profiling
        information to sys.stderr when the program terminates.

        The log file is not removed and remains there to clutter the current
        working directory.
        """
        self.fn = fn
        self.logfilename = fn.__name__ + ".cprof"
        self.ncalls = 0
        atexit.register(self.atexit)

    def __call__(self, *args, **kw):
        """Profile a singe call to the function."""
        self.ncalls += 1
        if TraceFuncCoverage.tracing:
            return self.fn(*args, **kw)
        try:
            TraceFuncCoverage.tracing = True
            return self.tracer.runfunc(self.fn, *args, **kw)
        finally:
            TraceFuncCoverage.tracing = False

    def atexit(self):
        """
        Stop profiling and print profile information to sys.stderr.

        This function is registered as an atexit hook.
        """
        funcname = self.fn.__name__
        filename = self.fn.__code__.co_filename
        lineno = self.fn.__code__.co_firstlineno
        print()
        print("*** COVERAGE RESULTS ***")
        print("%s (%s:%s)" % (funcname, filename, lineno))
        print("function called %d times" % self.ncalls)
        print()
        fs = FuncSource(self.fn)
        for (filename, lineno), count in list(self.tracer.counts.items()):
            if filename != fs.filename:
                continue
            fs.mark(lineno, count)
        print(fs)
        never_executed = fs.count_never_executed()
        if never_executed:
            print("%d lines were not executed." % never_executed)


class FuncSource:
    """Source code annotator for a function."""

    blank_rx = re.compile(r"^\s*finally:\s*(#.*)?$")

    def __init__(self, fn):
        self.fn = fn
        self.filename = inspect.getsourcefile(fn)
        self.source, self.firstlineno = inspect.getsourcelines(fn)
        self.sourcelines = {}
        self.firstcodelineno = self.firstlineno
        self.find_source_lines()

    def find_source_lines(self):
        """Mark all executable source lines in fn as executed 0 times."""
        strs = trace.find_strings(self.filename)
        lines = trace.find_lines_from_code(self.fn.__code__, strs)
        self.firstcodelineno = sys.maxsize
        for lineno in lines:
            self.firstcodelineno = min(self.firstcodelineno, lineno)
            self.sourcelines.setdefault(lineno, 0)
        if self.firstcodelineno == sys.maxsize:
            self.firstcodelineno = self.firstlineno

    def mark(self, lineno, count=1):
        """
        Mark a given source line as executed count times.

        Multiple calls to mark for the same lineno add up.
        """
        self.sourcelines[lineno] = self.sourcelines.get(lineno, 0) + count

    def count_never_executed(self):
        """Count statements that were never executed."""
        lineno = self.firstlineno
        counter = 0
        for line in self.source:
            if self.sourcelines.get(lineno) == 0:
                if not self.blank_rx.match(line):
                    counter += 1
            lineno += 1
        return counter

    def __str__(self):
        """Return annotated source code for the function."""
        lines = []
        lineno = self.firstlineno
        for line in self.source:
            counter = self.sourcelines.get(lineno)
            if counter is None:
                prefix = ' ' * 7
            elif counter == 0:
                if self.blank_rx.match(line):
                    prefix = ' ' * 7
                else:
                    prefix = '>' * 6 + ' '
            else:
                prefix = '%5d: ' % counter
            lines.append(prefix + line)
            lineno += 1
        return ''.join(lines)


def timecall(fn):
    """
    Wrap `fn` and print its execution time.

    Example::

        @timecall
        def somefunc(x, y):
            time.sleep(x * y)

        somefunc(2, 3)

    will print

        somefunc: 6.0 seconds

    """
    def new_fn(*args, **kw):
        try:
            start = time.time()
            return fn(*args, **kw)
        finally:
            duration = time.time() - start
            funcname = fn.__name__
            filename = fn.__code__.co_filename
            lineno = fn.__code__.co_firstlineno
            print("\n  %s (%s:%s):\n    %.3f seconds\n" % (
                                        funcname, filename, lineno, duration), file=sys.stderr)
    new_fn.__doc__ = fn.__doc__
    return new_fn

