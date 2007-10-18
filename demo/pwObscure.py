# -*- coding: utf-8 -*-
import sys
from dabo.lib.SimpleCrypt import SimpleCrypt

def usage():
	print """
Usage: 
	To obscure: python pwObscure.py <plain text password>
	To reveal: python pwObscure.py <obscured password> reveal

"""


if __name__ == "__main__":
	if len(sys.argv) < 2:
		usage()
		sys.exit()
	pw = sys.argv[1]
	cryp = SimpleCrypt()
	if len(sys.argv) > 2:
		if sys.argv[2].lower() != "reveal":
			usage()
			sys.exit()
		# Decrypt
		print """The decrypted value of '%s' is: %s
This is very simple security; you may want to provide more
powerful security for your data.""" % (pw, cryp.decrypt(pw))

	else:
		# Encrypt
		print """The encrypted value of '%s' is: %s
This is very simple security; you may want to provide more
powerful security for your data.""" % (pw, cryp.encrypt(pw))
		
