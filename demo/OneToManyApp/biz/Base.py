# -*- coding: utf-8 -*-

import dabo.lib.datanav2 as datanav

class Base(datanav.Bizobj):

	def afterInit(self):
		self.super()
		self.setBaseSQL()


	def setBaseSQL(self):
		pass


	def addFieldsFromDataStructure(self):
		max_fill = 0
		for field in self.DataStructure:
			fill = len("%s.%s" % (field[3], field[4]))
			max_fill = max(max_fill, fill)
		for field in self.DataStructure:
			fill = " " * (max_fill - len("%s.%s" % (field[3], field[4])))
			self.addField("%s.%s %sas %s" % (field[3], field[4], fill, field[0]))
