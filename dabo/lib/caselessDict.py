class CaselessDict(dict):
	"""This is a normal Python dictionary that operates in a case-insensitive way."""

	def _getOriginalCase(self):
		if not hasattr(self, "_originalCase"):
			self._originalCase = {}
		return self._originalCase
		
	_OriginalCase = property(_getOriginalCase)

	def __init__(self, *args, **kwargs):
		self._originalCase = {}
		super(CaselessDict, self).__init__(*args, **kwargs)

	def __setitem__(self, key, val):
		dict.__setitem__(self, key.lower(), val)
		self._OriginalCase[key.lower()] = key

	def __getitem__(self, key):
		return dict.__getitem__(self, key.lower())

	def __delitem__(self, key):
		dict.__delitem__(self, key)
		del(self._OriginalCase[key.lower()])

	def __contains__(self, key):
		return dict.__contains__(self, key.lower())

	def __str__(self):
		ret = "{"
		for v in self._OriginalCase.values():
			if len(ret) > 1:
				ret += ", "
			ret += "%s: %s" % (repr(v), repr(self[v]))
		ret += "}"
		return ret

	def __repr__(self):
		return self.__str__()

	def clear(self):
		dict.clear(self)
		self._OriginalCase.clear()

	def keys(self):
		return self._OriginalCase.values()

	def items(self):
		r = []
		for v in self._OriginalCase.values():
			r.append((v, self[v]))
		return r

	def has_key(self, key):
		return dict.has_key(self, key.lower())

	def get(self, key, default=None):
		if self.has_key(key):
			return self.__getitem__(key)
		return default

	def setdefault(self, key, default=None):
		if not self.has_key(key):
			self.__setitem__(key, default)
		return self.__getitem__(key)


if __name__ == "__main__":
	d = CaselessDict()
	d["PaulMcNett"] = 35
	d["Bananas"] = 42
	print d.keys()
	print d.items()
	print d["PAULMCNETT"]
	print d.has_key("pAULmCNETT")
	print d.has_key("pAULmCNETTy")
	print d
