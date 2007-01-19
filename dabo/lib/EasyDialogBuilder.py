#!/usr/bin/env python
""" EasyDialogBuilder.py

Author:		Nathan Lowrie

This dabo class is a series of functions that refactors repetitive GUI code.  The
refactoring of the GUI code allows for the developer to be more productive.  The
refactored code is also far easier to maintain and comprehend.  This mixin is mainly
targeted and Forms, Dialogs, and Panels.  
"""
import dabo
import types

# For now, 'wx' is the only valid UI. In the future, though, try changing
# this to 'tk' or 'qt'...
ui = "wx"
if not dabo.ui.loadUI(ui):
	dabo.errorLog.write("Could not load ui '%s'." % ui)


class EasyDialogBuilder(object):
	def makePageFrame(self, parent, pageData, properties=None):
		"""makePageFrame(parent, pageData, properties=None) -> dabo.ui.dPageFrame
		
		parent -> dabo object that is the parent of the controls, normally a panel of form
		pageData -> Tuple of Dictionaries with the following relevant keys:
			"page" -> dabo object that is the page.  Normally a dPage or Panel
			"caption" -> optional if defined image, string that is the tab label
			"image" -> optional, dabo image that is the tab label
		properties -> optional dictionary of Properties for the control
		"""
		pageFrame = dabo.ui.dPageFrame(parent, properties=properties)
		
		for page in pageData:
			if page.get("image"):
				page["imgKey"]=str(pageFrame.PageCount)
				pageFrame.addImage(page["image"], imgKey=page["imgKey"])
			elif not page.get("caption"):
				caption = "Page%i" % (pageFrame.PageCount,) 
			
			pageFrame.appendPage(pgCls=page.get("page"), caption=page.get("caption"), imgKey=page.get("imgKey"))
		
		return pageFrame

	def makeControlBox(self, parent, caption, controlFields, border=5, spacing=5, grid=True):
		"""makeControlBox(parent, controlFields, border=5, spacing=5, grid=True) -> dabo.ui.dBorderSizer
		
		parent -> dabo object that is the parent of the controls, normally a panel or form
		grid -> Boolean.  When true all objects are put into a grid sizer for even controlfield alignment.
			When false, all objects are put into boxSizers so the control fields line up with the end
			of their labels.
		controlFields -> Tuple of tuples in form of:
			((control, RegID, label Title, Properties),.....)
			control -> dabo control or string "file" (produces a textbox with a button to get a file)
			RegID -> string of the regID for this particular control
			label Title -> string that appears on the label
			Properties -> optional dictionary of Properties for the control
		
		Note, if you have "file" as a control, following properties as special:
			"directory" = True will cause the control to browse for a directory
			"format" = string will cause the control to only allow the user to select that file type
		"""
		box = dabo.ui.dBorderSizer(parent, "vertical")
		box.Caption = caption
		
		box.DefaultSpacing = spacing
		box.DefaultBorder = border
		box.DefaultBorderAll = True
		
		box.append1x(self.makeControlSizer(parent, controlFields, grid=grid))
		
		return box
	
	def makeControlSizer(self, parent, controlFields, border=5, spacing=5, grid=True):
		"""makeControlSizer(parent, controlFields, border=5, spacing=5, grid=True) -> dabo.ui.dSizer
		
		parent -> dabo object that is the parent of the controls, normally a panel or form
		grid -> Boolean.  When true all objects are put into a grid sizer for even controlfield alignment.
			When false, all objects are put into boxSizers so the control fields line up with the end
			of their labels.
		controlFields -> Tuple of tuples in form of:
			((control, RegID, label Title, Properties),.....)
			control -> dabo control or string "file" (produces a textbox with a button to get a file)
			RegID -> string of the regID for this particular control
			label Title -> string that appears on the label
			Properties -> optional dictionary of Properties for the control
		
		Note, if you have "file" as a control, following properties as special:
			"directory" = True will cause the control to browse for a directory
			"format" = string will cause the control to only allow the user to select that file type
		"""
		if grid:
			Sizer = dabo.ui.dGridSizer(MaxCols=3)
			Sizer.setColExpand(True, 1)
		else:
			Sizer = dabo.ui.dSizer("vertical")
		
		Sizer.DefaultSpacing = spacing
		Sizer.DefaultBorder = border
		Sizer.DefaultBorderAll = True
		
		for obj in controlFields:
			if len(obj)==4 and isinstance(obj[3], types.DictionaryType):
				Properties = obj[3]
			else:
				Properties = {}
			
			controls = self.makeControlField(parent, obj[0], obj[1], obj[2], Properties)
			
			if grid:
				lbl = Sizer.append(controls[0], halign="right")
				if len(controls) > 2:
					Sizer.append(controls[1], "expand")
					Sizer.append(controls[2])
				else:
					szItem = Sizer.append(controls[1], "expand", colSpan=2)
				
				if obj[0] is dabo.ui.dEditBox:
					Sizer.setRowExpand(True, Sizer.getGridPos(szItem)[0])
					Sizer.setItemProp(lbl, "valign", "top")
			else:
				bs = dabo.ui.dSizer("h")
				bs.append(controls[0], halign="right")
				bs.append(controls[1], "expand",1)
				
				if len(controls) > 2:
					bs.append(controls[2])
				
				if obj[0] is dabo.ui.dEditBox:
					Sizer.append(bs, "expand", 1)
				else:
					Sizer.append(bs, "expand")
		
		return Sizer
	
	def makeControlField(self, parent, control, regId, labelTitle, Properties, Sizer=None):
		"""makeControlField(parent, control, regId, labelTitle, Properties) -> List of Dabo Controls
		
		parent -> dabo object that is parent, normally a panel or form
		control -> the dabo class of the control that you want in the form.  Note, class not instansiated object
		regId -> string that is the regId of the control
		labelTitle -> string that is the title of the label next to the control
		Properties -> dictionary of any properties that are supposed to go with the control
		Sizer -> Optional Sizer object.  Used so we can insert objects directly into Grid Sizers
		"""
		
		if not Sizer:
			Sizer = dabo.ui.dSizer("horizontal")
		
		controlList = []
		
		if control == "File":
			if not Properties.get("format"):
				format = "*"
			else:
				format = Properties["format"]
				del Properties["format"]
			
			if not Properties.get("directory"):
				directory = False
			else:
				directory = Properties["directory"]
				del Properties["directory"]
			
			labelTitle += ":"
			
			target = dabo.ui.dTextBox(parent, RegID=regId, ReadOnly=True, properties=Properties)
			controlList.append(target)
			controlList.append(fileButton(parent, format, "%s_button" % (regId,), directory, target))
		else:
			if issubclass(control, (dabo.ui.dCheckBox, dabo.ui.dButton)):
				controlCaption = labelTitle
				labelTitle = ""
			else:
				controlCaption = ""
				labelTitle += ":"
			
			controlList.append(control(parent, RegID=regId, Caption=controlCaption, properties=Properties))
		
		controlList.insert(0, dabo.ui.dLabel(parent, RegID="%s_label" % (regId,), Caption=labelTitle))
		return controlList
	
	def makeButtonBar(self, buttonData, orientation="horizontal"):
		"""makeButtonBar(self, tuple buttonData) -> dabo.ui.dSizer
		
		buttonData is a tuple of tuples in the form of:
			(('button caption', 'regID'),...)
		"""
		hs = dabo.ui.dSizer(orientation=orientation)
		
		for button in buttonData:
			hs.append(dabo.ui.dButton(self, Caption=button[0], RegID=button[1]), "normal")
			hs.appendSpacer(5)
		
		return hs
	
	def setupStandardSizer(self, orientation="vertical"):
		"""setupStandardSizer(self, orientation="vertical") -> dabo.ui.dSizer
		
		Convienence function that sets up a standard sizer with some spacing and borders
		and returns it to the user
		"""
		sizer = dabo.ui.dSizer(orientation)
		sizer.DefaultSpacing = 5
		sizer.DefaultBorder= 10
		sizer.DefaultBorderAll = True
		
		return sizer


class fileButton(dabo.ui.dButton):
	def __init__(self, parent, format, regId, directory, target):
		self.format = format
		self.directory = directory
		self.target = target
		dabo.ui.dButton.__init__(self, parent, RegID=regId)
	
	def afterInit(self):
		self.Caption = "Browse..."
	
	def onHit(self, evt):
		if self.directory:
			self.target.value = dabo.ui.getFolder()
		else:
			self.target.Value = dabo.ui.getFile(self.format)


if __name__ == "__main__":
	class TestForm(dabo.ui.dForm, EasyDialogBuilder):
		def afterInit(self):
			self.Caption = "Simple Form with Controls"
			self.instantiateControls()
			self.Width = 200
	
		def instantiateControls(self):
			self.Sizer = dabo.ui.dSizer("vertical")
			
			pageFrame = self.makePageFrame(self,(
				{"page":controlBoxPage, "caption":"Control Box"},
				{"page":makeSizerTestPage, "caption":"Refactored Sizer"}))
			
			self.Sizer.append1x(pageFrame)
			self.Sizer.layout()
			self.fitToSizer()
	
	class controlBoxPage(dabo.ui.dScrollPanel, EasyDialogBuilder):
		def afterInit(self):
			self.Sizer = self.setupStandardSizer()
			
			self.Sizer.append(dabo.ui.dLabel(self, Caption="Example using the function makeControlBox", RegID="makeControlBox_Label"), "normal")
			self.Sizer.appendSpacer(10)
			
			box = self.makeControlBox(self, "Sample Control Box", 
						((dabo.ui.dTextBox, "txtCounty", "County"), 
						(dabo.ui.dTextBox, "txtCity", "City"),
						(dabo.ui.dTextBox, "txtZipcode", "Zip"),
						(dabo.ui.dSpinner, "spnPopulation", "Population"),
						(dabo.ui.dCheckBox, "chkReviewed", "Reviewed"),
						(dabo.ui.dEditBox, "edtComments", "Comments"),
						(dabo.ui.dSlider, "sldFactor", "Factor"),
						(dabo.ui.dButton, "cmdOk", "Ok")))
	
			self.Sizer.append1x(box)
	
	class makeSizerTestPage(dabo.ui.dScrollPanel, EasyDialogBuilder):
		def afterInit(self):
			self.Sizer = self.setupStandardSizer()
			
			self.Sizer.append(dabo.ui.dLabel(self, Caption="Example using the function makeControlSizer", RegID="makeControlSizer_Label"), "normal")
			self.Sizer.appendSpacer(10)
			
			vs = self.makeControlSizer(self, 
						((dabo.ui.dTextBox, "txtCounty2", "County"), 
						(dabo.ui.dTextBox, "txtCity2", "City"),
						(dabo.ui.dTextBox, "txtZipcode2", "Zip"),
						(dabo.ui.dSpinner, "spnPopulation2", "Population"),
						(dabo.ui.dCheckBox, "chkReviewed2", "Reviewed"),
						(dabo.ui.dEditBox, "edtComments2", "Comments"),
						(dabo.ui.dSlider, "sldFactor2", "Factor"),
						("File", "txtFile", "Important File"),
						(dabo.ui.dButton, "cmdOk2", "Ok")))
			
			self.Sizer.append1x(vs)

	app = dabo.dApp()
	app.MainFormClass = TestForm
	app.start()