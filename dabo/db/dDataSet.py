# -*- coding: utf-8 -*-
import sys
import re
import operator
import datetime
import hashlib

from decimal import Decimal
try:
	from pysqlite2 import dbapi2 as sqlite
except ImportError:
	try:
		import sqlite3 as sqlite
	except ImportError:
		msg = """

Dabo requires SQLite 3 and the pysqlite2 module. You will have to install these
free products before running Dabo. You can get them from the following locations:

SQLite: http://www.sqlite.org/download.html
pysqlite2: http://initd.org/tracker/pysqlite

"""
		sys.exit(msg)

import dabo
from dabo.dLocalize import _
from dabo.lib.utils import ustr



class dDataSet(tuple):
	""" This class assumes that its contents are not ordinary tuples, but
	rather tuples consisting of dicts, where the dict keys are field names.
	This is the data structure returned by the dCursorMixin class.

	It is used to give these data sets the ability to be queried, joined, etc.
	This is accomplished by using SQLite in-memory databases. If SQLite
	and pysqlite2 are not installed on the machine this is run on, a
	warning message will be printed out and the SQL functions will return
	None. The data will still be usable, though.
	"""
	def __init__(self, sequence=None):
		# Note that as immutable objects, tuples are created with __new__,
		# so we must not pass the argument to the __init__ method of tuple.
		super(dDataSet, self).__init__()
		self._connection = None
		self._cursor = None
		self._bizobj = None
		self._populated = False
		self._typeStructure = {}
		# We may need to encode fields that are not legal names.
		self.fieldAliases = {}
		# Keep a hash value to tell if we need to re-populate
		self._dataHash = ""

		sqlite.register_adapter(Decimal, self._adapt_decimal)
		# When filtering datasets, we need a reference to the dataset
		# this dataset was derived from.
		self._sourceDataSet = None

		# Register the converters
		sqlite.register_converter("decimal", self._convert_decimal)

		self._typeDict = {int: "integer", long: "integer", str: "text",
				unicode: "text", float: "real", datetime.date: "date",
				datetime.datetime: "timestamp", Decimal: "decimal"}



	def __del__(self):
		if self._cursor is not None:
			self._cursor.close()
		if self._connection is not None:
			self._connection.close()


	def __add__(self, *args, **kwargs):
		return dDataSet(super(dDataSet, self).__add__(*args, **kwargs))


	def __mul__(self, *args, **kwargs):
		return dDataSet(super(dDataSet, self).__mul__(*args, **kwargs))


	@staticmethod
	def _adapt_decimal(decVal):
		"""Converts the decimal value to a string for storage"""
		return ustr(decVal)


	@staticmethod
	def _convert_decimal(strVal):
		"""This is a converter routine. Takes the string representation of a
		Decimal value and return an actual decimal.
		"""
		return Decimal(strVal)


	def _index(self, rec):
		"""Returns the index of the record object, or None."""
		for idx, item in enumerate(self):
			if item == rec:
				return idx
		return None


	def replace(self, field, valOrExpr, scope=None):
		"""Replaces the value of the specified field with the given expression.

		All records matching the scope are affected; if	no scope is specified,
		all records are affected.

		Scope is a boolean expression.
		"""
		if scope is not None:
			scope = self._fldReplace(scope, "rec")

		literal = True
		if isinstance(valOrExpr, basestring):
			if valOrExpr.strip()[0] == "=":
				literal = False
				valOrExpr = valOrExpr.replace("=", "", 1)
			valOrExpr = self._fldReplace(valOrExpr, "rec")
		if literal:
			upDict = {field: valOrExpr}
			if scope is None:
				[rec.update(upDict) for rec in self]
			else:
				[rec.update(upDict) for rec in self
						if eval(scope)]
		else:
			# Need to go record-by-record so that the expression evaluates correctly
			for rec in self:
				if eval(scope):
					rec[field] = eval(valOrExpr)


	def sort(self, col, ascdesc=None, caseSensitive=None):
		if ascdesc is None:
			ascdesc = "ASC"
		casecollate = ""
		if caseSensitive is False:
			# The default of None will be case-sensitive
			casecollate = " COLLATE NOCASE "
		stmnt = "select * from dataset order by %s %s %s"
		stmnt = stmnt % (col, casecollate, ascdesc)
		ret = self.execute(stmnt)
		# Sorting doesn't change the data, so preserve any source dataset.
		ret._sourceDataSet = self._sourceDataSet
		return ret


	def filter(self, fld, expr, op="="):
		"""This takes a field name, an expression, and an optional operator,
		and returns a dataset that is filtered on that field by that expression.
		If the operator is specified, it will be used literally in the evaluation
		instead of the equals sign, unless it is one of the following strings,
		which will be interpreted as indicated:
			eq, equals: =
			ne, nequals: !=
			gt: >
			gte: >=
			lt: <
			lte: <=
			startswith, beginswith: fld.startswith(expr)
			endswith: fld.endswith(expr)
			contains: expr in fld
		"""
		if not self:
			# No rows, so nothing to filter
			return self
		op = op.strip().lower()
		opDict = {"eq": operator.eq,
				"=": operator.eq,
				"equals": operator.eq,
				"ne": operator.ne,
				"!=": operator.ne,
				"nequals": operator.ne,
				"gt": operator.gt,
				">": operator.gt,
				"gte": operator.ge,
				">=": operator.ge,
				"lt": operator.lt,
				"<": operator.lt,
				"lte": operator.le,
				"<=": operator.le}
		try:
			fnc = opDict[op]
		except KeyError:
			fnc = None
		if fnc:
			filtered = [rec for rec in self if fnc(rec[fld], expr)]
		elif op in ("startswith", "beginswith"):
			filtered = [rec for rec in self if (rec[fld] or "").startswith(expr)]
		elif op == "endswith":
			filtered = [rec for rec in self if (rec[fld] or "").endswith(expr)]
		elif op == "contains":
			filtered = [rec for rec in self if expr in (rec[fld] or "")]
		ret = self.__class__(filtered)
		ret._sourceDataSet = self
		ret._filtered_fld = fld
		ret._filtered_expr = expr
		ret._filtered_op = op
		return ret


	def filterByExpression(self, expr):
		"""Allows you to filter by any valid Python expression."""
		if not self:
			# No rows, so nothing to filter
			return self
		stmnt = """ [rec for rec in self if %s] """ % self._fldReplace(expr, "rec")
		recs = eval(stmnt)
		ret = self.__class__(recs)
		ret._sourceDataSet = self
		return ret


	def removeFilter(self):
		"""Remove the most recently applied filter."""
		ret = self
		if ret._sourceDataSet:
			ret = ret._sourceDataSet
		return ret


	def removeFilters(self):
		"""Remove all applied filters, going back to the original data set."""
		ret = self
		while ret._sourceDataSet:
			ret = ret._sourceDataSet
		return ret


	def _fldReplace(self, expr, dictName=None):
		"""The list comprehensions require the field names be the keys
		in a dictionary expression. Users, though, should not have to know
		about this. This takes a user-defined, SQL-like expressions, and
		substitutes any field name with the corresponding dict
		expression. If no dictName is supplied, the name 'rec' will be used,
		for the typical list comprehension of :
			[rec for rec in self where ...]
		Examples (assuming 'price' is a column in the data):
			self._fldReplace("price > 50")
				=> returns "rec['price'] > 50"
			self._fldReplace("price > 50", "foo")
				=> returns "foo['price'] > 50"
		"""
		patTemplate = r"\b%s\b"
		ret = expr
		if dictName is None:
			dictName = "rec"
		for kk in self[0]:
			pat = patTemplate % kk
			replacement = "%s['%s']" % (dictName, kk)
			ret = re.sub(pat, replacement, ret)
		return ret


	def _makeCreateTable(self, ds, alias=None):
		"""Makes the CREATE TABLE string needed to represent
		this data set. There must be at least one record in the
		data set, or we can't get the necessary column info. Optional, can use
		TypeStructure property to give data type hint to CREATE TABLE process.
		TypeStructure is a dictionary of form:
		{"fld_name":"field_type"} where field_type is the same as that in
		DataStructure. Ex: field_type "I" equals integer, "B" boolean,etc.
		"""
		if len(ds) == 0:
			return None
		if alias is None:
			# Use the default
			alias = "dataset"
		rec = ds[0]
		retList = []

		for key in rec:
			if key.startswith("dabo-"):
				# This is an internal field
				safekey = key.replace("-", "_")
				self.fieldAliases[safekey] = key
			else:
				safekey = key
			try:
				typ = dabo.db.getPythonType(self._typeStructure[key][0])
			except KeyError:
				typ = type(rec[key])
			try:
				retList.append("%s %s" % (safekey, ds._typeDict[typ]))
			except KeyError:
				retList.append(safekey)
		return "create table %s (%s)" % (alias, ", ".join(retList))


	def _populate(self, ds, alias=None):
		"""This is the method that converts a Python dataset
		into a SQLite table with the name specified by 'alias'.
		"""
		if alias is None:
			# Use the default
			alias = "dataset"
		if len(ds) == 0:
			# Can't create and populate a table without a structure
			dabo.log.info(_("Cannot populate without data for alias '%s'")
					% alias)
			return None
		hs = hashlib.md5(ustr(ds)).hexdigest()
		if hs == ds._dataHash:
			# Data's already there and hasn't changed; no need to re-load it
			return
		ds._dataHash = hs
		if ds._populated:
			# Clear out the old records
			self._cursor.execute("delete from %s" % alias)
		else:
			# Create the table
			self._cursor.execute(self._makeCreateTable(ds, alias))

		# Fields may contain illegal names. This will correct them
		flds = [fld.replace("dabo-", "dabo_") for fld in ds[0]]
		fldParams = [":%s" % fld for fld in flds]
		insStmnt = "insert into %s (%s) values (%s)" % (alias,
				", ".join(flds), ", ".join(fldParams))

		def recGenerator(ds):
			for rec in ds:
				yield rec

		self._cursor.executemany(insStmnt, recGenerator(ds))
		if ds is self:
			self._populated = True


	def execute(self, sqlExpr, params=(), cursorDict=None):
		"""This method allows you to work with a Python data set
		(i.e., a tuple of dictionaries) as if it were a SQL database. You
		can run any sort of statement that you can in a normal SQL
		database. It requires that SQLite and pysqlite2 are installed;
		if they aren't, this will return None.

		The SQL expression can be any standard SQL expression; however,
		the FROM clause should always be: 'from dataset', since these
		datasets do not have table names.

		If you want to do multi-dataset joins, you need to pass the
		additional DataSet objects in a dictionary, where the value is the
		DataSet, and the key is the alias used to reference that DataSet
		in your join statement.
		"""
		def dict_factory(cursor, row):
			dd = {}
			for idx, col in enumerate(cursor.description):
				dd[col[0]] = row[idx]
			return dd

		class DictCursor(sqlite.Cursor):
			def __init__(self, *args, **kwargs):
				sqlite.Cursor.__init__(self, *args, **kwargs)
				self.row_factory = dict_factory

		if self._connection is None:
			self._connection = sqlite.connect(":memory:",
					detect_types=(sqlite.PARSE_DECLTYPES | sqlite.PARSE_COLNAMES),
					isolation_level="EXCLUSIVE")
			if not hasattr(self, "_encoding"):
				self._encoding = self._connection.execute("PRAGMA encoding"). \
						fetchone()[0].lower()
			self._connection.text_factory = str
		if self._cursor is None:
			self._cursor = self._connection.cursor(factory=DictCursor)

# 		import time
# 		st = time.clock()
# 		print "starting"

		# Create the table for this dDataSet
		self._populate(self, "dataset")
		if not self._populated:
			# No data in the dataset
			return None

# 		pt = time.clock()
# 		print "POPULATED", pt-st
		# Now create any of the tables for the join dDataSets
		if cursorDict is not None:
			for alias, ds in cursorDict.items():
				self._populate(ds, alias)

		# We have a table now with the necessary data. Run the query!
		if params and not isinstance(params, tuple):
			params = (params,)
		self._cursor.execute(sqlExpr, params)

# 		et = time.clock()
# 		print "EXECUTED", et - pt
		# We need to know what sort of statement was run. Only a 'select'
		# will return results. The rest ('update', 'delete', 'insert') return
		# nothing. In those cases, we need to run a 'select *' to get the
		# modified data set.
		if not sqlExpr.lower().strip().startswith("select "):
			self._cursor.execute("select * from dataset")
		tmpres = self._cursor.fetchall()

# 		ft = time.clock()
# 		print "FETCH", ft-et
		return dDataSet(tmpres)

# 		res = []
# 		if tmpres:
# 			# There will be no description if there are no records.
# 			dscrp = [fld[0] for fld in self._cursor.description]
# 			for tmprec in tmpres:
# 				rec = {}
# 				for pos, val in enumerate(tmprec):
# 					fld = dscrp[pos]
# 					if self.fieldAliases.has_key(fld):
# 						fld = self.fieldAliases[fld]
# 					rec[fld] = val
# 				res.append(rec)
#
# 		dt = time.clock()
# 		print "CONVERTED", dt-ft


	def _getBizobj(self):
		return self._bizobj

	def _setBizobj(self, val):
		self._bizobj = val


	def _getCursor(self):
		return self._cursor

	def _setCursor(self, val):
		self._cursor = val


	def _getEncoding(self):
		try:
			return self._encoding
		except AttributeError:
			self._encoding = dabo.getEncoding()
			return self._encoding

	def _setEncoding(self, encoding):
		self._encoding = encoding


	def _getUnfilteredDataSet(self):
		ret = self
		while ret._sourceDataSet:
			ret = ret._sourceDataSet
		return ret

	def _getTypeStructure(self):
		return self._typeStructure

	def _setTypeStructure(self, val):
		self._typeStructure = val


	Bizobj = property(_getBizobj, _setBizobj, None,
			_("Reference to the bizobj that 'owns' this data set. Default=None  (bizobj)"))

	Cursor = property(_getCursor, _setCursor, None,
			_("Reference to the bizobj that 'owns' this data set. Default=None  (dCursorMixin)"))

	Encoding = property(_getEncoding, _setEncoding, None,
			_("The encoding used for data in the dataset.  (str)"))

	UnfilteredDataSet = property(_getUnfilteredDataSet, None, None,
			_("""If filters have been applied, returns the unfiltered dataset that would be returned if removeFilters() had been called. If no filters have been applied, returns self  (dDataSet)"""))

	TypeStructure = property(_getTypeStructure, _setTypeStructure, None,
			_("""An optional helper dictionary matching field names to dabo data types."""))



# class DataSetOld(tuple):
# 	""" This class assumes that its contents are not ordinary tuples, but
# 	rather tuples consisting of dicts, where the dict keys are field names.
# 	This is the data structure returned by the dCursorMixin class.
# 	"""
# 	# List comprehensions used in this class require a non-conflicting
# 	# name. This is unlikely to be used anywhere else.
# 	_dictSubName = "_dataSet_rec"
#
#
# 	def _fldReplace(self, expr, dictName=None):
# 		"""The list comprehensions require the field names be the keys
# 		in a dictionary expression. Users, though, should not have to know
# 		about this. This takes a user-defined, SQL-like expressions, and
# 		substitutes any field name with the corresponding dict
# 		expression.
# 		"""
# 		keys = self[0].keys()
# 		patTemplate = "(.*\\b)%s(\\b.*)"
# 		ret = expr
# 		if dictName is None:
# 			dictName = self._dictSubName
# 		for kk in keys:
# 			pat = patTemplate % kk
# 			mtch = re.match(pat, ret)
# 			if mtch:
# 				ret = mtch.groups()[0] + "%s['%s']" % (dictName, kk) + mtch.groups()[1]
# 		return ret
#
#
# 	def processFields(self, fields, aliasDict):
# 		if isinstance(fields, basestring):
# 			fields = fields.split(",")
# 		for num, fld in enumerate(fields):
# 			fld = fld.replace(" AS ", " as ").replace(" As ", " as ").strip()
# 			fa = fld.split(" as ")
# 			if len(fa) > 1:
# 				# An alias is specified
# 				fld = fa[0].strip()
# 				aliasDict[fld] = fa[1].strip()
# 			fields[num] = fld
# 		return fields, aliasDict
#
#
# 	def select(self, fields=None, where=None, orderBy=None):
# 		fldList = []
# 		fldAliases = {}
# 		whereList = []
# 		orderByList = []
# 		keys = self[0].keys()
# 		if fields is None or fields == "*":
# 			# All fields
# 			fields = keys
# 		fields, fldAliases = self.processFields(fields, fldAliases)
# 		for fld in fields:
# 			fldList.append("'%s' : %s" % (fld, self._fldReplace(fld)))
# 		fieldsToReturn = ", ".join(fldList)
# 		fieldsToReturn = "{%s}" % fieldsToReturn
#
# 		# Where list elements
# 		if where is None:
# 			whereClause = ""
# 		else:
# 			if isinstance(where, basestring):
# 				where = [where]
# 			for wh in where:
# 				whereList.append(self._fldReplace(wh))
# 			whereClause = " and ".join(whereList)
# 		if whereClause:
# 			whereClause = " if %s" % whereClause
# 		stmnt = "[%s for %s in self %s]" % (fieldsToReturn, self._dictSubName, whereClause)
# 		resultSet = eval(stmnt)
#
# 		if fldAliases:
# 			# We need to replace the keys for the field names with the
# 			# appropriate alias names
# 			for rec in resultSet:
# 				for key, val in fldAliases.items():
# 					orig = rec.get(key)
# 					if orig:
# 						rec[val] = orig
# 						del rec[key]
#
# 		if orderBy:
# 			# This should be a comma separated string in the format:
# 			#		fld1, fld2 desc, fld3 asc
# 			# After the field name is an optional direction, either 'asc'
# 			# (ascending, default) or 'desc' (descending).
# 			# IMPORTANT! Fields referenced in 'orderBy' MUST be in
# 			# the result data set!
# 			orderByList = orderBy.split(",")
# 			sortList = []
#
# 			def orderBySort(val1, val2):
# 				ret = 0
# 				compList = orderByList[:]
# 				while not ret:
# 					comp = compList[0]
# 					compList = compList[1:]
# 					if comp[-4:].lower() == "desc":
# 						compVals = (-1, 1)
# 					else:
# 						compVals = (1, -1)
# 					# Remove the direction, if any, from the comparison.
# 					compWords = comp.split(" ")
# 					if compWords[-1].lower() in ("asc", "desc"):
# 						compWords = compWords[:-1]
# 					comp = " ".join(compWords)
# 					cmp1 = self._fldReplace(comp, "val1")
# 					cmp2 = self._fldReplace(comp, "val2")
# 					eval1 = eval(cmp1)
# 					eval2 = eval(cmp2)
# 					if eval1 > eval2:
# 						ret = compVals[0]
# 					elif eval1 < eval2:
# 						ret = compVals[1]
# 					else:
# 						# They are equal. Continue comparing using the
# 						# remaining terms in compList, if any.
# 						if not compList:
# 							break
# 				return ret
#
# 			resultSet.sort(orderBySort)
#
# 		return DataSet(resultSet)
#
#
# 	def join(self, target, sourceAlias, targetAlias, condition,
# 			sourceFields=None, targetFields=None, where=None,
# 			orderBy=None, joinType=None):
# 		"""This method joins the current DataSet and the target
# 		DataSet, based on the specified condition. The 'joinType'
# 		parameter will determine the type of join (inner, left, right, full).
# 		Where and orderBy will affect the result of the join, and so they
# 		should reference fields in the result set without alias qualifiers.
# 		"""
# 		if joinType is None:
# 			joinType = "inner"
# 		joinType = joinType.lower().strip()
# 		if joinType == "outer":
# 			# This is the same as 'left outer'
# 			joinType = "left"
# 		if "outer" in joinType.split():
# 			tmp = joinType.split()
# 			tmp.remove("outer")
# 			joinType = tmp[0]
#
# 		leftDS = self
# 		rightDS = target
# 		leftAlias = sourceAlias
# 		rightAlias = targetAlias
# 		leftFields = sourceFields
# 		rightFields = targetFields
# 		leftFldAliases = {}
# 		rightFldAliases = {}
# 		if joinType == "right":
# 			# Same as left; we just need to reverse things
# 			(leftDS, rightDS, leftAlias, rightAlias, leftFields,
# 					rightFields) = (rightDS, leftDS, rightAlias, leftAlias,
# 					rightFields, leftFields)
#
#
# 		leftFields, leftFldAliases = self.processFields(leftFields, leftFldAliases)
# 		rightFields, rightFldAliases = self.processFields(rightFields, rightFldAliases)
#
# 		# Parse the condition. It should have an '==' in it. If not,
# 		# raise an error.
# 		condList = condition.split("==")
# 		if len(condList) == 1:
# 			# No equality specified
# 			errMsg = _("Bad join: no '==' in join condition: %s") % condition
# 			raise dException.QueryException(errMsg)
#
# 		leftCond = None
# 		rightCond = None
# 		leftPat = "(.*)(\\b%s\\b)(.*)" % leftAlias
# 		rightPat = "(.*)(\\b%s\\b)(.*)" % rightAlias
#
# 		mtch = re.match(leftPat, condList[0])
# 		if mtch:
# 			leftCond = condList[0].strip()
# 		else:
# 			mtch = re.match(leftPat, condList[1])
# 			if mtch:
# 				leftCond = condList[1].strip()
# 		mtch = re.match(rightPat, condList[0])
# 		if mtch:
# 			rightCond = condList[0].strip()
# 		else:
# 			mtch = re.match(rightPat, condList[1])
# 			if mtch:
# 				rightCond = condList[1].strip()
# 		condError = ""
# 		if leftCond is None:
# 			condError += _("No join condition specified for alias '%s'") % leftAlias
# 		if rightCond is None:
# 			if condError:
# 				condError += "; "
# 			condError += _("No join condition specified for alias '%s'") % rightAlias
# 		if condError:
# 			raise dException.QueryException(condError)
#
# 		# OK, we now know how to do the join. The plan is this:
# 		# 	create an empty result list
# 		# 	scan through all the left records
# 		# 		if leftFields, run a select to get only those fields.
# 		# 		find all the matching right records using select
# 		# 		if matches, update each with the left select and add
# 		# 				to the result.
# 		# 		if no matches:
# 		# 			if inner join:
# 		# 				skip to next
# 		# 			else:
# 		# 				get dict.fromkeys() for right select
# 		# 				update left with fromkeys and add to result
# 		#
# 		# 	We'll worry about full joins later.
#
# 		resultSet = []
# 		for leftRec in leftDS:
# 			if leftFields:
# 				leftSelect = DataSet([leftRec]).select(fields=leftFields)[0]
# 			else:
# 				leftSelect = leftRec
# 			tmpLeftCond = leftCond.replace(leftAlias, "leftRec")
# 			tmpLeftCond = "%s['%s']" % tuple(tmpLeftCond.split("."))
# 			leftVal = eval(tmpLeftCond)
#
# 			if isinstance(leftVal, basestring):
# 				leftVal = "'%s'" % leftVal
# 			rightWhere = rightCond.replace(rightAlias + ".", "") + "== %s" % leftVal
# 			rightRecs = rightDS.select(fields=rightFields, where=rightWhere)
#
# 			if rightRecs:
# 				for rightRec in rightRecs:
# 					rightRec.update(leftSelect)
# 					resultSet.append(rightRec)
# 			else:
# 				if not joinType == "inner":
# 					rightKeys = rightDS.select(fields=rightFields)[0].keys()
# 					leftSelect.update(dict.fromkeys(rightKeys))
# 					resultSet.append(leftSelect)
#
# 		resultSet = DataSet(resultSet)
# 		if where or orderBy:
# 			resultSet = resultSet.select(where=where, orderBy=orderBy)
# 		return resultSet


if __name__ == "__main__":
	data = [{"name" : "Ed Leafe", "age" : 51, "coder" :  True, "color": "brown"},
				{"name" : "Mike Leafe", "age" : 21, "coder" :  False, "color": "purple"},
				{"name" : "Dan Leafe", "age" : 17, "coder" :  False, "color": "green"},
				{"name" : "Paul McNett", "age" : 39, "coder" :  True, "color": "red"}]
	ds = dDataSet(data)

	newDS = ds.execute("select name, age from dataset where age > 30")
	print "Over 30:"
	for rec in newDS:
		print "\tName: %(name)s, Age: %(age)s" % rec

	emptyDS = ds.filter("age", 99, "gt")
	if not emptyDS:
		print "No one is over 99 years old"
	else:
		print "There are %s people over 99 years old" % len(emptyDS)
	filt = emptyDS.filter("foo", "bar")

	leafeDS = ds.filter("name", "Leafe", "endswith")
	if not leafeDS:
		print "No one is is named 'Leafe'"
	else:
		print "There are %s people named 'Leafe'" % len(leafeDS)
	orig = leafeDS.removeFilters()
	print "The original dataset has %s records." % len(orig)

