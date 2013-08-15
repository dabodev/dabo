# -*- coding: utf-8 -*-
import random
import string
import warnings
import base64
import dabo


class SimpleCrypt(object):
	""" Provides basic encryption for Dabo. Perhaps a better term would
	be 'obscure' rather than 'encrypt', since the latter implies strong
	security. Since this class is provided to all Dabo users, anyone with
	a copy of Dabo can decrypt your encrypted values.

	You can make your application more secure by making sure that the
	PyCrypto package is installed, and then setting the application's
	'CryptoKey' property to a string that is not publicly discoverable. This
	will provide security as strong as the secrecy of this key.

	For real-world applications, you should provide your own security
	class, and then set the Application's 'Crypto' property to an instance
	of that class. That class must provide the following interface:

		encrypt(val)
		decrypt(val)

	Thanks to Raymond Hettinger for the default (non-DES) code, originally found on
	http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/266586
	"""
	def __init__(self, key=None):
		super(SimpleCrypt, self).__init__()
		if callable(key):
			# Providing a callable is probably more secure than storing the key
			# directly in your code
			self.__key = key()
		else:
			self.__key = key
		self._cryptoProvider = None
		# If the Crypto package is available, use it.
		self._useDES3 = (self.__key is not None)
		if self._useDES3:
			try:
				from Crypto.Cipher import DES3
				from Crypto import Random
			except ImportError:
				self._useDES3 = False
		if self._useDES3:
			self.__key = self.__key[:16].rjust(16, "@")
			self._cryptoProvider = DES3.new(
					self.__key, DES3.MODE_CBC, Random.new().read(DES3.block_size))


	def showWarning(self):
		warnings.warn("WARNING: SimpleCrypt is not secure. Please see http://wiki.dabodev.com/SimpleCrypt for more information")


	def encrypt(self, aString):
		if not aString:
			return ""
		if self._useDES3:
			# Strings must have an introductory 8 byte string
			initialPad = "".join(random.sample(string.printable, 8))
			# Strings must be multiples of 8 bytes
			strLen = len(aString)
			diffToEight = 8 - (strLen % 8)
			pad = "@" * diffToEight
			paddedText = "%s%s%s" % (initialPad, pad, aString)
			enc = self._cryptoProvider.encrypt(paddedText)
			retText = "%s%s" % (diffToEight, enc)
			return base64.b64encode(retText)
		else:
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
		if self._useDES3:
			try:
				decString = base64.b64decode(aString)
			except TypeError:
				return ""
			# We need to chop off any padding, along with the first 8 garbage bytes
			padlen = int(decString[0]) + 8
			decString = decString[1:]
			ret = self._cryptoProvider.decrypt(decString)
			return ret[padlen:]
		else:
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

