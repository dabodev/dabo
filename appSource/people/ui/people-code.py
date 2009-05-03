# -*- coding: utf-8 -*-
### Dabo Class Designer code. You many freely edit the code,
### but do not change the comments containing:
### 		'Dabo Code ID: XXXX', 
### as these are needed to link the code to the objects.

## *!* ## Dabo Code ID: dLabel-dPage
def afterInit(self):
	self.DynamicCaption = self.Form.getIncidentLabel



## *!* ## Dabo Code ID: dButton-dPage
def onHit(self, evt):
	self.Form.search()



## *!* ## Dabo Code ID: dDropdownList-dPage-196
def afterInit(self):
	self.PositionValue = 0



## *!* ## Dabo Code ID: dDropdownList-dPage
def afterInit(self):
	self.PositionValue = 1



## *!* ## Dabo Code ID: dLabel-dForm
def afterInit(self):
	pass



## *!* ## Dabo Code ID: dButton-dForm-102
def onHit(self, evt):
	self.Form.cancel()



## *!* ## Dabo Code ID: dButton-dForm
def onHit(self, evt):
	self.Form.save()



## *!* ## Dabo Code ID: dTextBox-dPage
def onKeyChar(self, evt):
	if evt.keyCode == 13:
		self.Form.search()



## *!* ## Dabo Code ID: dForm-top
def afterInitAll(self):
	self.searchText.setFocus()


def createBizobjs(self):
	cxn = self.Application.getConnectionByName("people")
	peopleBizobj = self.Application.biz.PeopleBizobj(cxn)
	self.addBizobj(peopleBizobj)

	activitiesBizobj = self.Application.biz.ActivitiesBizobj(cxn)
	self.addBizobj(activitiesBizobj)
	peopleBizobj.addChild(activitiesBizobj)


def getIncidentLabel(self):
	biz = self.PrimaryBizobj
	try:
		return "Incidents for: %s, %s" % (biz.getFieldVal("lastname"), biz.getFieldVal("firstname"))
	except dabo.dException.NoRecordsException:
		return ""


def search(self):
	txt = self.searchText.Value
	if not txt:
		self.searchText.setFocus()
		return
	fld = {"Last Name": "lastname", "First Name": "firstname"}[self.searchFld.StringValue]
	opstring = self.searchOp.StringValue
	if opstring == "Equals":
		op = "="
	else:
		op = "ilike"
		if opstring.startswith("Starts"):
			txt = "%s%%" % txt
		elif opstring.startswith("Ends"):
			txt = "%%%s" % txt
		else:
			# Contains
			txt = "%%%s%%" % txt
	
	biz = self.PrimaryBizobj
	whr = " %s %s %%s " % (fld, op)
	biz.setWhereClause(whr)
	biz.setParams((txt,))
	self.requery()
	cnt = biz.RowCount
	if not cnt:
		dabo.ui.info("No matches found for '%s'." % txt, "Nothing matched")
	else:
		biz.RowNumber = 0
		self.update()



## *!* ## Dabo Code ID: dButton-dForm-750
def onHit(self, evt):
	self.Form.reload()


