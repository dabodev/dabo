#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" SimpleFormWithControls.py

This demo shows a subclass of dForm populated by dControl instances. 
Since this demo isn't connected to any data, we only need to import 
the ui layer.

A good amount of the 'bulk' in this code has to do with setting up 
the vertical and horizontal sizers.
"""
import dabo.ui

# For now, 'wx' is the only valid UI. In the future, though, try changing
# this to 'tk' or 'qt'...
ui = "wx"
if not dabo.ui.loadUI(ui):
	dabo.errorLog.write("Could not load ui '%s'." % ui)


class MyForm(dabo.ui.dForm):
	def afterInit(self):
		self.Caption = "Simple Form with Controls"
		self.instantiateControls()

	def instantiateControls(self):
		# The form will contain a panel, which will contain all 
		# the controls. Otherwise, tab traversal won't work.
		panel = self.addObject(dabo.ui.dPanel)

		# a vertical sizer will contain several horizontal sizers
		vs = dabo.ui.dSizer("vertical")
		vs.DefaultSpacing = 5
		vs.DefaultBorder= 20
		vs.DefaultBorderLeft = vs.DefaultBorderRight = True
		vs.appendSpacer(20)

		# Instantiate several dControls and dLabels into
		# separate horizontal sizers
		for obj in ((dabo.ui.dTextBox, "txtCounty", "County"), 
					(dabo.ui.dTextBox, "txtCity", "City"),
					(dabo.ui.dTextBox, "txtZipcode", "Zip"),
					(dabo.ui.dSpinner, "spnPopulation", "Population"),
					(dabo.ui.dCheckBox, "chkReviewed", "Reviewed"),
					(dabo.ui.dEditBox, "edtComments", "Comments"),
					(dabo.ui.dSlider, "sldFactor", "Factor"),
					(dabo.ui.dButton, "cmdOk", "Ok")):
			bs = dabo.ui.dSizer("horizontal")

			# Names, captions, and objects are all in the tuple:
			label = panel.addObject(dabo.ui.dLabel, Alignment="Right", Width=150)
			if issubclass(obj[0], (dabo.ui.dCheckBox, dabo.ui.dButton)):
				label.Caption = ""
			else:
				label.Caption = "%s:" % obj[2]
			bs.append(label, "fixed")

			if obj[0] is dabo.ui.dEditBox:
				layout = "expand"
			else:
				layout = "normal"

			# Instantiate the object:
			object = obj[0](panel, Name=obj[1], LogEvents=["Hit"])
			if isinstance(object, (dabo.ui.dCheckBox, dabo.ui.dButton)):
				object.Caption = "%s" % obj[2]

			bs.append(object, layout, 1)

			if isinstance(object, dabo.ui.dEditBox):
				vs.append(bs, "expand", 1)
			else:
				vs.append(bs, "expand")

		vs.appendSpacer(20)
		panel.Sizer = vs        
		panel.Sizer.layout()
		self.Sizer = dabo.ui.dSizer("vertical")
		self.Sizer.append(panel, "expand", 1)
		self.Sizer.layout()
		self.fitToSizer()


if __name__ == "__main__":
	app = dabo.dApp()
	app.BasePrefKey = "demo.simpleFormWithControls"
	app.MainFormClass = MyForm
	app.start()
