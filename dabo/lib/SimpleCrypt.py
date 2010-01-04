# -*- coding: utf-8 -*-
import random
import warnings
import base64
import dabo


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
	
	Thanks to Raymond Hettinger for the default (non-DES) code, originally found on
	http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/266586
	"""
	def __init__(self):
		super(SimpleCrypt, self).__init__()
		self._cryptoProvider = None
		# If the Crypto package is available, use it.
		useDES = True
		try:
			from Crypto.Cipher import DES
		except ImportError:
			useDES = False
		try:
			ckey = dabo.cryptoKeyDES[:8].rjust(8, "@")
		except TypeError:
			dabo.errorLog.write("The 'cryptoKey' value has not been configured in dabo")
			useDES = False
		if useDES:
				self._cryptoProvider = DES.new(ckey, DES.MODE_ECB)
			

	def showWarning(self):
		warnings.warn("WARNING: SimpleCrypt is not secure. Please see http://wiki.dabodev.com/SimpleCrypt for more information")


	def encrypt(self, aString):
		if not aString:
			return ""
		try:
			# If we are not using 
			encMethod = self._cryptoProvider.encrypt
			# Strings must be multiples of 8 in length
			padlen = 0
			pad = ""
			diffToEight = len(aString) % 8
			if diffToEight:
				padlen = 8 - diffToEight
				pad = "@" * padlen
			padVal = "%s%s" % (aString, pad)
			ret = "%s%s" % (padlen, encMethod(padVal))
			ret = base64.b64encode(ret)
			return ret
		except AttributeError:
			self.showWarning()
			tmpKey = self.generateKey(aString)
			myRand = random.Random(tmpKey).randrange
			crypted = [chr(ord(elem)^myRand(256)) for elem in aString]
			hex = self.strToHex("".join(crypted))
			ret = "".join([tmpKey[i/2]  + hex[i:i+2] for i in range(0, len(hex), 2)])
			return ret
		

	def decrypt(self, aString):
		if not aString:
			return ""
		try:
			decryptMethod = self._cryptoProvider.decrypt
			decString = base64.b64decode(aString)
			padlen = int(decString[0])
			encval = decString[1:]
			ret = decryptMethod(encval)
			if padlen:
				ret = ret[:-padlen]
			return ret
		except (ValueError, AttributeError):
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

