import wx
import dabo
import dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

from dabo.dLocalize import _
from dPemMixin import DrawObject

class dLed(dabo.ui.dPanel):
	def afterInit(self):
		self._offColor = "darkred"
		self._onColor = "green"
		self._on = False
		self.Size = (200, 200)
		self.drawRectangle(0,0,2,2)		#NWL: This is here so the led can be redrawn during resize
										#I needed at least one object in the draw objects list....
	
	def callAfterInit(self):
		self._redraw()
	
	def redraw(self, dc):
		self.ClearBackground()
		
		if self.On:
			fillColor = self.OnColor
		else:
			fillColor = self.OffColor
		
		obj = DrawObject(self, FillColor=fillColor, PenColor="black",
				PenWidth=1, Radius= min(self.Size[0], self.Size[1])/2, LineStyle=None, 
				Shape="circle", Xpos=self.Size[0]/2, Ypos=self.Size[1]/2, DrawMode=None)
		
		obj.draw(dc)
		
	# Getters and Setters
	def _getOffColor(self):
		return self._offColor
	
	def _setOffColor(self, val):
		self._offColor = val
		if not self.On:
			self._redraw()
	
	def _getOn(self):
		return self._on
	
	def _setOn(self, val):
		if val:
			self._on = True
		else:
			self._on = False
		
		self._redraw()
	
	def _getOnColor(self):
		return self._onColor
	
	def _setOnColor(self, val):
		self._onColor = val
		if self.On:
			self._redraw()
	
	
	# Property Definitions
	OffColor = property(_getOffColor, _setOffColor, None,
		_("The color of the LED when it is off. (default = 'darkred')"))
	
	On = property(_getOn, _setOn, None,
		_("Boolean on wether or not the LED is on. (default = False)"))
	
	OnColor = property(_getOnColor, _setOnColor, None,
		_("The color of the LED when it is on. (default = 'green')"))


class TestForm(dabo.ui.dForm):
	def afterInit(self):
		self.Sizer = dabo.ui.dSizer(orientation="horizontal")
		
		self.Sizer.append1x(dLed(self, RegID="LED"))
		
		vs = dabo.ui.dSizer(orientation="vertical", DefaultBorder=10, DefaultBorderAll=True, DefaultSpacing=5)
		vs.append(dabo.ui.dButton(self, Caption="Toggle LED", RegID="button"), "normal")
		vs.append(dabo.ui.dLabel(self, Caption="On Color:"), "normal")
		vs.append(dabo.ui.dDropdownList(self, RegID="onColor", Choices=dabo.dColors.colorDict.keys()),"normal")
		vs.append(dabo.ui.dLabel(self, Caption="Off Color:"), "normal")
		vs.append(dabo.ui.dDropdownList(self, RegID="offColor", Choices=dabo.dColors.colorDict.keys()),"normal")
		
		self.Sizer.append(vs, "normal")
		self.Sizer.layout()
		
		self.onColor.Value = "green"
		self.offColor.Value = "darkred"
	
	def onHit_button(self, evt):
		if self.LED.On:
			self.LED.On = False
		else:
			self.LED.On = True
	
	def onHit_onColor(self, evt):
		pass
	
	def onHit_offColor(self, evt):
		pass
	
	def onValueChanged_onColor(self, evt):
		self.LED.OnColor = self.onColor.Value
	
	def onValueChanged_offColor(self, evt):
		self.LED.OffColor = self.offColor.Value

if __name__ == '__main__':
	app = dabo.dApp()
	app.MainFormClass = TestForm
	app.start()
