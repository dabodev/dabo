import datetime
from dabo.dLocalize import _
from dBackend import dBackend

class MSSQL(dBackend):
	def __init__(self):
		dBackend.__init__(self)
		#- jfcs 11/06/06 first try getting Microsoft SQL 2000 server working
		# MSSQL requires the installation of FreeTDS.  FreeTDS can be downloaded from 
		# http://www.freetds.org/ 
		self.dbModuleName = "pymssql"
		self.useTransactions = True  # this does not appear to be required
		import pymssql 


	def getConnection(self, connectInfo):
		"""The pymssql module requires the connection be created for the FreeTDS libraries first.  Therefore, the 
		DSN is really the name of the connection for FreeTDS
		  __init__(self, dsn, user, passwd, database = None, strip = 0)"""
		import pymssql 
		
		port = str(connectInfo.Port)
		if not port or port == "None":
			port = 1433
		host = "%s:%s" % (connectInfo.Host, port)
		user = connectInfo.User
		password = connectInfo.revealPW()
		database = connectInfo.Database
				
		self._connection = pymssql.connect(host=host, user=user,password=password, database=database)
		return self._connection


	def getDictCursorClass(self):
		"""Currently this is not working completely"""
		import pymssql
		class conCursor(pymssql.pymssqlCursor):
			def _getconn(self):
				return self.__source
			# pymssql doesn't supply this optional dbapi attribute, so create it here.
			connection = property(_getconn, None, None)
		return conCursor
		#return cursors.Connection.cursor
		

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
		# jfcs 11/01/06 assumed public schema
		tempCursor.execute("select name from sysobjects where xtype = 'U' order by name")
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
		# Ok get the 'field name', 'field type'
		tempCursor.execute("""SELECT table_name=sysobjects.name,
				column_name=syscolumns.name,
			        datatype=systypes.name,
			        length=syscolumns.length
				FROM sysobjects 
				JOIN syscolumns ON sysobjects.id = syscolumns.id
				JOIN systypes ON syscolumns.xtype=systypes.xtype
				WHERE sysobjects.xtype='U' and sysobjects.name = '%s'
				ORDER BY sysobjects.name,syscolumns.colid
 """ % tableName)
		notcleanRS = tempCursor.fetchall()
		#jfcs 11/09/06 added below to remove dup-records that contain the field type as 'sysname'
		# the funny things is the above sql statements works in MS enterprize manager and the
		# record do not contain the 'sysname' record?????
		rs=[]
		for cleanrow in notcleanRS:
			if 'sysname' not in cleanrow:
				rs.append(cleanrow)
		
		## get the PK 
		tempCursor.execute("""select c.name from sysindexes i
				join sysobjects o ON i.id = o.id
				join sysobjects pk ON i.name = pk.name
				AND pk.parent_obj = i.id
				AND pk.xtype = 'PK'
				join sysindexkeys ik on i.id = ik.id
				and i.indid = ik.indid
				join syscolumns c ON ik.id = c.id
				AND ik.colid = c.colid
				where o.name = '%s'
				order by ik.keyno""" % tableName)	
		rs2=tempCursor.fetchall()

		if rs2==[]:
			thePKFieldName = None
		else:
			#thestr = rs2[0][0]
			#thePKFieldName = thestr[thestr.find("(") + 1: thestr.find(")")].split(", ")
			thePKFieldName = rs2[0][0]
		
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
			elif "datetime" in fldType:
				fldType = "T"
			elif "money" in fldType :
				fldType = "N"
			elif "bit" in fldType :
				fldType = "I"
			else:
				fldType = "?"
			fields.append((name.strip(), fldType, pk))
		return tuple(fields)
		

	#def getUpdateTablePrefix(self, tbl):
		#""" By default, the update SQL statement will be in the form of
					#tablename.fieldname
		#but Postgres does not accept this syntax. If not, change
		#this method to return an empty string, or whatever should 
		#preceed the field name in an update statement.
		 #Postgres needs to return an empty string."""
		#return ""
		
		
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
		self.commitTransaction(cursor)
		#self.commitTransaction()
		
	def getLimitWord(self):
		""" JFCS Override the default 'limit', since MS SQL doesn't use that. """
		return "TOP"
	
	def formSQL(self, fieldClause, fromClause, 
				whereClause, groupByClause, orderByClause, limitClause):
		""" MS SQL wants the limit clause before the field clause.	"""
		return "\n".join( ("SELECT ", limitClause, fieldClause, fromClause, 
				whereClause, groupByClause, orderByClause) )
	#def convertDateTime(self,mydate):
		#months={'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
		#mymonth=mydate[0:3]
		#myday = int(mydate[4:6])
		#myyear= int(mydate[7:11])
		#myhour = int(mydate[12:14])
		#theIntMonth=months.get(mymonth)
		#return datetime.datetime(myyear,theInMonth,myday,myhour)