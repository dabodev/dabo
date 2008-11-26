# -*- coding: utf-8 -*-
import datetime
import dabo
from dabo.dLocalize import _
from dBackend import dBackend

class Postgres(dBackend):
	"""Class providing PostgreSQL connectivity. Uses psycopg."""
	def __init__(self):
		""" JFCS 08/23/07 Currently supporting only psycopg2"""
		dBackend.__init__(self)
		self.dbModuleName = "psycopg"
		self.conn_user = ''


	def getConnection(self, connectInfo, **kwargs):
		# forceCreate maybe used in the future
		if 'forceCreate' in kwargs:
			kwargs.pop('forceCreate') 
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
	
	def beginTransaction(self, cursor):
		dabo.dbActivityLog.write("SQL: begin (implicit, nothing done)")
		return True


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
		val = self._stringify(val)
		return "%s%s%s" % (sqt, val, sqt)
	
	
	def getTables(self, cursor, includeSystemTables=False):
		# jfcs 11/01/04 assumed public schema
		# jfcs 01/22/07 added below to support schema 
		# thanks to Phillip J. Allen who provided a Select state that filtered for the user name
		if includeSystemTables:
			sqltablestr = (("SELECT schemaname || '.' || tablename AS tablename FROM pg_tables WHERE has_table_privilege('%s', schemaname || '.' || tablename, 'SELECT')") % self.conn_user)
		else:
			#sqltablestr = (("SELECT schemaname || '.' || tablename AS tablename FROM pg_tables WHERE (schemaname not like 'pg_%s' and schemaname not like 'information%s') and has_table_privilege('%s', schemaname || '.' || tablename, 'SELECT')") % ('%','%',self.conn_user))
		# jfcs 06/19/08 	
			sqltablestr = (("""SELECT schemaname || '.' || tablename AS tablename 
					FROM pg_tables 
					WHERE (schemaname not like 'pg_%s' 
						and schemaname not like 'information%s') 
					and has_table_privilege('%s', schemaname || '.' || tablename, 'SELECT')
					""") % ('%','%',self.conn_user))
		cursor.execute(sqltablestr)
		rs = cursor.getDataSet()
		tables = []
		for record in rs:
			tables.append(record["tablename"])
		return tuple(tables)

	
	def getTableRecordCount(self, tableName, cursor):
		cursor.execute("select count(*) as ncount from %s" % tableName)
		return cursor.getDataSet()[0]["ncount"]


	def getFields(self, tableName, cursor):
		"""JFCS support for 7.4 and greater
		   Requires that each table have a primary key"""
		tableNameBreak=tableName.split('.',1)
		localSchemaName = tableNameBreak[0]
		localTableName = tableNameBreak[1]
		

			
		cursor.execute("""SELECT a.attname, t.typname from pg_attribute a,pg_type t, pg_class c 
		LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
		where a.attrelid = c.oid 
		and a.atttypid = t.oid 
		AND n.nspname || '.'||c.relname = '%s'
		order by c.relname,a.attname""" % tableName)

		rs = cursor.getDataSet()

		#the code below may not work with 7.4 due to the use of the function generate_series()
		#However a postgres function can be added to simulate generate_series()
		#CREATE OR REPLACE FUNCTION generate_series(int, int) RETURNS setof int AS  
		#'BEGIN
		#FOR i IN $1..$2
		#LOOP 
		#RETURN NEXT i;
		#END LOOP; 
		#RETURN; 
		#END; ' LANGUAGE plpgsql;
		
		sqlstr = """SELECT n.nspname AS schema_name, c.relname AS table_name,
           c.oid AS table_oid, a.attname AS column_name, idx.n + 1 AS ordinal_position
      FROM pg_class c, pg_attribute a, pg_index i, pg_namespace n, generate_series(0, 31) idx(n)
     WHERE c.oid = a.attrelid AND c.oid = i.indrelid AND i.indisprimary AND a.attnum = i.indkey[idx.n]
       AND NOT a.attisdropped
       AND has_schema_privilege(n.oid, 'USAGE'::text)
       AND n.nspname NOT LIKE 'pg!_%s' ESCAPE '!'
       AND has_table_privilege(c.oid, 'SELECT'::text)
       AND c.relnamespace = n.oid and c.relname = '%s' and n.nspname = '%s' """ % ('%',localTableName,localSchemaName)
		
		cursor.execute(sqlstr)
		rs2 = cursor.getDataSet()
		if rs2 == ():
			thePKFieldName = None
		else:
			#thestr = rs2[0][3]
			thePKFieldName = rs2[0]['column_name']

		fields = []
		for r in rs:
			name = r["attname"]
			fldType =r["typname"]
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
		dabo.dbActivityLog.write("SQL: Commit")


	def getLastInsertID(self, cursor):
		""" Return the ID of the last inserted row, or None.
		
		When inserting a new record in a table that auto-generates a PK (such 
		as a serial data type) value, different databases have their own way of retrieving that value.
		With Postgres a sequence is created.  The SQL statement determines the sequence name 
		('table_pkid_seq') and needs three parameters the schema name, table name, and the primary
		key field for the table.
		cursor.KeyField = primary field
		cursor.Table = returns 'schema.table' for the cursor
		
		Postgres uses 'currval(sequence_name)' to determine the last value of the session.
		If two different sessions are open (two users accessing the same table for example)
		currval() will return the correct value for each session.
		
		"""
		tableNameBreak=cursor.Table.split('.',1)
		localSchemaName = tableNameBreak[0]
		localTableName = tableNameBreak[1]
		

		tempCursor =self._connection.cursor()

		#JFCS 01/13/08 changed the select statement to allow primary fields that were not based
		#on a serial data type to work.
		# special thanks to Lorenzo Alberton for his help with parsing of the fields.
		# It has been confirmed that the statement works with 7.4 through 8.3.x
		sql="""
		SELECT substring((SELECT substring(pg_get_expr(d.adbin, d.adrelid) for 128) 
		FROM pg_attrdef d 
		WHERE d.adrelid = a.attrelid  AND d.adnum = a.attnum  AND a.atthasdef) 
		FROM 'nextval[^'']*''([^'']*)') 
		FROM pg_attribute a 
		LEFT JOIN pg_class c ON c.oid = a.attrelid 
		LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum AND a.atthasdef 
		LEFT JOIN pg_namespace n ON c.relnamespace = n.oid WHERE (c.relname = %s) 
		AND a.attname = %s and n.nspname=%s AND NOT a.attisdropped AND a.attnum > 0 AND pg_get_expr(d.adbin, d.adrelid) LIKE 'nextval%%' 
		"""

		tempCursor.execute(sql, ( localTableName,cursor.KeyField,localSchemaName))
		rs = tempCursor.fetchall()
		#if rs is None:
			#dabo.dbActivityLog.write("no data in getLastInsertID")

		sqlWithseq_name="""select currval('%s') as curval""" % (rs[0][0],)
		tempCursor.execute(sqlWithseq_name) 
		rs = tempCursor.fetchall()
		if not rs[0][0] is None:
			return rs[0][0]
		else:
			raise AttributeError, "Unable to determine the sequence used or the sequence return a strange value."

