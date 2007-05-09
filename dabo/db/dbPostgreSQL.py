# -*- coding: utf-8 -*-
import datetime
from dabo.dLocalize import _
from dBackend import dBackend

class Postgres(dBackend):
	"""Class providing PostgreSQL connectivity. Uses psycopg."""
	def __init__(self):
		dBackend.__init__(self)
		#- jfcs 11/01/04 I have to use alpha/beta of psycopg (currently 1.99.10)
		#- because the 1.1.x series does not support a cursor class (confirmed
		#- by the author of the module).
		#self.dbModuleName = "pgdb"
		#self.dbModuleName = "PgSQL"
		self.dbModuleName = "psycopg"
		self.useTransactions = True  # this does not appear to be required
		self.conn_user = ''


	def getConnection(self, connectInfo, **kwargs):
		import psycopg2 as dbapi
		#from pyPgSQL import PgSQL as dbapi
		self.conn_user = connectInfo.User
		#- jfcs 11/01/04 port needs to be a string
		port = str(connectInfo.Port)
		if not port or port == "None":
			port = "5432"
				
		DSN = "host=%s port=%s dbname=%s user=%s password=%s" % (connectInfo.Host,
			port, connectInfo.Database, connectInfo.User, connectInfo.revealPW())
		for kw, val in kwargs:
			DSN += " %s=%s" % (kw, val)
		self._connection = dbapi.connect(DSN)
		return self._connection


	def getDictCursorClass(self):
		# the new psycopg 2.0 supports DictCursor
		import psycopg2.extras as cursors
		return cursors.DictCursor 


	def escQuote(self, val):
		# escape backslashes and single quotes, and
		# wrap the result in single quotes
		sl = "\\"
		qt = "\'"
		return qt + val.replace(sl, sl+sl).replace(qt, sl+qt) + qt
	
	
	def formatDateTime(self, val):
		""" We need to wrap the value in quotes. """
		sqt = "'"		# single quote
		return "%s%s%s" % (sqt, str(val), sqt)
	
	
	def getTables(self, includeSystemTables=False):
		tempCursor = self._connection.cursor()
		# jfcs 11/01/04 assumed public schema
		#tempCursor.execute("select tablename from pg_tables where schemaname = 'public'")
		# jfcs 01/22/07 added below to support schema 
		# thanks to Phillip J. Allen who provided a Select state that filtered for the user name
		if includeSystemTables:
			sqltablestr = (("SELECT schemaname || '.' || tablename AS tablename FROM pg_tables WHERE has_table_privilege('%s', schemaname || '.' || tablename, 'SELECT')") % self.conn_user)
	
		else:
			sqltablestr = (("SELECT schemaname || '.' || tablename AS tablename FROM pg_tables WHERE (schemaname not like 'pg_%s' and schemaname not like 'information%s') and has_table_privilege('%s', schemaname || '.' || tablename, 'SELECT')") % ('%','%',self.conn_user))
						
		tempCursor.execute(sqltablestr)
		rs = tempCursor.fetchall()
		
		
		tables = []
		for record in rs:
			tables.append(record[0])
		return tuple(tables)

	
	def getTableRecordCount(self, tableName):
		tempCursor = self._connection.cursor()
		tempCursor.execute("select count(*) as ncount from %s" % tableName)
		return tempCursor.fetchall()[0][0]


	def getFields(self, tableName):
		tempCursor = self._connection.cursor()
		tableNameBreak=tableName.split('.',1)
		localSchemaName = tableNameBreak[0]
		localTableName = tableNameBreak[1]
		#jfcs 11/01/04 works great from psql (but does not work with the psycopg
		#module) and only with postgres 7.4.x and later.  Too bad, the statement
		#does everything in one shot.
		#jfcs 11/02/04 below now works just fine
		#comment it if your working with 7.3.x
		# make sure you uncomment the other code out
		
		# jfcs 01/22/07 actually I'm not sure Dabo is still able to support 7.1 - 7.4
		# should you attempt to Dabo with 7.4 or below please let us know.
		
		#tempCursor.execute("select c.column_name as fielname, c.data_type as fieldtyp, \
		#i.indisprimary AS is_pkey \
		#FROM information_schema.columns c \
		#LEFT JOIN information_schema.key_column_usage cu \
		#ON (c.table_name=cu.table_name AND c.column_name=cu.column_name) \
		#LEFT JOIN pg_class cl ON(cl.relname=cu.table_name) \
		#LEFT JOIN pg_index i ON(cl.oid= i.indrelid) WHERE c.table_name= '%s'" % tableName)
		#rs=tempCursor.fetchall()
		
		
		# Ok get the 'field name', 'field type'
		#tempCursor.execute("""select c.oid,a.attname, t.typname 
				#from pg_class c inner join pg_attribute a 
				#on a.attrelid = c.oid inner join pg_type t on a.atttypid = t.oid 
				#where c.relname = '%s' and a.attnum > 0 """ % tableName)
		# JFCS 01/22/07 Added support for schema 
		tempCursor.execute("""select c.oid,a.attname, t.typname, b.schemaname from pg_class c 
inner join pg_attribute a on a.attrelid = c.oid 
inner join pg_type t on a.atttypid = t.oid 
inner join pg_tables b on b.tablename=c.relname
where (b.schemaname || '.'|| c.relname)  = '%s' and a.attnum > 0 """ % tableName)
		rs = tempCursor.fetchall()

		## get the PK the code should work well with 7.4 - 8.2 versions
		
		sqlstr = """SELECT n.nspname AS schema_name, c.relname AS table_name,
           c.oid AS table_oid, a.attname AS column_name, idx.n + 1 AS ordinal_position
      FROM pg_class c, pg_attribute a, pg_index i, pg_namespace n, generate_series(0, 31) idx(n)
     WHERE c.oid = a.attrelid AND c.oid = i.indrelid AND i.indisprimary AND a.attnum = i.indkey[idx.n]
       AND NOT a.attisdropped
       AND has_schema_privilege(n.oid, 'USAGE'::text)
       AND n.nspname NOT LIKE 'pg!_%s' ESCAPE '!'
       AND has_table_privilege(c.oid, 'SELECT'::text)
       AND c.relnamespace = n.oid and c.relname = '%s' and n.nspname = '%s' """ % ('%',localTableName,localSchemaName)
		
		tempCursor.execute(sqlstr)
		rs2=tempCursor.fetchall()
		if rs2==[]:
			thePKFieldName = None
		else:
			#thestr = rs2[0][3]
			#thePKFieldName = thestr[thestr.find("(") + 1: thestr.find(")")].split(", ")
			thePKFieldName = rs2[0][3]
		
		fields = []
		for r in rs:
			name = r[1]
			fldType =r[2]
			pk = False
			if thePKFieldName is not None:
				pk = (name in thePKFieldName)
			if "int" in fldType:
				fldType = "I"
			elif "char" in fldType :
				fldType = "C"
			elif "bool" in fldType :
				fldType = "B"
			elif "text" in fldType:
				fldType = "M"
			elif "numeric" in fldType:
				fldType = "N"
			elif "double" in fldType:
				fldType = "F"
			elif "real" in fldType:
				fldType = "F"
			elif "float" in fldType:
				fldType = "F"
			elif "datetime" in fldType:
				fldType = "T"
			elif "timestamp" in fldType:
				fldType = "T"
			elif "date" in fldType:
				fldType = "D"
			elif "bytea" in fldType:
				fldType = "L"
			elif "point" in fldType:
				fldType = "C"
			elif "box" in fldType:
				fldType = "C"
			elif "circle" in fldType:
				fldType = "C"
			elif "lseg" in fldType:
				fldType = "C"
			elif "polygon" in fldType:
				fldType = "C"
			elif "path" in fldType:
				fldType = "C"
			elif "oid" in fldType:
				fldType = "G"
			else:
				fldType = "?"
			fields.append((name.strip(), fldType, pk))
		return tuple(fields)
		

	def getUpdateTablePrefix(self, tbl, autoQuote=True):
		""" By default, the update SQL statement will be in the form of
					tablename.fieldname
		but Postgres does not accept this syntax. If not, change
		this method to return an empty string, or whatever should 
		preceed the field name in an update statement.
		 Postgres needs to return an empty string."""
		return ""
		
		
	def noResultsOnSave(self):
		""" Most backends will return a non-zero number if there are updates.
		Some do not, so this will have to be customized in those cases.
		"""
		return 


	def noResultsOnDelete(self):
		""" Most backends will return a non-zero number if there are deletions.
		Some do not, so this will have to be customized in those cases.
		"""
		#raise dException.dException, _("No records deleted")
		return 

	
	def flush(self, cursor):
		""" Postgres requires an explicit commit in order to have changes
		to the database written to disk.
		"""
		self.commitTransaction(cursor)
