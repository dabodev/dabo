from dBackend import dBackend
import datetime

class Postgres(dBackend):
	def __init__(self):
		dBackend.__init__(self)
		#- jfcs 11/01/04 I have to use alpha/beta of psycopg (currently 1.99.10)
		#- because the 1.1.x series does not support a cursor class (confirmed
		#- by the author of the module).
		#self.dbModuleName = "pgdb"
		#self.dbModuleName = "PgSQL"
		self.dbModuleName = "psycopg"
		self.useTransactions = True  # this does not appear to be required

	def getConnection(self, connectInfo):
		### TODO: what connector should we use?
		import psycopg as dbapi
		#from pyPgSQL import PgSQL as dbapi
		
		#- jfcs 11/01/04 port needs to be a string
		port = str(connectInfo.Port)
		if not port or port == 'None':
			port = '5432'
				
		DSN = "host=%s port=%s dbname=%s user=%s password=%s" % (connectInfo.Host,
			port,
			connectInfo.DbName,
			connectInfo.User,
			connectInfo.revealPW())
			
		self._connection = dbapi.connect(DSN)
		return self._connection

	def getDictCursorClass(self):
		### TODO: If PostgreSQL doesn't offer specific Dict cursors, 
		###   return a plain one, and Dabo will convert it.
		# the new psycopg 2.0 supports DictCursor
		import psycopg.extras as cursors
		return cursors.DictCursor 

	def escQuote(self, val):
		### TODO: This method needs to escape any 'dangerous' characters,
		###   and properly enclose a string value in quotes.
		# escape backslashes and single quotes, and
		# wrap the result in single quotes
		sl = "\\"
		qt = "\'"
		return qt + val.replace(sl, sl+sl).replace(qt, sl+qt) + qt
	
	def formatDateTime(self, val):
		""" We need to wrap the value in quotes. """
		### TODO:  How does PostgreSQL handle date-time values?
		sqt = "'"		# single quote
		return "%s%s%s" % (sqt, str(val), sqt)
		
	def getTables(self, includeSystemTables=False):
		tempCursor = self._connection.cursor()
		### TODO: Verify that this is the correct syntax
		# jfcs 11/01/04 assumed public schema
		tempCursor.execute("select tablename from pg_tables where schemaname = 'public'")
		rs = tempCursor.fetchall()
		tables = []
		for record in rs:
			tables.append(record[0])

		return tuple(tables)
		
	def getTableRecordCount(self, tableName):
		tempCursor = self._connection.cursor()
		### TODO: Verify syntax
		tempCursor.execute("select count(*) as ncount from %s" % tableName)
		return tempCursor.fetchall()[0][0]

	def getFields(self, tableName):
		tempCursor = self._connection.cursor()
		### TODO: Verify syntax
		#jfcs 11/01/04 works great from psql (but does not work with the psycopg
		#module) and only with postgres 7.4.x and later.  Too bad, the statement
		#does everything in one shot.
		#jfcs 11/02/04 below now works just fine
		#comment it if your working with 7.3.x
		# make sure you uncomment the other code out
		
		#tempCursor.execute("select c.column_name as fielname, c.data_type as fieldtyp, \
		#i.indisprimary AS is_pkey \
		#FROM information_schema.columns c \
		#LEFT JOIN information_schema.key_column_usage cu \
		#ON (c.table_name=cu.table_name AND c.column_name=cu.column_name) \
		#LEFT JOIN pg_class cl ON(cl.relname=cu.table_name) \
		#LEFT JOIN pg_index i ON(cl.oid= i.indrelid) WHERE c.table_name= '%s'" % tableName)
		#rs=tempCursor.fetchall()
		
		
		# jfcs 11/01/04 Below sucks but works with 7.3.x and 7.4.x (don't know anything
		# about 8.0.x) 
		# Ok get the 'field name', 'field type'
		tempCursor.execute("Select c.oid,a.attname, t.typname \
		from pg_class c inner join pg_attribute a \
		on a.attrelid = c.oid inner join pg_type t on a.atttypid = t.oid \
		where c.relname = '%s' and a.attnum > 0 " % tableName)
		rs = tempCursor.fetchall()
		myoid=rs[0][0]
		## get the PK 
		tempCursor.execute("SELECT c2.relname, i.indisprimary, i.indisunique, pg_catalog.pg_get_indexdef(i.indexrelid) \
		FROM pg_catalog.pg_class c, pg_catalog.pg_class c2, pg_catalog.pg_index i \
		WHERE c.oid = %s AND c.oid = i.indrelid AND i.indexrelid = c2.oid \
		AND i.indisprimary =TRUE \
		ORDER BY i.indisprimary DESC, i.indisunique DESC, c2.relname" % myoid)	
		rs2=tempCursor.fetchall()
		if rs2==[]:
			thePKFieldName=False
		else:
			thestr=rs2[0][3]
			thePKFieldName=thestr[thestr.find('(')+1:thestr.find(')')]
		
		fields = []
		### TODO: Verify the field type names returned.
		for r in rs:
			
			name = r[1]
			fldType =r[2]
			if name == thePKFieldName:
				pk = True
			else:
			        pk = False
			
			if 'int' in fldType:
				fldType = 'I'
			elif 'char' in fldType :
				fldType = 'C'
			elif 'text' in fldType:
				fldType = 'M'
			elif 'numeric' in fldType:
				fldType = 'N'
			elif 'datetime' in fldType:
				fldType = 'T'
			elif 'date' in fldType:
				fldType = 'D'
			else:
				fldType = "?"
			
			
			fields.append((name.strip(), fldType, pk))
			
		return tuple(fields)
		
	### TODO: Customize these for PostgreSQL syntax.

	def beginTransaction(self, cursor):
		""" Begin a SQL transaction."""
		# jfcs 11/01/04 not sure of this
		# Normally Postgres is in the 
		# transaction mode always????
		#if self.useTransactions:
		cursor.execute("BEGIN")

	def commitTransaction(self, cursor):
		""" Commit a SQL transaction."""
		#if self.useTransactions:
		cursor.execute("COMMIT")

	def rollbackTransaction(self, cursor):
		""" Roll back (revert) a SQL transaction."""
		#if self.useTransactions:
		cursor.execute("ROLLBACK")
		

	
	def getUpdateTablePrefix(self, tbl):
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
		#TODO find out what it should return when it fails....
		return 

	def noResultsOnDelete(self):
		""" Most backends will return a non-zero number if there are deletions.
		Some do not, so this will have to be customized in those cases.
		"""
		#raise dException.dException, _("No records deleted")
		#TODO find out what it should return when it fails....
		return 
	
	def flush(self, cursor):
		""" Postgres requires an explicit commit in order to have changes
		to the database written to disk.
		"""
		cursor.execute("COMMIT")
