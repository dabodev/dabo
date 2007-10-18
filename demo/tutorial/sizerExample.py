# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents


class SizerController(dabo.ui.dPanel):
	""" This class will contain several controls designed to be
	manipulated by the user in order to visually change the 
	behavior of a specified sizer.
	"""
	def afterInit(self):
		# Holds a reference to the target this set of controls will affect.
		# This will be set at runtime.
		self._target = None
		# Create a grid sizer with 2 columns
		self.Sizer = sz = dabo.ui.dGridSizer(MaxCols=2)
		
		# Add a heading
		self.lblHeading = dabo.ui.dLabel(self, FontBold=True)
		sz.append(self.lblHeading, colSpan=2, halign="center")
		
		# Add a labeled spinner to affect weight
		sz.append(dabo.ui.dLabel(self, Caption="Weight:"), halign="right")
		self.weightSpinner = dabo.ui.dSpinner(self, Min=0, Max=10)
		self.weightSpinner.bindEvent(dEvents.Hit, self.onWeightChange)
		sz.append(self.weightSpinner)
		
		# Add a checkbox to affect the Expand setting
		sz.append(dabo.ui.dLabel(self, Caption="Expand?"), halign="right")
		self.expandChk = dabo.ui.dCheckBox(self, Caption="")
		self.expandChk.bindEvent(dEvents.Hit, self.onExpandChange)
		sz.append(self.expandChk)
		
		# Add a spinner to set the Border
		sz.append(dabo.ui.dLabel(self, Caption="Border:"), halign="right")
		self.borderSpinner = dabo.ui.dSpinner(self, Min=0, Max=100, Value=1)
		self.borderSpinner.bindEvent(dEvents.Hit, self.onBorderChange)
		sz.append(self.borderSpinner)

		# Add a dropdown to select Horiz. and Vert. alignment
		sz.append(dabo.ui.dLabel(self, Caption="Horiz. Align:"), halign="right")
		self.ddHAlign = dabo.ui.dDropdownList(self, ValueMode="String",
				Choices=["Left", "Center", "Right"])
		self.ddHAlign.bindEvent(dEvents.Hit, self.onAlignChange)
		self.ddHAlign.sizerProp = "HAlign"
		sz.append(self.ddHAlign)
		sz.append(dabo.ui.dLabel(self, Caption="Vert. Align:"), halign="right")
		self.ddVAlign = dabo.ui.dDropdownList(self, ValueMode="String",
				Choices=["Top", "Middle", "Bottom"])
		self.ddVAlign.bindEvent(dEvents.Hit, self.onAlignChange)
		self.ddVAlign.sizerProp = "VAlign"
		sz.append(self.ddVAlign)
		
	
	def onAlignChange(self, evt):
		tsi = self.Target.ControllingSizerItem
		ts = self.Target.ControllingSizer
		if ts is None:
			return
		obj = evt.EventObject
		val = obj.Value
		prop = obj.sizerProp
		ts.setItemProp(tsi, prop, val)
		self.Form.layout()
		
		
	def onWeightChange(self, evt):
		tsi = self.Target.ControllingSizerItem
		ts = self.Target.ControllingSizer
		if ts is None:
			return
		ts.setItemProp(tsi, "Proportion", self.weightSpinner.Value)
		self.Form.layout()
		
	
	def onBorderChange(self, evt):
		tsi = self.Target.ControllingSizerItem
		ts = self.Target.ControllingSizer
		if ts is None:
			return
		ts.setItemProp(tsi, "Border", self.borderSpinner.Value)
		self.Form.layout()
		
	
	def onExpandChange(self, evt):
		tsi = self.Target.ControllingSizerItem
		ts = self.Target.ControllingSizer
		if ts is None:
			return
		ts.setItemProp(tsi, "Expand", self.expandChk.Value)
		self.Form.layout()
		
	
	def _setCaption(self, val):
		self.lblHeading.Caption = val
		
	def _getTarget(self):
		return self._target
		
	def _setTarget(self, val):
		self._target = val
		cs = val.ControllingSizer
		csi = val.ControllingSizerItem
		self.weightSpinner.Value = cs.getItemProp(csi, "Proportion")
		self.expandChk.Value = cs.getItemProp(csi, "Expand")
		self.borderSpinner.Value = cs.getItemProp(csi, "Border")
		self.ddHAlign.Value = cs.getItemProp(csi, "HAlign")
		self.ddVAlign.Value = cs.getItemProp(csi, "VAlign")
		
	Caption = property(None, _setCaption)
	Target = property(_getTarget, _setTarget)
	
	
class SampleForm(dabo.ui.dForm):
	def afterInit(self):
		self.Caption = "Playing with Sizers"
		backPnl = self.backPanel = dabo.ui.dPanel(self)
		self.Sizer = dabo.ui.dSizer("v")
		self.Sizer.append1x(backPnl)
		
		# First, divide the form into 4 vertical sections:
		# Top: visual display
		# Middle 1: Individual sizer controls
		# Middle 2: Overall sizer controls
		# Bottom: Close button
		backPnl.Sizer = sz = dabo.ui.dSizer("v", DefaultBorder=5, DefaultBorderAll=True)
		dispPanel = dabo.ui.dPanel(backPnl, BackColor="wheat")
		sz.append(dispPanel, 2, "x")
		self.displaySizer = ds = dabo.ui.dSizer("h")
		dispPanel.Sizer = ds
		# Append the displaySizer  to the main sizer, giving
		# it a weight of 2, and have it expand to fill the horizontal space.
		
		# Create 3 panels. Give each a default height/weight of 10 so that 
		# they are still visible when 'expand' is set to 0 or weight is 0.
		self.leftPanel = lp = dabo.ui.dPanel(dispPanel, BackColor="red", 
				BorderWidth=1, Height=10, Width=10)
		self.middlePanel = mp = dabo.ui.dPanel(dispPanel, BackColor="green", 
				BorderWidth=1, Height=10, Width=10)
		self.rightPanel = rp = dabo.ui.dPanel(dispPanel, BackColor="blue", 
				BorderWidth=1, Height=10, Width=10)
		# Add them to the display sizer, giving each equal weight, and
		# having each expand to fill the opposite direction. Normally, you
		# would write sz.append(obj, 1, "expand") for each, but there is a
		# convenience method 'append1x' that eliminates the need for
		# the last two parameters.
		ds.append1x(lp)
		ds.append1x(mp)
		ds.append1x(rp)
		
		# OK, now we need to add the controls 
		self.controlSizer = cs = dabo.ui.dSizer("h")
		self.leftControls = lc = SizerController(backPnl)
		self.middleControls = mc = SizerController(backPnl)
		self.rightControls = rc = SizerController(backPnl)
		lc.Target = lp
		mc.Target = mp
		rc.Target = rp
		lc.Caption = "Red"
		mc.Caption = "Green"
		rc.Caption = "Blue"
		# When we'd like to append several items in a row, we can
		# pass them as a list/tuple, and they will get added in the order
		# they appear in that list/tuple.
		cs.appendItems((lc, mc, rc), 1, "x")
		sz.append(cs, 0, "x")
		
		# Add the Orientation selector
		self.ddOrientation = dabo.ui.dDropdownList(backPnl, RegID="ddOrient",
				Choices=["Vertical", "Horizontal"])
		self.ddOrientation.StringValue = self.displaySizer.Orientation
		hsz = dabo.ui.dSizer("h")
		hsz.append(dabo.ui.dLabel(backPnl, Caption="Orientation:"), valign="Middle")
		hsz.appendSpacer(4)
		hsz.append(self.ddOrientation)
		sz.appendSpacer(10)
		sz.append(hsz, 0, halign="center")
		
		# Add a button to close the form
		btn = dabo.ui.dButton(backPnl, Caption="OK", RegID="btnOK")
		sz.append(btn, 0, halign="right")
		
		# OK, everything is added, so let's lay 'em out!
		self.layout()
		
		
	def onHit_btnOK(self, evt):
		self.release()
		
	
	def onHit_ddOrient(self, evt):
		self.displaySizer.Orientation = self.ddOrientation.StringValue
		self.layout()
	
		
def main():
	app = dabo.dApp()
	app.MainFormClass = SampleForm
	app.start()
	
	
if __name__ == '__main__':
	main()

