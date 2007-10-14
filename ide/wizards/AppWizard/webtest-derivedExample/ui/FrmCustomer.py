# -*- coding: utf-8 -*-
import os
from FrmBase import FrmBase


class FrmCustomer(FrmBase):

	def initProperties(self):
		FrmCustomer.doDefault()
		self.NameBase = "frmCustomer"
		self.Caption = "Customer"


	def addEditPage(self, dataSource, title, pageClass=None):
		# If you have an overridden edit page, stick it in here. eg:
		#pageClass = self.Application.ui.PagEditClient
		FrmCustomer.doDefault(dataSource, title, pageClass)
		

	def afterInit(self):
		FrmCustomer.doDefault()

		# Instantiate the bizobj:
		app = self.Application
		primaryBizobj = app.biz.Customer(app.dbConnection)
		
		# Register it with dForm:
		self.addBizobj(primaryBizobj)
		
		# Set up the field information for the form
		fsXML = os.path.join(app.HomeDirectory, "ui", "fieldSpecs.fsxml")
		rsXML = os.path.join(app.HomeDirectory, "ui", "relationSpecs.rsxml")
		self.setFieldSpecs(fsXML, "customer")
		self.setRelationSpecs(rsXML, app.biz)

		# The form now knows what it needs to create itself. Do it!
		self.creation()

