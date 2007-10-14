# -*- coding: utf-8 -*-
"""This is a very simple demo designed to show a few things about 
Dabo programming:

- I've laid out the form using absolute positioning instead of sizers.
Nothing about Dabo requires sizers. The layout looks great on my 
OS X box; I'm sure it will look less ideal on other platforms.

- The EditBox is bound to a method of the form. Nothing in Dabo 
requires that you bind controls to fields in a database table. You 
can easily achieve highly interactive UIs by using the data binding
of controls.

- Note how simple it is to populate a list: just set the 'Choices' property
to the list containing the values you want, and it's done!

- Auto-binding of events: note that we're binding to the Hit events of
both the button and the dropdown list. Dabo resolves that by using the 
RegID property of those controls. This is a developer-definable label that
must be unique across a given form. You don't need to define them for all
controls; just for those you wish to reference. Given an event 'XXX',
creating an 'onXXX()' method in the form binds that method to the form's 
XXX event, but creating a method named 'onXXX_zzz()' binds that method 
to the XXX event of the object whose RegID ='zzz', no matter where on
the form that object exists.

- Calling the 'refresh()' method of a control will update that control with
its bound value. Calling 'refresh()' of the form will update all controls on 
the form.

"""

import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents


class DocStringForm(dabo.ui.dForm):
	def afterInit(self):
		self.Caption = "DocString Demo"
		self.Size = (660, 400)
		self.pnl = dabo.ui.dPanel(self)
		self.Sizer.append1x(self.pnl)
		
		self.btn = dabo.ui.dButton(self.pnl, Left=50, Top=50, RegID="button",
				Width=320, Caption="Click Me to Populate the Dropdown List")
		
		self.dd = dabo.ui.dDropdownList(self.pnl, Width=150, Left=50,
				Top=100, RegID="ddList")
				
		self.edt = dabo.ui.dEditBox(self.pnl, Width=360, Height=200,
				Left=250, Top=100, DataSource="form", 
				DataField="getdocstring")
		
		self.spnPos = dabo.ui.dSpinner(self.pnl, Left=50, Top=200,
				DataSource="ddList", DataField="PositionValue")
		
		lbl = dabo.ui.dLabel(self.pnl, Left=50, Top=180, 
				Caption="Selected Item")
	
	
	def onValueChanged_ddList(self, evt):
		"""Note: this will fire when the dropdown list is changed"""
#		self.refresh()
		self.update()


	def onHit_ddList(self, evt):
		"""Note: this will fire when the dropdown list is changed by the user."""
		# no need to do anything, though, because onValueChanged_ddList() will 
		# handle it...
		pass


	def onHit_button(self, evt):
		"""This populates the DropdownList control"""
		choices = [i for i in dir(self.btn) if not i[0].isupper()
				and i[0] != "_"]
		self.dd.Choices = choices
		self.spnPos.Max = len(self.dd.Choices)
		self.dd.PositionValue = 0


	def getdocstring(self):
		""" Return the docstring for the selected prop/method/attribute"""
		ret = ""
		val = self.dd.StringValue
		if val:
			try:
				ret = eval("self.btn.__class__.%s.__doc__" % val).replace("\t", "")
			except:
				ret = None
		if ret is None:
			ret = "-no docstring available-"
		return ret
		

def main():
	app = dabo.dApp()
	app.MainFormClass = DocStringForm
	app.start()

if __name__ == '__main__':
	main()

