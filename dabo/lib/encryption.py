# -*- coding: utf-8 -*-
import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .. import settings
from ..base_object import dObject


class Encryption(dObject):
    """
    A wrapper around the `cryptography` library to enable secure encryption and decryption of
    sensitive values.

    Your application will need to supply a password, and an optional salt value. It will work
    without a salt, but it will be less secure. If you are unfamiliar with salts in cryptography,
    this is a good introduction: https://en.wikipedia.org/wiki/Salt_%28cryptography%29

    It is very important to not store neither your password nor salt in your code. Instead, create a
    function in your code that will retrieve it from a local file that is *NOT* included in your
    project. This way you can use public sites like Github or Gitlab without anyone being able to
    discover your secret values.

    The Application object will wrap these methods, so you never need to create a separate instance
    of this class. Instead, make calls through the app object:

        self.Application.CryptoKey = get_my_secure_credentials()
        encrypted_val = self.Application.encrypt(val)
        decrypted_val = self.Application.decrypt(encrypted_val)

    """

    def beforeInit(self):
        self.encoding = settings.getEncoding()
        self.key_cache = {}
        self.__password = self.__salt = b""
        self.__key = b""

    def set_key(self, key):
        keyvals = key() if callable(key) else key
        if isinstance(keyvals, (list, tuple)):
            self.__password, self.__salt = keyvals
        else:
            # Some tools, like the preference manager, use local DBs with no password
            self.__password = keyvals or "default"
            self.__salt = b"\xc6\x15\xb2Y\x974\x81\x9d\x82\xb5S\xd6\x84\x00y4"
        # Invalidate any previously computed key
        self.__key = b""
        self._set_encoded()

    def _set_encoded(self):
        """Ensure that the password and salt are bytes, not str"""
        if isinstance(self.__password, str):
            self.__password = self.__password.encode(self.encoding)
        if isinstance(self.__salt, str):
            self.__salt = self.__salt.encode(self.encoding)
        if isinstance(self.__key, str):
            self.__key = self.__key.encode(self.encoding)

    def _get_key(self):
        cache_key = (self.__password, self.__salt)
        cached = self.key_cache.get(cache_key)
        if not cached:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self.__salt,
                iterations=1_000_000,
            )
            cached = base64.urlsafe_b64encode(kdf.derive(self.__password))
            self.key_cache[cache_key] = cached
        return cached

    def encrypt(self, val):
        if not val:
            return ""
        self.__key = self.__key or self._get_key()
        val = val.encode(self.encoding) if isinstance(val, str) else val
        f = Fernet(self.__key)
        token = f.encrypt(val)
        return token.decode(self.encoding)

    def decrypt(self, token):
        if not token:
            return ""
        self.__key = self.__key or self._get_key()
        token = token.encode(self.encoding) if isinstance(token, str) else token
        f = Fernet(self.__key)
        val = f.decrypt(token)
        return val.decode(self.encoding)

    def strToHex(self, val):
        hexlist = ["%02X" % ord(x) for x in val]
        return "".join(hexlist)

    def hexToStr(self, val):
        # Break the string into 2-character chunks
        try:
            chunks = [chr(int(val[i] + val[i + 1], 16)) for i in range(0, len(val), 2)]
        except IndexError:
            raise ValueError(_("Incorrectly-encrypted password"))
        return "".join(chunks)
