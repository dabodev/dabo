"""Clears the 'from dabo.dLocalize import *' lines from all python
files underneath the directory or directories you specify. If you
don't specify a directory, the current directory will be used.
"""

import os

def clear_localize_walk(arg, dirname, fnames):
	print "Processing directory %s..." % dirname
	for fname in fnames:
		if os.path.splitext(fname)[1] == ".py":
			print "Checking file %s..." % fname
			full_fname = os.path.join(dirname, fname)
			rlines = open(full_fname).readlines()
			wlines = []
			for idx, line in enumerate(rlines):
				lineno = idx + 1
				if "dLocalize" in line:
					print "--> Removing line %s, '%s'" % (lineno, line)
					continue
				wlines.append(line)
			open(full_fname, "wb").write(''.join(wlines))

def clear_localize(dirname):
	os.path.walk(dirname, clear_localize_walk, None)


if __name__ == "__main__":
	import sys

	dirs = sys.argv[1:]
	if not dirs:
		dirs = ["."]
	for dir in dirs:
		clear_localize(dir)

