# -*- coding: utf-8 -*-
import reportlab.lib.units as units

def dictunion(lhs, rhs):
	""" Dictionary union

	>>> util.dictunion({1:'a'}, {2:'b'})
	{1: 'a', 2: 'b'}
	"""
	res = lhs.copy()
	res.update(rhs)
	return res


def getPt(val):
	"""Get numeric pt value from string value.

	Strings can have the unit appended, like "3.5 in", "2 cm", "3 pica", "10 mm".

	> print self.getPt("1 in")
	72
	> print self.getPt("1")
	1
	> print self.getPt(1)
	1
	"""
	if isinstance(val, (int, long, float)):
		# return as-is as the pt value.
		return val
	else:
		# try to run it through reportlab's units.toLength() function:
		return units.toLength(val)
