#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dabo

class ActivitiesBizobj(dabo.biz.dBizobj):
	def afterInit(self):
		self.DataSource = "activities"
		self.KeyField = "id"
		self.addFrom("activities")
		self.addField("details")
		self.addField("reported_date")
		self.addField("severity")
		self.addField("id")
		self.LinkField = "people_fk"
		
		self.NonUpdateFields = ["reported_date"]


	def initProperties(self):
		self.ChildCacheInterval = 60

	
	def validateRecord(self):
		"""Returning anything other than an empty string from
		this method will prevent the data from being saved.
		"""
		ret = ""
		# Add your business rules here. 
		return ret
