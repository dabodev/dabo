import wx
import dabo
import dabo.ui
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
from dabo.dLocalize import _


class dLed(dabo.ui.dPanel):
	def afterInit(self):
		self._offColor = "darkred"
		self._onColor = "green"
		self._on = False
		self.Buffered = True
		self.led = self.drawCircle(1,1,1)
		self.led.DynamicXpos = self.setXPos
		self.led.DynamicYpos = self.setYPos
		self.led.DynamicRadius = self.setRadius
		self.led.DynamicFillColor = self.setFillColor
		self.update()
	

	def onResize(self, evt):
		"""Update the size of the LED."""
		self.update()

		
	# Methods for the dynamic properties
	def setXPos(self):
		return self.Width /2
	def setYPos(self):
		return self.Height /2
	def setRadius(self):
		return (min(self.Width, self.Height)) /2
	def setFillColor(self):
		return self.Color
		

	# Getters and Setters
	def _getColor(self):
		if self._on:
			return self._onColor
		else:
			return self._offColor
			
	def _getOffColor(self):
		return self._offColor
	
	def _setOffColor(self, val):
		self._offColor = val
		self.update()
	
	def _getOn(self):
		return self._on
	
	def _setOn(self, val):
		self._on = val
		self.update()
	
	def _getOnColor(self):
		return self._onColor
	
	def _setOnColor(self, val):
		self._onColor = val
		self.update()
	
	
	# Property Definitions
	Color = property(_getColor, None, None,
		_("The color of the LED (color)"))

	OffColor = property(_getOffColor, _setOffColor, None,
		_("The color of the LED when it is off.  (color)"))
	
	On = property(_getOn, _setOn, None,
		_("Is the LED is on? Default=False  (bool)"))
	
	OnColor = property(_getOnColor, _setOnColor, None,
		_("The color of the LED when it is on.  (color)"))



class TestForm(dabo.ui.dForm):
	def afterInit(self):
		mp = dabo.ui.dPanel(self)
		self.Sizer.append1x(mp)
		mp.Sizer = dabo.ui.dSizer("h")
		mp.Sizer.append1x(dLed(self, RegID="LED"))
		
		vs = dabo.ui.dSizer("v", DefaultBorder=20)
		vs.appendSpacer(20)
		vs.DefaultBorderLeft = vs.DefaultBorderRight = True
		btn = dabo.ui.dToggleButton(mp, Caption="Toggle LED",
				DataSource=self.LED, DataField="On", Value=False)
		vs.append(btn)
		vs.appendSpacer(12)
		vs.append(dabo.ui.dLabel(mp, Caption="On Color:"))
		dd = dabo.ui.dDropdownList(mp, Choices=dabo.dColors.colors,
				DataSource=self.LED, DataField="OnColor", Value="green")
		vs.append(dd)
		vs.appendSpacer(12)
		vs.append(dabo.ui.dLabel(mp, Caption="Off Color:"))
		dd = dabo.ui.dDropdownList(mp, Choices=dabo.dColors.colors,
				DataSource=self.LED, DataField="OffColor", Value="darkred")
		vs.append(dd)
		mp.Sizer.append(vs)
		
		self.LED.On = True
		
		self.layout()
		

if __name__ == '__main__':
	app = dabo.dApp()
	app.MainFormClass = TestForm
	app.start()
