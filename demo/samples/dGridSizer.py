# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class TestPanel(dabo.ui.dPanel):
	def afterInit(self):
		sz = self.Sizer = dabo.ui.dSizer("V")
		sz.appendSpacer(50)

		intro = _("This demo shows the effect of the HGap and VGap properties on a GridSizer. "
				"The panel containing the grid sizer has a tan background, and the various controls "
				"in the sizer have a light blue background. These colors help you to visualize the effect "
				"of changing these properties.")
		cap = dabo.ui.dLabel(self, Caption=intro, Width=400, WordWrap=True)
		sz.append(cap, halign="center")
		sz.appendSpacer(25)

		# Create the grid sizer
		gridPanel = dabo.ui.dPanel(self, BackColor="moccasin")
		gs = self.gridSizer = gridPanel.Sizer = dabo.ui.dGridSizer(MaxCols=2, HGap=3, VGap=8)

		lbl = dabo.ui.dLabel(gridPanel, Caption="First", BackColor="powderblue")
		ctl = dabo.ui.dTextBox(gridPanel, BackColor="powderblue")
		gs.append(lbl, halign="right")
		gs.append(ctl)
		lbl = dabo.ui.dLabel(gridPanel, Caption="Second", BackColor="powderblue")
		ctl = dabo.ui.dTextBox(gridPanel, BackColor="powderblue")
		gs.append(lbl, halign="right")
		gs.append(ctl)
		lbl = dabo.ui.dLabel(gridPanel, Caption="Third", BackColor="powderblue")
		ctl = dabo.ui.dTextBox(gridPanel, BackColor="powderblue")
		gs.append(lbl, halign="right")
		gs.append(ctl)
		lbl = dabo.ui.dLabel(gridPanel, Caption="Fourth", BackColor="powderblue")
		ctl = dabo.ui.dTextBox(gridPanel, BackColor="powderblue")
		gs.append(lbl, halign="right")
		gs.append(ctl)

		hs = dabo.ui.dSizer("H")
		hs.append(gridPanel, valign="middle")

		gs = dabo.ui.dGridSizer(MaxCols=2)
		lbl = dabo.ui.dLabel(self, Caption=_("HGap:"))
		gs.append(lbl, halign="right")
		spn = dabo.ui.dSpinner(self, DataSource="self.Parent.gridSizer",
				DataField="HGap")
		spn.bindEvent(dEvents.Hit, self.onChangeLayout)
		gs.append(spn)

		lbl = dabo.ui.dLabel(self, Caption=_("VGap:"))
		gs.append(lbl, halign="right")
		spn = dabo.ui.dSpinner(self, DataSource="self.Parent.gridSizer",
				DataField="VGap")
		spn.bindEvent(dEvents.Hit, self.onChangeLayout)
		gs.append(spn)

		# Add this *before* the first grid sizer
		hs.prependSpacer(30)
		hs.insert(0, gs, valign="middle")
		# Now add the horizontal sizer to the main sizer for the panel.
		sz.append(hs, halign="center")
		# Call update() to set the controls' Value.
		self.update()


	def onChangeLayout(self, evt):
		self.layout()


category = "Layout.dGridSizer"

overview = """
<p><b>dGridSizer</b> is a two-dimensional sizer for laying out items in a grid
of rows and columns. You can specify a particular row/col position when you add
an item, or simply call '<b>append()</b>' and the grid will place it in the first
available cell.</p>

<p>The key properties to set are <b>MaxRows</b> and <b>MaxCols</b>.
You only set one or the other; what this tells the grid is how many rows/columns
to create before starting another row/col in the grid. Example: if you have a series of
controls that you want to add, and they consist of an identifying label and its
matching control, and you want them arranged in a grid with the label in the left
column and the control in the right column, simply set MaxCols to 2, and then append
label, control, label, control, label, control, etc., and the grid sizer will automatically
construct the appropriate grid.</p>

<p>Two other important properties are <b>HGap</b> and <b>VGap</b>, which control
the horizontal and vertical spacing between grid cells, respectively.</p>
"""