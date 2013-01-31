# -*- coding: utf-8 -*-
import datetime
import dabo
from dabo.dLocalize import _
import dabo.dException as dException
from dabo.biz.dBizobj import dBizobj
# Make sure that the user's installation supports Decimal.
_USE_DECIMAL = True
try:
	from decimal import Decimal
except ImportError:
	_USE_DECIMAL = False


class modglob:
	_AutoTables = {}
	_toExc = {}
g = modglob()
bizs = g._AutoTables


def setupAutoBiz(conn, autoBizes):
	"""
	This function sets up a list of dAutoBizobj's for auto creation.
	Instead of doing this::

		t = myBiz1(conn)
		t = myBiz2(conn)
		t = myBiz3(conn)
		t = myBiz4(conn)

	Use SetupAutoBiz like so::

		dabo.biz.SetupAutoBiz(conn, (myBiz1, myBiz2, myBiz3, myBiz4))

	"""
	for obj in autoBizes:
		t = obj(conn)


def autoCreateTables(noAccessDialog=None):
	"""
	This function creates tables if they don't exist.
	Tables are added to the list of tables for auto creation when the Table
	property is set for a dAutoBizobj.
	"""
	if len(g._AutoTables) == 0:
		raise dException.dException(_("No tables have been setup for autocreation."))

	g._toExc = {}
	for biz in g._AutoTables.values():
		biz.createTable()

	if g._toExc:
		if dabo.dAppRef is not None:
			class DbAdminLogin(dabo.ui.dDialog):
				def __init__(self, parent, conn):
					self._conn = conn
					super(DbAdminLogin, self).__init__(parent)

				def addControls(self):
					import dabo.dEvents as dEvents
					self.Caption = self.Application.getAppInfo("appName")

					self.Sizer = dabo.ui.dSizer("v")
					cs = dabo.ui.dGridSizer()

					lblmain = self.addObject(dabo.ui.dLabel, Caption=_("The database could not be setup. Contact your DB administrator."), FontBold=True, FontSize=14)
					lblinst = self.addObject(dabo.ui.dLabel, Caption=_("""For the DB Admin:
 The tables must either created by:
  1. using this program by TEMPORARLY giving this program access to the database to create the needed tables.
  2. or executing all the quries in the 'queries.sql' file."""))

					hst, db = self._conn.ConnectInfo.Host, self._conn.ConnectInfo.Database
					lblinst2 = self.addObject(dabo.ui.dLabel, Caption=_("DBA, please enter the username and password that has access to create tables for database on server '%(hst)s' and database '%(db)s'") % locals())

					o = self.addObject(dabo.ui.dLabel, Caption=_("Username"))
					cs.append(o, row=0, col=0, border=3)
					self.txtUsername = self.addObject(dabo.ui.dTextBox)
					cs.append(self.txtUsername, row=0, col=1, border=3)

					o = self.addObject(dabo.ui.dLabel, Caption=_("Password"))
					cs.append(o, row=1, col=0, border=3)
					self.txtPassword = self.addObject(dabo.ui.dTextBox, PasswordEntry=True)
					cs.append(self.txtPassword, row=1, col=1, border=3)

					s = dabo.ui.dSizer()
					b = self.addObject(dabo.ui.dButton, DefaultButton=True, Caption=_("OK"))
					b.bindEvent(dEvents.Hit, self.onHitOK)
					s.append(b, border=3)

					b = self.addObject(dabo.ui.dButton, CancelButton=True, Caption=_("Cancel"))
					b.bindEvent(dEvents.Hit, self.onHitCancel)
					s.append(b, border=3)

					self.Sizer.append(lblmain, border=3, halign="center")
					self.Sizer.append(lblinst, border=3)
					self.Sizer.append(lblinst2, border=3)
					self.Sizer.appendSpacer(7, 7)
					self.Sizer.append(cs, halign="center")
					self.Sizer.appendSpacer(10, 10)
					self.Sizer.append(s, halign='center')

				def onHitOK(self, evt):
					if not self.txtUsername.Value:
						dabo.ui.exclaim(_("You must enter the username first."))
						return

					if not self.txtPassword.Value:
						dabo.ui.exclaim(_("You must enter the password first."))
						return

					self._data = (self.txtUsername.Value, self.txtPassword.Value)
					self.Accepted = True
					self.EndModal(dabo.dConstants.DLG_OK)

				def onHitCancel(self, evt):
					self._data = ()
					self.Accepted = False
					self.EndModal(dabo.dConstants.DLG_CANCEL)

				def _getAnswer(self):
					return self._data

				Answer = property(_getAnswer)

			for k in g._toExc:
				if noAccessDialog is None:
					login = DbAdminLogin(None, k)
				else:
					login = noAccessDialog(None, k)
				login.Modal = True
				ret = login.show()
				if login.Answer:
					user = login.Answer[0]
					password = login.Answer[1]
					login.release()

					#Temporarly connect to the database using the new user and pass
					ci = dabo.db.dConnectInfo(DbType=k.ConnectInfo.DbType, Database=k.ConnectInfo.Database, Host=k.ConnectInfo.Host, User=user, PlainTextPassword=password)
					try:
						tempConn = dabo.db.dConnection(ci)
					except dException.DBNoAccessException:
						dabo.ui.stop(_("Could not access the database with the given username and password."))
						_writeQueriesToFile(g._toExc)
						raise dException.DBNoAccessException
					else:
						cur = tempConn.getDaboCursor()

						#Execute the needed queries
						for query in g._toExc[k]:
							try:
								cur.execute(query)
							except dException.DBNoAccessExeption:
								dabo.ui.stop(_("Could not setup the database. Access was denied."))
								_writeQueriesToFile(g._toExc)
								raise dException.DBNoAccessException

				else:
					login.release()
					_writeQueriesToFile(g._toExc)
					raise dException.DBNoAccessException

		else:
			_writeQueriesToFile(g._toExc)
			raise dException.DBNoAccessException


def _writeQueriesToFile(queries):
	f = open("queries.sql", "w")
	for k in queries:
		db, hst = k.ConnectInfo.Database, k.ConnectInfo.Host
		f.write(_("#Queries for DB '%(db)s' on host '%(hst)s':\n") % locals())
		for query in queries[k]:
			f.write("%s;\n" % (query))
	f.close()



class dAutoBizobj(dBizobj):
	"""This class is just like bBizobj but is supports the auto creation of
	the table by setting the table property.

	If there is a field that is set to AutoIncrement, self.AutoPopulatePK
	is set to true.
	If there is a field that is a stamp field, it is set to not update that field."""
	def _beforeInit(self):
		super(dAutoBizobj, self)._beforeInit()
		self._table = None
		self._table_checked = False


	def _afterInit(self):
		table = self.getTable()
		if table is not None:
			self._table = table
			g._AutoTables[table.Name] = self

			self.DataSource = table.Name
			self.KeyField = table.PK[0]
			self.addFrom(table.Name)
			for fld in table.Fields:
				self.addField("%s.%s as %s" % (table.Name, fld.Name, fld.Name))

				self.DefaultValues[fld.Name] = fld.Default

				if fld.DataType == "Numeric":
					self._CurrentCursor._types[fld.Name] = int
				elif fld.DataType == "Float":
					self._CurrentCursor._types[fld.Name] = float
				elif fld.DataType == "Decimal":
					if _USE_DECIMAL:
						self._CurrentCursor._types[fld.Name] = Decimal
					else:
						pass
				elif fld.DataType == "String":
					self._CurrentCursor._types[fld.Name] = str
				elif fld.DataType == "Date":
					self._CurrentCursor._types[fld.Name] = datetime.date
				elif fld.DataType == "Time":
					self._CurrentCursor._types[fld.Name] = datetime.time
				elif fld.DataType == "DateTime":
					self._CurrentCursor._types[fld.Name] = datetime.datetime
				elif fld.DataType == "Stamp":
					self._CurrentCursor._types[fld.Name] = datetime.datetime
				elif fld.DataType == "Binary":
					self._CurrentCursor._types[fld.Name] = str

				if fld.IsAutoIncrement:
					self.AutoPopulatePK = True

				if fld.DataType == "Stamp":
					self.NonUpdateFields = self.NonUpdateFields + [fld.Name]

		self.afterInit()

	def getTable(self):
		"""Return the dTable definition for the table.
		"""
		#Override in subclass


	def initTable(self):
		"""Return the data to be inserted into the table after it has been created.
		Return a tuple in the format of ((column list), (lists to insert)).
		Example::

			def initTable(self):
				return 	(("firstname","lastname"), (("bob","smith"),("granny","smith"))

		"""
		#Override in subclass


	def createTable(self):
		"""Create the tables that has been asigned to this bizobj."""
		if self._table is None:
			raise dException.dException(_("No table has been defined for this bizobj."))

		if self._CurrentCursor.BackendObject.isExistingTable(self.Table.Name):
			self._table_checked = True
			return

		#Create table
		toExc = self._CurrentCursor.BackendObject.createTableAndIndexes(self._table, self._CurrentCursor)
		if toExc:
			if self._conn in g._toExc:
				g._toExc[self._conn] = g._toExc[self._conn] + toExc
			else:
				g._toExc[self._conn] = toExc

		#Insert data
		to_insert = self.initTable()
		if to_insert:
			if to_insert is dict:
				#in a dict where key is the column and value is a list of data for that column
				for i in range(0, len(to_insert[to_insert.keys()[0]])):
					self.new()
					for k in to_insert:
						self.setFieldVal(k, to_insert[k][i])

					try:
						self.save()
					except dException.DBQueryException, e:
						if self._conn in g._toExc:
							g._toExc[self._conn] = g._toExc[self._conn].append(e.sql)
						else:
							g._toExc[self._conn] = [e.sql]
			else:
				#tuple in the format of ((column list), (lists to insert))
				for row in to_insert[1]:
					self.new()
					for col, val in zip(to_insert[0], row):
						self.setFieldVal(col, val)

					try:
						self.save()
					except dException.DBQueryException, e:
						print 'failed'
						if self._conn in g._toExc:
							g._toExc[self._conn] = g._toExc[self._conn].append(e.sql)
						else:
							g._toExc[self._conn] = [e.sql]


	def _getTable(self):
		return self._table


	Table = property(_getTable, None, None,
			_("The table definition for this bizobj.  (object)"))
