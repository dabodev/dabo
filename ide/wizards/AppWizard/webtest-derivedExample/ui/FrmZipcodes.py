# -*- coding: utf-8 -*-
import os
from FrmBase import FrmBase


class FrmZipcodes(FrmBase):

	def initProperties(self):
		FrmZipcodes.doDefault()
		self.NameBase = "frmZipcodes"
		self.Caption = "Zipcodes"


	def addEditPage(self, dataSource, title, pageClass=None):
		# If you have an overridden edit page, stick it in here. eg:
		#pageClass = self.Application.ui.PagEditClient
		FrmZipcodes.doDefault(dataSource, title, pageClass)
		

	def afterInit(self):
		FrmZipcodes.doDefault()

		# Instantiate the bizobj:
		app = self.Application
		primaryBizobj = app.biz.Zipcodes(app.dbConnection)
		
		# Register it with dForm:
		self.addBizobj(primaryBizobj)
		
		# Set up the field information for the form
		fsXML = os.path.join(app.HomeDirectory, "ui", "fieldSpecs.fsxml")
		rsXML = os.path.join(app.HomeDirectory, "ui", "relationSpecs.rsxml")
		self.setFieldSpecs(fsXML, "zipcodes")
		self.setRelationSpecs(rsXML, app.biz)

		# The form now knows what it needs to create itself. Do it!
		self.creation()

