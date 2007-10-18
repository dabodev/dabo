# -*- coding: utf-8 -*-
import dabo
import dabo.dEvents as dEvents

dabo.ui.loadUI("wx")

class MyButton(dabo.ui.dButton):
	def onHit(self, evt):
		print "MyButton.Hit"


class MyPanel(dabo.ui.dPanel):
	def initProperties(self):
		self.BackColor = self.mainColor = "lightblue"
		self.Size = (100, 50)

	def onMouseEnter(self, evt):
		self.BackColor = "yellow"
		print "MyPanel.MouseEnter"

	def onMouseLeave(self, evt):
		self.BackColor = self.mainColor
		print "MyPanel.MouseLeave"

	def onHit_btn1(self, evt):
		print "panel: btn1 hit!"


class MyForm(dabo.ui.dForm):
	def initProperties(self):
		self.Caption = "autoBindEvents() Demo"

	def afterInit(self):
		self.addObject(MyPanel, RegID="pan1")
		self.pan1.addObject(MyButton, Caption="Hit me!", RegID="btn1")
		# Note that underscores *are* just fine in the RegID:
		btn2 = self.addObject(dabo.ui.dButton, Caption="Hello!", Top=100)
		btn2.RegID = "btn2_test_underscores"
		
	def onActivate(self, evt):
		print "MyForm.Activate"

	def onDeactivate(self, evt):
		print "MyForm.Deactivate"

	def onHit_btn1(self, evt):
		print "form: onHit_btn1"

	def onHit_btn2_test_underscores(self, evt):
		print "form: onHit_btn2_test_underscores"


if __name__ == "__main__":
	app = dabo.dApp(MainFormClass=None)
	app.setup()
	app.MainForm = MyForm()
	app.start()
