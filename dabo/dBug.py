# -*- coding: utf-8 -*-
import inspect
from cStringIO import StringIO

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
		output.write(str(msg) + "\n")
	
	stackSection = stack[-1*levels:]
	for stackLine in stackSection:
		frame, filename, line, funcname, lines, unknown = stackLine
		if filename.endswith("/unittest.py"):
			# unittest.py code is a boring part of the traceback
			continue
		if filename.startswith("./"):
			filename = filename[2:]
		output.write("%s:%s in %s:\n" % (filename, line, funcname))
		if lines:
			output.write("	%s\n" % "".join(lines)[:-1])
	s = output.getvalue()
	# I actually logged the result, but you could also print it:
	return s
