class CaselessDict(dict):
	"""This is a normal Python dictionary that operates in a case-insensitive way."""
	def __init__(self, *args, **kwargs):
		super(CaselessDict, self).__init__(*args, **kwargs)
		self._originalCase = {}

	def __setitem__(self, key, val):
		dict.__setitem__(self, key.lower(), val)
		self._originalCase[key.lower()] = key

	def __getitem__(self, key):
		return dict.__getitem__(self, key.lower())

	def __delitem__(self, key):
		dict.__delitem__(self, key)
		del(self._originalCase[key.lower()])

	def __contains__(self, key):
		return dict.__contains__(self, key.lower())

	def __str__(self):
		ret = "{"
		for v in self._originalCase.values():
			if len(ret) > 1:
				ret += ", "
			ret += "%s: %s" % (repr(v), repr(self[v]))
		ret += "}"
		return ret

	def __repr__(self):
		return self.__str__()

	def keys(self):
		return self._originalCase.values()

	def items(self):
		r = []
		for v in self._originalCase.values():
			r.append((v, self[v]))
		return r

if __name__ == "__main__":
	d = CaselessDict()
	d["PaulMcNett"] = 35
	d["Bananas"] = 42
	print d.keys()
	print d.items()
	print d["PAULMCNETT"]
	print d
