# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")

print "Type 'This dabo thing rules!' in the textbox..."

class FrmTest(dabo.ui.dForm):
	def afterInit(self):
		self.Caption = "Type 'This dabo thing rules!' in the textbox..."
		self.addObject(dabo.ui.dTextBox, Name="txtTest", Width=200)
		self.txtTest.DynamicFontItalic = self.dynFontItalic
		self.txtTest.DynamicFontBold = self.dynFontBold
		self.tmr = dabo.ui.callEvery(300, self. update)


	def dynFontBold(self):
		return "dabo" in self.txtTest.Value.lower()


	def dynFontItalic(self):
		return "rules" in self.txtTest.Value.lower()


app = dabo.dApp(MainFormClass=FrmTest).start()
