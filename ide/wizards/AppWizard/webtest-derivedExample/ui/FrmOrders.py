# -*- coding: utf-8 -*-
import os
from FrmBase import FrmBase


class FrmOrders(FrmBase):

	def initProperties(self):
		FrmOrders.doDefault()
		self.NameBase = "frmOrders"
		self.Caption = "Orders"


	def addEditPage(self, dataSource, title, pageClass=None):
		# If you have an overridden edit page, stick it in here. eg:
		#pageClass = self.Application.ui.PagEditClient
		FrmOrders.doDefault(dataSource, title, pageClass)
		

	def afterInit(self):
		FrmOrders.doDefault()

		# Instantiate the bizobj:
		app = self.Application
		primaryBizobj = app.biz.Orders(app.dbConnection)
		
		# Register it with dForm:
		self.addBizobj(primaryBizobj)
		
		# Set up the field information for the form
		fsXML = os.path.join(app.HomeDirectory, "ui", "fieldSpecs.fsxml")
		rsXML = os.path.join(app.HomeDirectory, "ui", "relationSpecs.rsxml")
		self.setFieldSpecs(fsXML, "orders")
		self.setRelationSpecs(rsXML, app.biz)

		# The form now knows what it needs to create itself. Do it!
		self.creation()

