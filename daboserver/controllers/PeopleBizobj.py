#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dabo

class PeopleBizobj(dabo.biz.RemoteBizobj):
	def defineConnection(self):
		self.setConnectionParams(
				dbType="PostgreSQL", 
				database="webtest", 
				host="localhost",
				user="webuser",
				plainTextPassword="foxrox")


	def validateRecord(self):
		"""Place record validation code here"""
		if "leafe" in self.Record.lastname.lower():
			return "Keep Leafe out of here!"
			
			
