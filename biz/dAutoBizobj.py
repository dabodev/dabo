import dabo
from dabo.dLocalize import _
import dabo.dException as dException
from dabo.biz.dBizobj import dBizobj

class modglob:
	_AutoTables = {}
	_toExc = {}
g = modglob()

def AutoCreateTables(noAccessDialog=None):
	"""This function creates tables if they don't exist.
	Tables are added to the list of tables for auto creation when the Table
	property is set for a dAutoBizobj.
	"""
	if len(g._AutoTables) == 0:
		raise dException.dException(_("No tables have been setup for autocreation."))	
		
	g._toExc = {}
	for biz in g._AutoTables.values():
		ac = biz.AutoCommit 
		biz.AutoCommit = True
		biz.CreateTable()
		
		biz.AutoCommit = ac
		
	if g._toExc:
		if dabo.dAppRef is not None:
			class DbAdminLogin(dabo.ui.dDialog):
				def __init__(self, parent, conn):
					self._conn = conn
					DbAdminLogin.doDefault(parent)
				
				def addControls(self):
					self.Caption = self.Application.getAppInfo("appName")
					
					self.Sizer = dabo.ui.dSizer("v")
					cs = dabo.ui.dGridSizer()
					
					lblmain = self.addObject(dabo.ui.dLabel, Caption=_("The database could not be setup. Contact your DB administrator."), FontBold=True, FontSize=14)
					lblinst = self.addObject(dabo.ui.dLabel, Caption=_("""For the DB Admin:
 The tables must either created by:
  1. using this program by TEMPORARLY giving this program access to the database to create the needed tables.
  2. or executing all the quries in the 'queries.sql' file."""))

					lblinst2 = self.addObject(dabo.ui.dLabel, Caption=_("DBA, please enter the username and password that has access to create tables for database on server '%s' and database '%s'") % (self._conn.ConnectInfo.Host, self._conn.ConnectInfo.Database))

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
					b.bindEvent(dabo.dEvents.Hit, self.onHitOK)
					s.append(b, border=3)
					
					b = self.addObject(dabo.ui.dButton, CancelButton=True, Caption=_("Cancel"))
					b.bindEvent(dabo.dEvents.Hit, self.onHitCancel)
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
			
			for k in g._toExc.keys():
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
						_WriteQueriesToFile(g._toExc)
						raise dException.DBNoAccessException
					else:
						cur = tempConn.getDaboCursor()
						
						#Execute the needed queries
						for query in g._toExc[k]:
							try:
								cur.execute(query)
							except dException.DBNoAccessExeption:
								dabo.ui.stop(_("Could not setup the database. Access was denied."))
								_WriteQueriesToFile(g._toExc)
								raise dException.DBNoAccessException
					
				else:
					login.release()
					_WriteQueriesToFile(g._toExc)
					raise dException.DBNoAccessException
							
		else:
			_WriteQueriesToFile(g._toExc)
			raise dException.DBNoAccessException


def _WriteQueriesToFile(queries):
	f = open("queries.sql", "w")
	for k in queries.keys():
		f.write(_("#Queries for DB '%s' on host '%s':\n") % (k.ConnectInfo.Database, k.ConnectInfo.Host))
		for query in queries[k]:
			f.write("%s;\n" % (query))
			
	f.close
		
class dAutoBizobj(dBizobj):
	"""This class is just like bBizobj but is supports the auto creation of
	the table by setting the table property."""		
	def _beforeInit(self):
		dAutoBizobj.doDefault()
		self._table = None
		self._table_checked = False


	def CreateTable(self):
		if self._table is None:
			raise dException.dException(_("No table has been defined for this bizobj."))
		
		if self._CurrentCursor.BackendObject.isExistingTable(self.Table.Name):
			self._table_checked = True
			return
			
		toExc = self._CurrentCursor.BackendObject.createTableAndIndexes(self._table, self._CurrentCursor)
		if toExc:
			if g._toExc.has_key(self._conn):
				g._toExc[self._conn] = g._toExc[self._conn] + toExc
			else:
				g._toExc[self._conn] = toExc


	def _setTable(self, table):
		if self._table is not None:
			raise dException.dException(_("Table can only be set once."))
		self._table = table
		g._AutoTables[table.Name] = self
		
		self.addFrom(table.Name)
		for f in table.Fields:
			self.addField("%s.%s as %s" % (table.Name, f.Name, f.Name))	


	def _getTable(self):
		return self._table
		
	Table = property(_getTable, _setTable, None,
			_("The table definition for this bizobj.  (object)"))
