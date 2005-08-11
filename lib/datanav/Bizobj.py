import dabo.biz

class Bizobj(dabo.biz.dBizobj):
	def addField(self, fld):
		try:
			self.backendTableFields
		except AttributeError:
			self.backendTableFields = {}
		try:
			cursorInfo, alias = fld.split(" as ")
			table, field = cursorInfo.split(".")		
		except:
			# if fld wasn't sent as the conventional "table.field as alias",
			# then there's nothing to automatically do.
			alias, table, field = None, None, None
		if alias is not None:
			self.backendTableFields[alias] = (table, field)

		Bizobj.doDefault(fld)

		## self.backendTableFields:
		## This custom property contains optional information
		## for filling out the where clause. Say you have the
		## following base sql:
		##
		##  select invoice.number as invoicenumber,
		##         customer.name as name
		##    from invoice
		##   inner join customer
		##      on customer.id = invoice.custid
		##
		## The where clause as generated using fieldSpecs
		## will incorrectly do "WHERE invoice.invoicenumber = "
		## or "WHERE invoice.name = "
		##
		## So, tell it explicitly which table and field
		## to use for a given fieldname:
		##  self.backendTableFields["invoicenumber"] = ("invoice", "number")
		##  self.backendTableFields["name"] = ("customer", "name")         
