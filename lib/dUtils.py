# This serves as a catch-all script for common utilities that may be used
# in lots of places throughout Dabo. Typically, to use a function 'foo()' in
# this file, add the following import statement to your script:
#
#	import dabo.lib.dUtils as dUtils
# 
# Then, in your code, simply call:
#
#	dUtils.foo()

def reverseText(tx):
	"""Takes a string and returns it reversed. Example:
	
	dUtils.reverseText("Wow, this is so cool!")
		=> returns "!looc os si siht ,woW"
	"""
	return tx[::-1]


def padl(txt, lngth, fill=" "):
	"""Left pads the given string to the given length."""
	txt = str(txt)[:lngth]
	return (fill * (lngth-len(txt)) ) + txt
		

def padr(txt, lngth, fill=" "):
	"""Right pads the given string to the given length."""
	txt = str(txt)[:lngth]
	return txt + (fill * (lngth-len(txt)) )
		

def padc(txt, lngth, fill=" "):
	""" Return string of the specified length, padded with the
	specified fill character equally on the left and right (center
	the string). Default fill character	is space.
	"""
	txt = str(txt)[:lngth]
	# If the difference is odd, the extra character goes on the right
	diff = lngth - len(txt)
	dl = int( diff / 2)
	dr = diff - dl
	
	print "DIFF", diff, dl, dr
	
	return (fill * dl) + txt[:lngth] + (fill * dr)

