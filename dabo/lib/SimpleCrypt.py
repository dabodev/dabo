# -*- coding: utf-8 -*-
import random

class SimpleCrypt(object):
	""" Provides basic encryption for Dabo. Perhaps a better term would
	be 'obscure' rather than 'encrypt', since the latter implies strong 
	security. Since this class is provided to all Dabo users, anyone with
	a copy of Dabo can decrypt your encrypted values.
	
	For real-world applications, you should provide your own security
	class, and then set the Application's 'Crypto' property to an instance
	of that class. That class must provide the following interface:
	
		encrypt(val)
		decrypt(val)
	
	Thanks to Raymond Hettinger for this code, originally found on
	http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/266586
	"""

	def showWarning(self):
		import warnings
		warnings.warn("""
WARNING: 
Your application uses SimpleCrypt, which is fine for testing but should
not be used in production, because:

1) Anyone with a copy of Dabo could decrypt your password.

2) It isn't portable between 32-bit and 64-bit python. See the trac
   ticket at http://trac.dabodev.com/ticket/1179 for more information.
""", UserWarning)

	def encrypt(self, aString):
		self.showWarning()
		tmpKey = self.generateKey(aString)
		myRand = random.Random(tmpKey).randrange
		crypted = [chr(ord(elem)^myRand(256)) for elem in aString]
		hex = self.strToHex("".join(crypted))
		ret = "".join([tmpKey[i/2]  + hex[i:i+2] for i in range(0, len(hex), 2)])
		return ret
		

	def decrypt(self, aString):
		self.showWarning()
		tmpKey = "".join([aString[i] for i in range(0, len(aString), 3)])
		val = "".join([aString[i+1:i+3] for i in range(0, len(aString), 3)])
		myRand = random.Random(tmpKey).randrange
		out = self.hexToStr(val)
		decrypted = [chr(ord(elem)^myRand(256)) for elem in out]
		return "".join(decrypted)
		
		
	def generateKey(self, s):
		chars = []
		for i in range(len(s)):
			chars.append(chr(65 + random.randrange(26)))
		return "".join(chars)
		

	def strToHex(self, aString):
		hexlist = ["%02X" % ord(x) for x in aString]
		return ''.join(hexlist)
	
	def hexToStr(self, aString):
		# Break the string into 2-character chunks
		try:
			chunks = [chr(int(aString[i] + aString[i+1], 16)) 
					for i in range(0, len(aString), 2)]
		except IndexError:
			raise ValueError(_("Incorrectly-encrypted password"))
		return "".join(chunks)

