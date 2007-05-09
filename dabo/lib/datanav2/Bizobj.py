# -*- coding: utf-8 -*-
import dabo.biz

class Bizobj(dabo.biz.dBizobj):
	def getBaseWhereClause(self):
		"""Subclasses can return a where clause stub that will always exist,
		no matter what the user selects on the select page. For instance:
	
			return "clients.ldeleted = 0 and invoices.ldeleted=0"
	
		Don't include the word "where": that'll be added automatically later.
		"""
		return ""

	def addField(self, fld):
		try:
			cursorInfo, alias = fld.split(" as ")
			table, field = cursorInfo.split(".")		
		except:
			# if fld wasn't sent as the conventional "table.field as alias",
			# then there's nothing to automatically do.
			alias, table, field = None, None, None
		if alias is not None:
			self.BackendTableFields[alias] = (table, field)

		self.super(fld)


	def _getBackendTableFields(self):
		try:
			v = self._backendTableFields
		except AttributeError:
			v = self._backendTableFields = {}
		return v

	def _setBackendTableFields(self, val):
		assert isinstance(val, dict)
		self._backendTableFields = val

	BackendTableFields = property(_getBackendTableFields,
			_setBackendTableFields, None, 
			"""Contains information for properly filling out the where clause.

			If you have the following base sql:

				select invoice.number as invoicenumber,
				       customer.name as name
				  from invoice
				 inner join customer
				    on customer.id = invoice.custid

			The where clause as generated using fieldSpecs will incorrectly 
			do "WHERE invoice.invoicenumber = " or "WHERE invoice.name = "

			The BackendTableFields property tells it explicitly which table and 
			field to use for a given fieldname:

				self.BackendTableFields["invoicenumber"] = ("invoice", "number")
				self.BackendTableFields["name"] = ("customer", "name")

			Note that you don't need to set this property if you call addField()
			with the standard explicit sql field clause, because it will happen
			automatically. In other words, the only thing your code really needs
			to do is to call self.addField():

				self.addField("invoice.number as invoicenumber")
				self.addField("customer.name as name")
			""")
