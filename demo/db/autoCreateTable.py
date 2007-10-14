# -*- coding: utf-8 -*-
import dabo
from dabo.db import dTable
import dabo.biz.dAutoBizobj as autobiz

def main():
	#Connect to database
	ci = dabo.db.dConnectInfo(DbType="SQLite", Database="act.db")
	conn = dabo.db.dConnection(ci)
	
	class table1(autobiz):
		def getTable(self):
			t = dTable(Name="table1")
			t.addField(Name="id", DataType="int", Size=8, IsPK=True)
			return t
	
	class table2(autobiz):
		def getTable(self):
			t = dTable(Name="table2")
			t.addField(Name="id", DataType="int", Size=8, IsPK=True)
			t.addField(Name="data", DataType="string", Size=25)
			t.addIndex(Name="idx_data", Fields="data")
			return t
			
	dabo.biz.setupAutoBiz(conn, (table1, table2))
	dabo.biz.autoCreateTables()

if __name__ == "__main__":
	main()
	