#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dabo

class ActivitiesBizobj(dabo.biz.RemoteBizobj):
	def defineConnection(self):
# 		self.setConnectionParams(
# 				dbType="MySQL", 
# 				database="webtest", 
# 				host="dabodev.com",
# 				user="webuser",
# 				plainTextPassword="foxrocks")
		self.setConnectionParams(
				dbType="PostgreSQL", 
				database="webtest", 
				host="localhost",
				user="webuser",
				plainTextPassword="foxrox")


	def validateRecord(self):
		"""Place record validation code here"""
		pass
			
