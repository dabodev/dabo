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
	txL = list(tx)
	txL.reverse()
	txR = ''.join(txL)
	return txR

