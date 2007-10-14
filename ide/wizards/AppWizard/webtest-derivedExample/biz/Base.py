# -*- coding: utf-8 -*-
import dabo.lib.datanav as datanav

class Base(datanav.Bizobj):

	def afterInit(self):
		Base.doDefault()
		self.setBaseSQL()


	def setBaseSQL(self):
		pass
