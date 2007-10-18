# -*- coding: utf-8 -*-
"""This is a very simple demo designed to show a few things about 
Dabo programming:

- like the first demo, it uses absolute positioning instead of sizers. 
The position of the blue label will vary from platform to platform,
and if you change the size or face of the font for the labels, it will
look even worse. The next demo will be the same thing, but now 
adding simple sizers. 

- unlike the first demo, instead of storing references to controls in
form attributes (e.g., self.txtName = dabo.ui.dTextBox(...)), we can 
use the RegID of the control as if it were a form attribute. Note that
when the slider is created it is not assigned to a form att, but right
after that, the form sets the slider's value by referring to it as
'self.bigSlider'.

- The value of the slider is bound to the blue label by setting the 
DataSource for the slider to the label's RegID. RegIDs are powerful
and versatile for internal referencing.

"""

import dabo
dabo.ui.loadUI("wx")


class DemoForm(dabo.ui.dForm):
	def afterInit(self):
		self.Caption = "Slider Demo"
		self.Size = (500, 260)
		
		dabo.ui.dLabel(self, Left=50, Top=50, Caption="Slider Value:", 
				FontSize=30, BackColor="palegreen")
		
		dabo.ui.dLabel(self, Left=300, Top=50, Caption="", 
				FontSize=30, ForeColor="blue", RegID="valueLabel",
				BackColor="lightsalmon")
		
		dabo.ui.dSlider(self, Min=0, Max=1000, ShowLabels=False,
			DataSource="valueLabel", DataField="Caption", 
			Left=50, Top=120, Width=400, RegID="bigSlider",
			BackColor="lightblue")
		
		self.bigSlider.Value = 42


def main():
	app = dabo.dApp()
	app.MainFormClass = DemoForm
	app.start()

if __name__ == '__main__':
	main()

