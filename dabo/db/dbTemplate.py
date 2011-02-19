# -*- coding: utf-8 -*-
"""
This is a template for creating new backend-specific scripts. To create
a script to support a database not yet suppported by Dabo, make a copy
of this file in the dabo/db directory, and name the copy 'dbProduct.py',
where 'Product' is the actual name of the database (e.g., dbMySQL.py,
dbFirebird.py, etc.)

This template uses 'NEWDATABASE' as the name of the database; you
should replace this with the actual name of the database
(e.g., Oracle, PostgreSQL, etc.)

Then go down through each section marked with TODO comments, and
modify the code so that it works correctly for this particular database. As
soon as you know that it works, remove the TODO comment, and replace it
with anything that might be relevant.

These database-specific scripts are designed to abstract out those parts
of the code that can vary among the various products out there. By
customizing the code in these methods, the standard cursor works great
in the framework with any database backend. However, if you find
something about your database that simply can't be fixed by
customizing these methods, report it to the dabo-dev list; it may require
some refactoring of the code to handle a situation that is unique to this
particular database.
"""
import datetime
from dabo.dLocalize import _
from dBackend import dBackend
from dabo.lib.utils import ustr



class NEWDATABASE(dBackend):
	def __init__(self):
		dBackend.__init__(self)
		#### TODO: Customize with name of dbapi module
		self.dbModuleName = "???"


	def getConnection(self, connectInfo, **kwargs):
		#### TODO: replace 'ZZZ' with dbapi module name
		import ZZZ as dbapi

		port = connectInfo.Port
		if not port:
			#### TODO: Customize with standard NEWDATABASE port
			port = -1

		#### TODO: Customize to make correct connect string
		self._connection = dbapi.connect(host=connectInfo.Host,
				user=connectInfo.User, passwd=connectInfo.revealPW(),
				db=connectInfo.Database, port=port, **kwargs)

		return self._connection


	def getDictCursorClass(self):
		#### TODO: Replace 'ZZZ' with appropriate NEWDATABASE dbapi
		####  module class or just a standard cursor, if it doesn't offer Dict cursors.
		return ZZZ.DictCursor


	def escQuote(self, val):
		#### TODO: Verify that NEWDATABASE uses this method for escaping quotes
		# escape backslashes and single quotes, and
		# wrap the result in single quotes
		sl = "\\"
		qt = "\'"
		return qt + val.replace(sl, sl+sl).replace(qt, sl+qt) + qt


	def formatDateTime(self, val):
		"""We need to wrap the value in quotes."""
		#### TODO: Make sure that the format for DateTime
		####    values is returned correctly
		sqt = "'"		# single quote
		val = ustr(val)
		return "%s%s%s" % (sqt, val, sqt)


	def getTables(self, cursor, includeSystemTables=False):
		#### TODO: Verify that this works with NEWDATABASE, including
		####    the option for including/excluding system tables.
		cursor.execute("show tables")
		rs = cursor.fetchall()
		tables = []
		for record in rs:
			tables.append(record[0])
		return tuple(tables)


	def getTableRecordCount(self, tableName):
		#### TODO: Verify that this is the correct syntax for NEWDATABASE
		tempCursor = self._connection.cursor()
		tempCursor.execute("select count(*) as ncount from %s" % tableName)
		return tempCursor.fetchall()[0][0]


	def getFields(self, tableName):
		tempCursor = self._connection.cursor()
		#### TODO: Modify for NEWDATABASE syntax
		tempCursor.execute("describe %s" % tableName)
		rs = tempCursor.fetchall()
		fldDesc = tempCursor.description
		# The field name is the first element of the tuple. Find the
		# first entry with the field name 'Key'; that will be the
		# position for the PK flag
		for i in range(len(fldDesc)):
			if fldDesc[i][0] == 'Key':
				pkPos = i
				break

		fields = []
		for r in rs:
			#### TODO: Alter these so that they match the field type
			####    names returned by NEWDATABASE.
			name = r[0]
			ft = r[1]
			if ft.split()[0] == "tinyint(1)":
				ft = "B"
			elif "int" in ft:
				ft = "I"
			elif "varchar" in ft:
				# will be followed by length
				ln = int(ft.split("(")[1].split(")")[0])
				if ln > 255:
					ft = "M"
				else:
					ft = "C"
			elif "char" in ft :
				ft = "C"
			elif "text" in ft:
				ft = "M"
			elif "decimal" in ft:
				ft = "N"
			elif "datetime" in ft:
				ft = "T"
			elif "date" in ft:
				ft = "D"
			elif "enum" in ft:
				ft = "C"
			else:
				ft = "?"
			pk = (r[pkPos] == "PRI")

			fields.append((name.strip(), ft, pk))
		return tuple(fields)


	def getWordMatchFormat(self):
		#### TODO: If NEWDATABASE supports fulltext searches with matching by
		####    words, create an expression that will execute such a search
		####    The format must have the expressions %(table)s, %(field)s and %(value)s
		####    which will be replaced with the table, field, and value strings,
		####    respectively. If NEWDATABASE does not support word searches, delete
		####    this method to use the default backend class's method.
		return """ match (%(table)s.%(field)s) against ("%(value)s") """
