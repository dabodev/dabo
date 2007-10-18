# -*- coding: utf-8 -*-
# myForms.py
# Created with the Dabo AppWizard on Fri Jan 21 17:43:30 2005.

import os.path
import dabo
import dabo.lib.datanav as datanav
import myBizobjs, myFileOpenMenu

dabo.ui.loadUI("wx")

### Define a base form class for the application:
class MyFormBase(datanav.Form):

	def afterInit(self):
		# The connect info was already loaded by dApp, but a connection instance is
		# needed to pass to the bizobj's constructor.
		self.connection = dabo.db.dConnection(self.Application.dbConnectionDefs["dabo@paulmcnett.com"])
		MyFormBase.doDefault()


	def afterSetMenuBar(self):
		myFileOpenMenu.fill(self)


### Each table gets its own form derived from MyFormBase:
class frmReccats(MyFormBase):
	def initProperties(self):
		self.NameBase = "frmReccats"
		self.Caption = "Recipe Categories"
		
	def afterInit(self):
		frmReccats.doDefault()
		# This next property affects the behavior of a form
		# that has more than one table being edited, such as
		# parent/child relationships. When True, clicking on
		# Save, Cancel or Requery will affect all tables; when
		# False (default), only the current table and its children
		# (if any) will be affected.
		self.saveCancelRequeryAll = False

		# Instantiate the bizobj defined in myBizobjs.py:
		primaryBizobj = myBizobjs.BizReccats(self.connection)
		
		# Register it with dForm:
		self.addBizobj(primaryBizobj)
		
		# Tell the datanav.Form some things about the columns in the result set,
		# so that it can do some automatic setup chores, such as filling in the
		# browse grid, edit page, and select page. If you want to control what 
		# fields appear on the select/browse/edit pages, run the FieldSpecEditor
		# program, and select the file named 'fieldSpecs.fsxml' in your app's 
		# directory.
		fsXML = os.path.join(self.Application.HomeDirectory, "fieldSpecs.fsxml")
		rsXML = os.path.join(self.Application.HomeDirectory, "relationSpecs.rsxml")
		# Set up the field information for the form
		self.setFieldSpecs(fsXML, "reccats")
		# Now initialize the relations to child bizobjs, if any.
		self.setRelationSpecs(rsXML, myBizobjs)
		# The form now knows what it needs to create itself. Do it!
		self.creation()
	
	def beforeCreation(self):
		""" This will be called before the form's menu and toolbar are
		created, and before any objects on the form are created. Use this to 
		customize the form as required.
		"""
		pass
	
	def afterCreation(self):
		""" This will be called after all parts of the form are 
		created. Use this method to make any last-minute adjustments
		"""
		pass


class frmRecipes(MyFormBase):
	def initProperties(self):
		self.NameBase = "frmRecipes"
		self.Caption = "Recipes"

	def afterInit(self):
		frmRecipes.doDefault()
		# This next property affects the behavior of a form
		# that has more than one table being edited, such as
		# parent/child relationships. When True, clicking on
		# Save, Cancel or Requery will affect all tables; when
		# False (default), only the current table and its children
		# (if any) will be affected.
		self.saveCancelRequeryAll = False

		# Instantiate the bizobj defined in myBizobjs.py:
		primaryBizobj = myBizobjs.BizRecipes(self.connection)
		
		# Register it with dForm:
		self.addBizobj(primaryBizobj)

		# Tell the datanav.Form some things about the columns in the result set,
		# so that it can do some automatic setup chores, such as filling in the
		# browse grid, edit page, and select page. If you want to control what 
		# fields appear on the select/browse/edit pages, run the FieldSpecEditor
		# program, and select the file named 'fieldSpecs.fsxml' in your app's 
		# directory.
		fsXML = os.path.join(self.Application.HomeDirectory, "fieldSpecs.fsxml")
		rsXML = os.path.join(self.Application.HomeDirectory, "relationSpecs.rsxml")
		# Set up the field information for the form
		self.setFieldSpecs(fsXML, "recipes")
		# Now initialize the relations to child bizobjs, if any.
		self.setRelationSpecs(rsXML, myBizobjs)
		# The form now knows what it needs to create itself. Do it!
		self.creation()
	
	def beforeCreation(self):
		""" This will be called before the form's menu and toolbar are
		created, and before any objects on the form are created. Use this to 
		customize the form as required.
		"""
		pass
	
	def afterCreation(self):
		""" This will be called after all parts of the form are 
		created. Use this method to make any last-minute adjustments
		"""
		pass

