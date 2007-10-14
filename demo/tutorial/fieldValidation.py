# -*- coding: utf-8 -*-
## This was a tutorial for a way to implement field validation, written before
## field validation became a feature built-in to the framework. This demo 
## doesn't use a data or biz layer at all: it simply shows how to trap a
## control's LostFocus event and conditionally allow or deny the user from
## leaving the control. To implement real field validation in your apps, do
## it with the validateField() method of the bizobj.

import dabo
import dabo.dEvents as dEvents

dabo.ui.loadUI("wx")

class Txt(dabo.ui.dTextBox):
	def initEvents(self):
		self.bindEvent(dEvents.GotFocus, self.onGotFocus)
		self.bindEvent(dEvents.LostFocus, self.onLostFocus)

	def onGotFocus(self, evt):
		print "onGotFocus for %s" % self.Name

	def onLostFocus(self, evt):
		print "onLostFocus for %s" % self.Name
		print self.Form.fldValid(self)


class MyForm(dabo.ui.dForm):
	def afterInit(self):
		pan = self.addObject(dabo.ui.dPanel, Size=(200,200))
		pan.addObject(Txt, Name="txtName")
		pan.addObject(Txt, Name="txtPhone", Top=100)
	

	def fldValid(self, obj):
		print "fldValid for %s" % obj.Name
		ret = True
		if obj.Name == "txtPhone":
			if len(obj.Value) < 8:
				ret = False
		if not ret:
			obj.setFocus()
		return ret


app = dabo.dApp(MainFormClass=None)
app.setup()
frm = MyForm()
app.MainForm=frm
frm.show()
app.start()
