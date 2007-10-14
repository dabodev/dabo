# -*- coding: utf-8 -*-
"""This is a very simple demo designed to show a few things about 
Dabo programming:

- This is identical to simpleDemo2, except that the spacing of the 
controls is handled by sizers instead of absolute positioning.

"""

import dabo
dabo.ui.loadUI("wx")


class DemoForm(dabo.ui.dForm):
	def afterInit(self):
		self.Caption = "Slider Demo"
		self.Size = (500, 260)
		
		dabo.ui.dLabel(self, Left=50, Top=50, Caption="Slider Value:", 
				FontSize=30, RegID="plainLabel", BackColor="palegreen")
		
		dabo.ui.dLabel(self, Left=300, Top=50, Caption="", 
				FontSize=30, ForeColor="blue", RegID="valueLabel",
				BackColor="lightsalmon")
		
		dabo.ui.dSlider(self, Min=0, Max=1000, ShowLabels=False,
			DataSource="valueLabel", DataField="Caption", 
			Left=50, Top=120, Width=400, RegID="bigSlider",
			BackColor="lightblue")

		self.bigSlider.Value = 42
		
		# Add the controls to the sizers. First, the form has a main
		# sizer. Make sure that it is vertical, and we'll divide it into 
		# two equal sections.
		self.Sizer.Orientation = "Vertical"
		
		# The top section will consist of the two labels arranged
		# side-by-side. So create a horizontal sizer to hold them
		hsz = dabo.ui.dSizer("h")
		hsz.append(self.plainLabel)
		hsz.append(self.valueLabel)
		# Now add this sizer to the main sizer. The '1' is the weight,
		# or proportion, that this element will be allotted when the
		# sizer determines how much vertical space to give each element.
		# The 'halign' says to horizontally align it in the center.
		self.Sizer.append(hsz, 1, halign="center")
		# Now add the slider. We also want to give this a weight of 1,
		# so that the labels and the slider each take up half of the 
		# vertical space, but we also want the slider to expand 
		# horizontally to fill up the availalble room. That's what the 
		# 'x' represents (you could also write 'expand').
		self.Sizer.append(self.bigSlider, 1, "x")
		# Now tell the form to determine sizes and positions
		self.layout()


def main():
	app = dabo.dApp()
	app.MainFormClass = DemoForm
	app.start()

if __name__ == '__main__':
	main()

