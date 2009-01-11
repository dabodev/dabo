# -*- coding: utf-8 -*-
### Dabo Class Designer code. You many freely edit the code,
### but do not change the comments containing:
### 		'Dabo Code ID: XXXX', 
### as these are needed to link the code to the objects.

## *!* ## Dabo Code ID: dListBox-dForm
def afterInit(self):
	self.DynamicWidth = lambda: .75 * self.Parent.Width



## *!* ## Dabo Code ID: dTextBox-dForm
def onKeyChar(self, evt):
	dabo.ui.callAfter(self.Form.onSearchTextKeyChar, evt)



## *!* ## Dabo Code ID: dButton-dForm
def onHit(self, evt):
	self.Form.requery()



## *!* ## Dabo Code ID: dForm-top
import dabo.dEvents as dEvents

def afterInitAll(self):
	dabo.ui.callAfter(self.layout)
	self.nameList.bindEvent(dEvents.Hit, self.onNameSelection)

def onNameSelection(self, evt):
	self.PrimaryBizobj.RowNumber = self.nameList.PositionValue
	self.update()

def afterRequery(self):
	names = self.PrimaryBizobj.getDataSet(flds=("id", "fullname"))
	self.nameList.Choices = [rec["fullname"] for rec in names]
	self.nameList.Keys = [rec["id"] for rec in names]
	dabo.ui.callAfterInterval(100, self.update)
	dabo.ui.callAfterInterval(200, self.layout)

def beforeRequery(self):
	val = self.searchText.Value
	if not val:
		return False
	self.PrimaryBizobj.setWhereClause(" lastname like '%%%s%%' " % val)

def createBizobjs(self):
	cxn = self.Application.getConnectionByName("people")
	pbiz = self.Application.biz.PeopleBizobj(cxn)
	self.addBizobj(pbiz)
	abiz = self.Application.biz.ActivitiesBizobj(cxn)
	self.addBizobj(abiz)
	pbiz.addChild(abiz)

def onSearchTextKeyChar(self, evt):
	val = self.searchText.Value
	if evt.keyCode == 13 and val:
		self.requery()
	else:
		self.searchButton.Enabled = bool(val)

