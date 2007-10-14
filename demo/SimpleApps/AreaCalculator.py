# -*- coding: utf-8 -*-
"""
File:			AreaCalculator.py

Author:			Nathan Lowrie

Description:	This file contains a GUI that calculates area for various geometries
	The purpose here is to demonstrate various GUI aspects like Sizers, DrawObjects,
	and event handling.
"""

import dabo
dabo.ui.loadUI('wx')

class AreaCalculatorForm(dabo.ui.dForm):
	def afterInit(self):
		self.Sizer = dabo.ui.dSizer("vertical")
		self.Panel = dabo.ui.dPanel(self)
		self.Sizer.append1x(self.Panel)
		
		self.Panel.Sizer = vs = dabo.ui.dSizer("vertical")
		vs.DefaultBorder = 5
		vs.DefaultSpacing = 10
		vs.DefaultBorderAll = True
		
		#Define input section
		bs = dabo.ui.dBorderSizer(self.Panel, "vertical", Caption="Geometry")
		gs = dabo.ui.dGridSizer(MaxCols=2)
		gs.setColExpand(True, 1)
		
		dabo.ui.dDropdownList(self.Panel, Choices=["Rectangle", "Circle", "Right Triangle"], Value="Rectangle", RegID="ddGeometry")
		dabo.ui.dTextBox(self.Panel, Value="1", RegID="txtOne")
		dabo.ui.dTextBox(self.Panel, Value="1", RegID="txtTwo")
		
		gs.append(dabo.ui.dLabel(self.Panel, Caption="Geometry"), halign="right")
		gs.append(self.ddGeometry, "expand")
		
		#Initally add Rectangle fields
		gs.append(dabo.ui.dLabel(self.Panel, Caption="Length", RegID="firstLabel"), halign="right")
		gs.append(self.txtOne, "expand")
		gs.append(dabo.ui.dLabel(self.Panel, Caption="Height", RegID="secondLabel"), halign="right")
		gs.append(self.txtTwo, "expand")
		
		bs.append1x(gs)
		vs.append(bs, "expand", halign="center")
		
		#define output section
		vs.append(dabo.ui.dLabel(self.Panel, Caption="Area: 1", RegID="lblArea", FontSize=25, ForeColor="Blue"))
		vs.append(dabo.ui.dLabel(self.Panel, Caption="Perimeter: 4", RegID="lblPerimeter", FontSize=25, ForeColor="Green"))
		vs.append1x(dabo.ui.dPanel(self.Panel, RegID="drawPanel"))
		
		self.drawObject = self.drawPanel.drawRectangle(5, 5, 5, 5, penColor="Green", penWidth=5, fillColor="Blue")
		self.drawObject.DynamicWidth = self.setWidth
		self.drawObject.DynamicHeight = self.setHeight
		
		
		self.Size = (200,200)
		self.update()
	
	#Methods for setting Dynamic Properties
	def setWidth(self):
		return self.drawPanel.Width - 10
	def setHeight(self):
		return self.drawPanel.Height - 10
	def setXPos(self):
		return self.drawPanel.Width /2
	def setYPos(self):
		return self.drawPanel.Height /2
	def setRadius(self):
		return (min(self.drawPanel.Width, self.drawPanel.Height)) /2
	def setPoints(self):
		return ((5,5), (5, self.drawPanel.Height - 5), (self.drawPanel.Width - 5, self.drawPanel.Height -5))
	
	#Misc. Class methods
	def calculate(self):
		if self.ddGeometry.StringValue == "Rectangle":
			Area =  float(self.txtOne.Value) * float(self.txtTwo.Value)
			Perimeter = (float(self.txtOne.Value) * 2) + (float(self.txtTwo.Value) * 2)
		elif self.ddGeometry.StringValue == "Circle":
			Area = float(self.txtOne.Value)**2 * 3.14159265
			Perimeter = float(self.txtOne.Value) * 2 * 3.14159265
		else:
			Area = float(self.txtOne.Value) * float(self.txtTwo.Value) / 2
			Perimeter = float(self.txtOne.Value) + float(self.txtTwo.Value) + (float(self.txtOne.Value) + float(self.txtTwo.Value))**.5
		
		self.lblArea.Caption = "Area: %s" % (Area,)
		self.lblPerimeter.Caption = "Perimeter: %s" % (Perimeter,)
	
	#Event Handlers
	def onResize(self, evt):
		"""Update the size of the geometry object."""
		self.clear()
		self.update()
	
	def onHit_txtOne(self, evt):
		self.calculate()
	
	def onHit_txtTwo(self, evt):
		self.calculate()
	
	def onHit_ddGeometry(self, evt):
		self.drawPanel.removeDrawnObject(self.drawObject)
		
		if self.ddGeometry.StringValue == "Rectangle":
			self.drawObject = self.drawPanel.drawRectangle(5, 5, 5, 5, penColor="Green", penWidth=5, fillColor="Blue")
			self.drawObject.DynamicWidth = self.setWidth
			self.drawObject.DynamicHeight = self.setHeight
			self.firstLabel.Caption = "Width:"
			self.secondLabel.Caption = "Height:"
			self.secondLabel.Visible = True
			self.txtTwo.Visible = True
		elif self.ddGeometry.StringValue == "Circle":
			self.drawObject = self.drawPanel.drawCircle(1, 1, 1, penColor="Green", penWidth=5, fillColor="Blue")
			self.drawObject.DynamicXpos = self.setXPos
			self.drawObject.DynamicYpos = self.setYPos
			self.drawObject.DynamicRadius = self.setRadius
			self.firstLabel.Caption = "Radius:"
			self.secondLabel.Visible = False
			self.txtTwo.Visible = False
		else:
			self.drawObject = self.drawPanel.drawPolygon(((1,1),(2,2),(3,3)), penColor="Green", penWidth=5, fillColor="Blue")
			self.drawObject.DynamicPoints = self.setPoints
			self.firstLabel.Caption = "Base:"
			self.secondLabel.Caption = "Height:"
			self.secondLabel.Visible = True
			self.txtTwo.Visible = True
		
		self.calculate()
		self.drawPanel.clear()
		self.drawPanel.update()


if __name__ == "__main__":
	app = dabo.dApp()
	app.MainFormClass = AreaCalculatorForm
	app.start()
