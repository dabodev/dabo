# -*- coding: utf-8 -*-

import re
import dabo
from dBackend import dBackend
from dabo.lib.utils import ustr



class Firebird(dBackend):
	"""Class providing Firebird connectivity. Uses kinterbasdb."""

	# Firebird treats quotes names differently than unquoted names. This
	# will turn off the effect of automatically quoting all entities in Firebird;
	# if you need quotes for spaces and bad names, you'll have to supply
	# them yourself.
	nameEnclosureChar = ""

	def __init__(self):
		dBackend.__init__(self)
		self.dbModuleName = "kinterbasdb"
		self.fieldPat = re.compile("([A-Za-z_][A-Za-z0-9-_$]+)\.([A-Za-z_][A-Za-z0-9-_$]+)")
		self.paramPlaceholder = "?"
		import kinterbasdb
		initialized = getattr(kinterbasdb, "initialized", None)
		if not initialized:
			if initialized is None:
				# type_conv=200 KeyError with the older versions. User will need
				# mxDateTime installed as well:
				kinterbasdb.init()
			else:
				# Use Python's Decimal and datetime types:
				if kinterbasdb.__version__[0] == 3 and kinterbasdb.__version__[1] >= 3:
					# use type_conv=300 for blob encoding
					kinterbasdb.init(type_conv=300)
					dabo.dbActivityLog.info("kinterbasdb.init(type_conv=300)")
				else:
					kinterbasdb.init(type_conv=200)
					dabo.dbActivityLog.info("kinterbasdb.init(type_conv=200)")
			if initialized is None:
				# Older versions of kinterbasedb didn't have this attribute, so we write
				# it ourselves:
				kinterbasdb.initialized = True

		self.dbapi = kinterbasdb


	def getConnection(self, connectInfo, **kwargs):
		# kinterbasdb will barf with unicode strings for user nad password:
		host = ustr(connectInfo.Host)
		port = connectInfo.Port
		if port:
			host = "%s/%s" % (host, port)
		user = str(connectInfo.User)
		password = str(connectInfo.revealPW())
		database = ustr(connectInfo.Database)

		self._connection = self.dbapi.connect(host=host, user=user,
				password=password, database=database, **kwargs)
		return self._connection


	def getDictCursorClass(self):
		return self.dbapi.Cursor


	def noResultsOnSave(self):
		"""
		Firebird does not return the number of records updated, so
		we just have to ignore this, since we can't tell a failed save apart
		from a successful one.
		"""
		return


	def noResultsOnDelete(self):
		"""
		Firebird does not return the number of records deleted, so
		we just have to ignore this, since we can't tell a failed delete apart
		from a successful one.
		"""
		return


	def processFields(self, txt):
		"""
		Firebird requires that all field names be surrounded
		by double quotes.
		"""
		return self.dblQuoteField(txt)


	def escQuote(self, val):
		# escape backslashes and single quotes, and
		# wrap the result in single quotes
		sl = "\\"
		qt = "\'"
		return qt + val.replace(sl, sl+sl).replace(qt, qt+qt) + qt


	def formatDateTime(self, val):
		"""We need to wrap the value in quotes."""
		sqt = "'"		# single quote
		val = ustr(val)
		return "%s%s%s" % (sqt, val, sqt)


	def getTables(self, cursor, includeSystemTables=False):
		if includeSystemTables:
			whereClause = ''
		else:
			whereClause = "where rdb$relation_name not starting with 'RDB$' "

		cursor.execute("select rdb$relation_name from rdb$relations "
			"%s order by rdb$relation_name" % whereClause)
		rs = cursor.getDataSet()
		tables = []
		for record in rs:
			tables.append(record["rdb$relation_name"].strip())
		return tuple(tables)


	def getTableRecordCount(self, tableName, cursor):
		cursor.execute("select count(*) as ncount from %s where 1=1" % tableName)
		return cursor.getDataSet()[0][0]


	def getFields(self, tableName, cursor):
		# Get the PK
### The SQL for the PK changed by Uwe Grauer 2007.08.23
# 		sql = """ select inseg.rdb$field_name
# 		from rdb$indices idxs join rdb$index_segments inseg
# 			on idxs.rdb$index_name = inseg.rdb$index_name
# 			where idxs.rdb$relation_name = '%s'
# 	and idxs.rdb$unique_flag = 1 """ % tableName.upper()
		sql = """ SELECT S.RDB$FIELD_NAME AS COLUMN_NAME
		FROM RDB$RELATION_CONSTRAINTS RC
			LEFT JOIN RDB$INDICES I ON (I.RDB$INDEX_NAME = RC.RDB$INDEX_NAME)
			LEFT JOIN RDB$INDEX_SEGMENTS S ON (S.RDB$INDEX_NAME = I.RDB$INDEX_NAME)
		WHERE (RC.RDB$CONSTRAINT_TYPE = 'PRIMARY KEY')
		AND (I.RDB$RELATION_NAME = '%s') """ % tableName.upper()
		cursor.execute(sql)
		rs = cursor.getDataSet(rows=1)
		try:
			pkField = rs[0]["column_name"].strip()
		except KeyError:
			pkField = None
		except IndexError:
			pkField = None

		# Now get the field info
		sql = """  SELECT b.RDB$FIELD_NAME, d.RDB$TYPE_NAME, c.RDB$FIELD_SUB_TYPE,
 c.RDB$CHARACTER_LENGTH, c.RDB$FIELD_SCALE, b.RDB$FIELD_ID
 FROM RDB$RELATIONS a
 INNER JOIN RDB$RELATION_FIELDS b
 ON a.RDB$RELATION_NAME = b.RDB$RELATION_NAME
 INNER JOIN RDB$FIELDS c
 ON b.RDB$FIELD_SOURCE = c.RDB$FIELD_NAME
 INNER JOIN RDB$TYPES d
 ON c.RDB$FIELD_TYPE = d.RDB$TYPE
 WHERE a.RDB$SYSTEM_FLAG = 0
 AND d.RDB$FIELD_NAME = 'RDB$FIELD_TYPE'
 AND a.RDB$RELATION_NAME = '%s'
 ORDER BY b.RDB$FIELD_ID """ % tableName.upper()

		cursor.execute(sql)
		rs = cursor.getDataSet()
		fields = []
		for r in rs:
			name = r["rdb$field_name"].strip()
			ftype = r["rdb$type_name"].strip().lower()
			if ftype == "text":
				ft = "C"
			elif ftype == "varying":
				if r["rdb$character_length"] > 64:
					ft = "M"
				else:
					ft = "C"
			elif ftype in ("long", "short", "int64"):
				# Can be either integers or float types, depending on column 3
				if r["rdb$field_scale"] == 0:
					# integer
					ft = "I"
				else:
					ft = "N"
			elif ftype in ("float", "double"):
				if r["rdb$field_scale"] == 0:
					ft = "F"
				else:
					ft = "N"
			elif ftype == "date":
				ft = "D"
			elif ftype == "time":
				# Default it to character for now
				ft = "C"
			elif ftype == "timestamp":
				ft = "T"
			elif ftype == "blob":
				if r["rdb$field_sub_type"] == 1:
					ft = "M"
				else:
					ft = "L"
			else:
				ft = "?"

			if pkField is None:
				# No pk defined for the table
				pk = False
			else:
				pk = (name.lower() == pkField.lower() )

			fields.append((name.strip().lower(), ft, pk))
		return tuple(fields)


	def beginTransaction(self, cursor):
		"""Begin a SQL transaction."""
		ret = False
		if not self._connection._has_transaction():
			self._connection.begin()
			dabo.dbActivityLog.info("SQL: begin")
			ret = True
		return ret


	def flush(self, cursor):
		"""
		Firebird requires an explicit commit in order to have changes
		to the database written to disk.
		"""
		self._connection.commit()
		dabo.dbActivityLog.info("SQL: commit")


	def getLimitWord(self):
		"""Override the default 'limit', since Firebird doesn't use that."""
		return "first"


	def formSQL(self, fieldClause, fromClause, joinClause,
				whereClause, groupByClause, orderByClause, limitClause):
		"""Firebird wants the limit clause before the field clause."""
		clauses =  (limitClause, fieldClause, fromClause, joinClause,
				whereClause, groupByClause, orderByClause)
		sql = "SELECT " + "\n".join( [clause for clause in clauses if clause] )
		return sql


	def massageDescription(self, cursor):
		"""Force all the field names to lower case."""
		dd = cursor.descriptionClean = cursor.description
		if dd:
			cursor.descriptionClean = tuple([(elem[0].lower(), elem[1], elem[2],
					elem[3], elem[4], elem[5], elem[6])
					for elem in dd])


	def pregenPK(self, cursor):
		"""
		Determines the generator for which a 'before-insert' trigger
		is associated with the cursor's table. If one is found, get its
		next value and return it. If not, return None.
		"""
		ret = None
		sql = """select rdb$depended_on_name as genname
				from rdb$dependencies
				where rdb$dependent_type = 2
				and rdb$depended_on_type = 14
				and rdb$dependent_name =
				(select rdb$trigger_name from rdb$triggers
				where rdb$relation_name = '%s'
				and rdb$trigger_type = 1 )""" % cursor.Table.upper()
		cursor.execute(sql)
		if cursor.RowCount:
			gen = cursor.getFieldVal("genname").strip()
			sql = """select GEN_ID(%s, 1) as nextval
					from rdb$database""" % gen
			cursor.execute(sql)
			ret = cursor.getFieldVal("nextval")
		dabo.dbActivityLog.info("SQL: result of pregenPK: %d" % ret)
		return ret


	def setSQL(self, sql):
		return self.dblQuoteField(sql)
	def setFieldClause(self, clause, autoQuote=True):
		if autoQuote:
			clause = self.dblQuoteField(clause)
		return clause
	def setFromClause(self, clause, autoQuote=True):
		if autoQuote:
			clause = self.dblQuoteField(clause)
		return clause
	def setWhereClause(self, clause, autoQuote=True):
		if autoQuote:
			clause = self.dblQuoteField(clause)
		return clause
	def setChildFilterClause(self, clause, autoQuote=True):
		if autoQuote:
			clause = self.dblQuoteField(clause)
		return clause
	def setGroupByClause(self, clause, autoQuote=True):
		if autoQuote:
			clause = self.dblQuoteField(clause)
		return clause
	def setOrderByClause(self, clause, autoQuote=True):
		if autoQuote:
			clause = self.dblQuoteField(clause)
		return clause


	def dblQuoteField(self, txt):
		"""
		Takes a string and returns the same string with
		all occurrences of xx.yy replaced with xx."YY".
		In other words, wrap the field name in double-quotes,
		and change it to upper case.
		"""
		def qtField(mtch):
			tbl = mtch.groups()[0]
			fld = mtch.groups()[1].upper()
			return "%s.\"%s\"" % (tbl, fld)
		return self.fieldPat.sub(qtField, txt)


# Test method for all the different field structures, just
# like dblQuoteField().
# def q(txt):
# 	def qtField(mtch):
# 		tbl = mtch.groups()[0]
# 		fld = mtch.groups()[1].upper()
# 		return "%s.\"%s\"" % (tbl, fld)
# 	return pat.sub(qtField, txt)
#
