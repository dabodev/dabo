# -*- coding: utf-8 -*-
### Dabo Class Designer code. You many freely edit the code,
### but do not change the comments containing:
### 		'Dabo Code ID: XXXX', 
### as these are needed to link the code to the objects.

## *!* ## Dabo Code ID: dButton-dForm
def onHit(self, evt):
	self.Form.save()



## *!* ## Dabo Code ID: dButton-dPage
def onHit(self, evt):
	self.Form.search()



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


def search(self):
	txt = self.searchText.Value
	if not txt:
		self.searchText.setFocus()
		return
	self.PrimaryBizobj.setParams("%%%s%%" % txt)
	self.requery()



## *!* ## Dabo Code ID: dButton-dForm-905
def onHit(self, evt):
	self.Form.cancel()


