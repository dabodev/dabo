# -*- coding: utf-8 -*-
"""
File:			Conversion.py

Author:			Nathan Lowrie

Description:	This program will perform various conversions for different standard
	and non-standard units.  The aim is to demonstrate widget manipulation, Sizer
	layout, and modular panel design.
"""

import dabo
dabo.ui.loadUI('wx')

#They idea here is to take the lowest unit as a common denomonater.
#It's multiplier is 1, the rest are multiplier conversions for the
#smallest unit to the largest.  The actual conversion multiplier is 
#then calculated by taking Input_Multiplier/Output_Multiplier 
AccelerationDic = {"centigal": 10.0,
	"centimeter/square second": 1000.0,
	"decigal": 100.0,
	"decimeter/square second": 10000.0,
	"dekameter/square second": 1000000.0,
	"foot/square second": 30480.0,
	"g-unit (G)": 980665.0,
	"gal": 1000.0,
	"galileo": 1000.0,
	"gn": 980655.0,
	"grav": 980665.0,
	"hectometer/square second": 10000000.0,
	"inch/square second": 2540.0,
	"kilometer/hour second": 27777.7777778,
	"kilometer/square second": 100000000.0,
	"meter/square second": 100000.0,
	"mile/hour minute": 745.06666667,
	"mile/hour second": 44704.0,
	"mile/square second": 160934400.0,
	"milligal": 1.0,
	"millimeter/square second": 100.0}

AnglesDic = {"radial": 206264.8062471,
	"mil": 202.5,
	"grad": 3240.0,
	"degree": 3600.0,
	"minute": 60.0,
	"second": 1.0,
	"point": 40500.0,
	"1/16 Circle": 81000.0,
	"1/10 Circle": 129600.0,
	"1/8 Circle": 162000.0,
	"1/6 Circle": 216000.0,
	"1/4 Circle": 324000.0,
	"1/2 Circle": 648000.0,
	"Full Circle": 1296000.0}

AreasDic = {"Acre": 4046.8564224,
	"Acre [commercial]": 3344.50944,
	"Acre [survey]": 4046.87262672,
	"Acre [Ireland]": 6555.0,
	"Are": 100.0,
	"Arpent [Canada]": 3418.89,
	"barn": 10**-28,
	"bovate": 60000.0,
	"bunder": 10000.0,
	"caballeria [Spain/Peru]": 400000.0,
	"caballeria [Central America]": 450000.0,
	"caballeria [Cuba]": 134200.0,
	"carreau": 12900.0,
	"carucate": 486000.0,
	"hectare": 10000.0,
	"section": 2589998.5,
	"square": 9.290304,
	"square angstrom": 10**-20,
	"square astronomical unit": 2.2379523 * 10**22,
	"square centimeter": .0001,
	"square cubit": .20903184,
	"square decimeter": .01,
	"square dekameter": 100.0,
	"square foot": .09290304,
	"square hectometer": 10000.0,
	"square inch": .00064516,
	"square kilometer": 1000000.0,
	"square meter": 1.0,
	"square mile": 2589988.110336,
	"square millimeter": .000001,
	"square nanometer": 10**-18,
	"square yard": .83612736}

DistanceDic = {"centimeter": 10.0, 
	"feet": 304.8,
	"inch": 25.4,
	"kilometer": 1000000.0,
	"league": 4828041.7,
	"league [nautical]": 5556000.0,
	"meter": 1000.0,
	"mile": 1609344.0,
	"millimeter": 1.0,
	"yard": 914.4}

TemperatureDic = {"Celsius": 493.47,
	"Fahrenheit": 460.67,
	"Kelvin": 1.8,
	"Rankine": 1.0,
	"Reaumur": 493.92}

CategoryDic = {"Acceleration": AccelerationDic,
			   "Angles": AnglesDic,
			   "Area": AreasDic,
			   "Distance": DistanceDic,
			   "Temperature": TemperatureDic}

class conversionPanel(dabo.ui.dPanel):
	def afterInit(self):
		self.Sizer = vs = dabo.ui.dSizer("vertical")
		vs.DefaultBorder = 5
		vs.DefaultSpacing = 5
		vs.DefaultBorderAll = True
		
		self.ddCategory = dabo.ui.dDropdownList(self, RegID="ddCategory")
		self.lbInput = dabo.ui.dListBox(self, RegID="lbInput", DataSource="lblInputUnits", DataField="Caption")
		self.lbOutput = dabo.ui.dListBox(self, RegID="lbOutput", DataSource="lblOutputUnits", DataField="Caption")
		self.txtInputNum = dabo.ui.dTextBox(self, RegID="txtInputNum", Value="1")
		self.txtOutputNum = dabo.ui.dTextBox(self, RegID="txtOutputNum", ReadOnly=True)
		
		#layout category select
		bs = dabo.ui.dBorderSizer(self, "vertical", Caption="Category")
		bs.append1x(self.ddCategory)
		vs.append(bs, "expand")
		
		#layout input and output lists
		hs = dabo.ui.dSizer("horizontal")
		bs = dabo.ui.dBorderSizer(self, "vertical", Caption="Input")
		bs.append1x(self.lbInput)
		hs.append1x(bs)
		hs.appendSpacer(5)
		
		bs = dabo.ui.dBorderSizer(self, "vertical", Caption="Output")
		bs.append1x(self.lbOutput)
		hs.append1x(bs)
		vs.append1x(hs)
		
		#layout conversion textboxes
		bs = dabo.ui.dBorderSizer(self, "vertical", Caption="Category")
		gs = dabo.ui.dGridSizer(MaxCols=3)
		gs.setColExpand(True, 1)
		bs.append1x(gs)
		vs.append(bs, "expand")
		
		gs.append(dabo.ui.dLabel(self, Caption="Input:"), halign="right")
		gs.append(self.txtInputNum, "expand")
		gs.append(dabo.ui.dLabel(self, RegID="lblInputUnits", Width=200))
		gs.append(dabo.ui.dLabel(self, Caption="Output:"), halign="right")
		gs.append(self.txtOutputNum, "expand")
		gs.append(dabo.ui.dLabel(self, RegID="lblOutputUnits", Width=200))
		
		#Initialize Lists
		self.ddCategory.Choices = CategoryDic.keys()
		self.ddCategory.Value = CategoryDic.keys()[0]
		self.lbInput.Choices = CategoryDic[self.ddCategory.StringValue].keys()
		self.lbInput.Value = self.lbInput.Choices[0]
		self.lbOutput.Choices = CategoryDic[self.ddCategory.StringValue].keys()
		self.lbOutput.Value = self.lbOutput.Choices[0]
		
		self.convert()
	
	def convert(self):
		self.txtOutputNum.Value = float(self.txtInputNum.Value) * (CategoryDic[self.ddCategory.Value][self.lbInput.Value] / CategoryDic[self.ddCategory.Value][self.lbOutput.Value])

	
	#event handlers
	def onHit_lbInput(self, evt):
		self.convert()
	
	def onHit_lbOutput(self, evt):
		self.convert()
	
	def onHit_txtInputNum(self, evt):
		self.convert()
	
	def onHit_ddCategory(self, evt):
		self.lbInput.Choices = CategoryDic[self.ddCategory.StringValue].keys()
		self.lbInput.Value = self.lbInput.Choices[0]
		self.lbOutput.Choices = CategoryDic[self.ddCategory.StringValue].keys()
		self.lbOutput.Value = self.lbOutput.Choices[0]
		
		self.convert()


class mainForm(dabo.ui.dForm):
	def afterInit(self):
		self.Sizer = dabo.ui.dSizer("vertical")
		self.Sizer.append1x(conversionPanel(self))
		self.layout()

if __name__ == "__main__":
	app = dabo.dApp()
	app.MainFormClass = mainForm
	app.start()
