"""
This 32-line script creates a database with sample data, a bizobj, and
then shows the data in a ui grid that is editable and saves the data
back to the underlying table.
"""
import dabo
dabo.ui.loadUI("wx")

# app:
app = dabo.dApp(MainFormClass=None)
app.setup()

# db:
con = dabo.db.dConnection(DbType="sqlite", Database=":memory:")
cur = con.getDaboCursor()
cur.execute("create table customers (id INTEGER PRIMARY KEY, name CHAR, valid INT)")
cur.execute("insert into customers (name, valid) values ('Paul', 0)")
cur.execute("insert into customers (name, valid) values ('John', 1)")
cur.flush()

# biz:
biz = dabo.biz.dBizobj(con)
biz.DataSource = "customers"
biz.KeyField = "id"
biz.UserSQL = "select id, name, valid from customers"
biz.DataStructure = (
		# (field_alias, field_type, pk, table_name, field_name, field_scale)
		("id", "I", True, "customers", "id"),
		("name", "C", False, "customers", "name"),
		("valid", "B", False, "customers", "valid"))

biz.requery()

# ui:
frm = dabo.ui.dForm()
grd = dabo.ui.dGrid(frm, DataSource=biz, Editable=True)
grd.addColumn(DataField="id", Caption="Id")
grd.addColumn(DataField="name", Caption="Name", Editable=True)
grd.addColumn(DataField="valid", Caption="Valid", DataType="bool", Editable=True)
frm.Sizer.append1x(grd)

def butGetDS_hit(evt):
	print grd.DataSet
	print grd.DataSet.execute("select * from dataset where valid")
butGetDS = dabo.ui.dButton(frm, Caption="Print DataSet", OnHit=butGetDS_hit)
frm.Sizer.append(butGetDS)
txt = dabo.ui.dTextBox(frm)
frm.Sizer.append(txt)

frm.show()
app.start()
