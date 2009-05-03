#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dabo

class PeopleBizobj(dabo.biz.dBizobj):
	def afterInit(self):
		self.DataSource = "people"
		self.KeyField = "id"
		self.addFrom("people")
		self.addField("city")
		self.addField("firstname")
		self.addField("stateprov")
		self.addField("lastname")
		self.addField("street")
		self.addField("postalcode")
		self.addField("id")
		self.addOrderBy("lastname")
		self.VirtualFields = {"fullname": self.getFullName}
		
	
	def getFullName(self):
		return " ".join((self.Record.firstname, self.Record.lastname))
		

	def validateRecord(self):
		"""Returning anything other than an empty string from
		this method will prevent the data from being saved.
		"""
		ret = ""
		# Add your business rules here. 
		return ret
