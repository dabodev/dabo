# -*- coding: utf-8 -*-
import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _


from dabo.ui import dLabel
from dabo.ui import dPanel

from dabo.ui import dSpinner
from dabo.ui import dDropdownList
from dabo.ui import dGridSizer
from dabo.ui import dCheckBox

dSizer = dabo.ui.dSizer


class TestPanel(dPanel):
    def afterInit(self):
        # First, divide the form into 4 vertical sections:
        # Top: visual display
        # Middle 1: Individual sizer controls
        # Middle 2: Overall sizer controls
        # Bottom: Close button
        self.Sizer = sz = dSizer("v", DefaultBorder=5, DefaultBorderAll=True)
        dispPanel = dPanel(self, BackColor="wheat")
        sz.append(dispPanel, 2, "x")
        self.displaySizer = ds = dSizer("h")
        dispPanel.Sizer = ds
        # Append the displaySizer  to the main sizer, giving
        # it a weight of 2, and have it expand to fill the horizontal space.

        # Create 3 panels. Give each a default height/weight of 10 so that
        # they are still visible when 'expand' is set to 0 or weight is 0.
        self.leftPanel = lp = dPanel(
            dispPanel,
            BackColor="red",
            Name="RedPanel",
            BorderWidth=1,
            Height=10,
            Width=10,
        )
        self.middlePanel = mp = dPanel(
            dispPanel,
            BackColor="green",
            Name="GreenPanel",
            BorderWidth=1,
            Height=10,
            Width=10,
        )
        self.rightPanel = rp = dPanel(
            dispPanel,
            BackColor="blue",
            Name="BluePanel",
            BorderWidth=1,
            Height=10,
            Width=10,
        )
        # Add them to the display sizer, giving each equal weight, and
        # having each expand to fill the opposite direction. Normally, you
        # would write sz.append(obj, 1, "expand") for each, but there is a
        # convenience method 'append1x' that eliminates the need for
        # the last two parameters.
        ds.append1x(lp)
        ds.append1x(mp)
        ds.append1x(rp)

        # OK, now we need to add the controls
        self.controlSizer = cs = dSizer("h")
        self.leftControls = lc = SizerController(self)
        self.middleControls = mc = SizerController(self)
        self.rightControls = rc = SizerController(self)
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
        self.ddOrientation = dDropdownList(self, Choices=["Vertical", "Horizontal"])
        self.ddOrientation.StringValue = self.displaySizer.Orientation
        self.ddOrientation.bindEvent(dEvents.Hit, self.onOrientationChange)
        hsz = dSizer("h")
        hsz.append(dLabel(self, Caption=_("Orientation:")), valign="Middle")
        hsz.appendSpacer(4)
        hsz.append(self.ddOrientation)
        sz.appendSpacer(10)
        sz.append(hsz, 0, halign="center")

        # OK, everything is added, so let's lay 'em out!
        self.layout()

    def onOrientationChange(self, evt):
        self.displaySizer.Orientation = self.ddOrientation.StringValue
        self.Form.logit(_("Overall Orientation changed to %s") % self.displaySizer.Orientation)
        self.layout()


class SizerController(dPanel):
    """This class will contain several controls designed to be
    manipulated by the user in order to visually change the
    behavior of a specified sizer.
    """

    def afterInit(self):
        # Holds a reference to the target this set of controls will affect.
        # This will be set at runtime.
        self._target = None
        # Create a grid sizer with 2 columns
        self.Sizer = sz = dGridSizer(MaxCols=2)

        # Add a heading
        self.lblHeading = dLabel(self, FontBold=True)
        sz.append(self.lblHeading, colSpan=2, halign="center")

        # Add a labeled spinner to affect proportion
        sz.append(dLabel(self, Caption=_("Proportion:")), halign="right")
        self.proportionSpinner = dSpinner(self, Min=0, Max=10)
        self.proportionSpinner.bindEvent(dEvents.Hit, self.onProportionChange)
        sz.append(self.proportionSpinner)

        # Add a checkbox to affect the Expand setting
        sz.append(dLabel(self, Caption=_("Expand?")), halign="right")
        self.expandChk = dCheckBox(self, Caption="")
        self.expandChk.bindEvent(dEvents.Hit, self.onExpandChange)
        sz.append(self.expandChk)

        # Add a spinner to set the Border
        sz.append(dLabel(self, Caption=_("Border:")), halign="right")
        self.borderSpinner = dSpinner(self, Min=0, Max=100, Value=1)
        self.borderSpinner.bindEvent(dEvents.Hit, self.onBorderChange)
        sz.append(self.borderSpinner)

        # Add a dropdown to select Horiz. and Vert. alignment
        sz.append(dLabel(self, Caption=_("Horiz. Align:")), halign="right")
        self.ddHAlign = dDropdownList(self, ValueMode="String", Choices=["Left", "Center", "Right"])
        self.ddHAlign.bindEvent(dEvents.Hit, self.onAlignChange)
        self.ddHAlign.sizerProp = "HAlign"
        sz.append(self.ddHAlign)
        sz.append(dLabel(self, Caption=_("Vert. Align:")), halign="right")
        self.ddVAlign = dDropdownList(self, ValueMode="String", Choices=["Top", "Middle", "Bottom"])
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
        nm = self.Target.Name
        self.Form.logit(_("%(nm)s.%(prop)s changed to '%(val)s'") % locals())

    def onProportionChange(self, evt):
        tsi = self.Target.ControllingSizerItem
        ts = self.Target.ControllingSizer
        if ts is None:
            return
        val = self.proportionSpinner.Value
        ts.setItemProp(tsi, "Proportion", val)
        self.Form.layout()
        nm = self.Target.Name
        self.Form.logit(_("%(nm)s.Proportion changed to '%(val)s'") % locals())

    def onBorderChange(self, evt):
        tsi = self.Target.ControllingSizerItem
        ts = self.Target.ControllingSizer
        if ts is None:
            return
        val = self.borderSpinner.Value
        ts.setItemProp(tsi, "Border", val)
        self.Form.layout()
        nm = self.Target.Name
        self.Form.logit(_("%(nm)s.Border changed to '%(val)s'") % locals())

    def onExpandChange(self, evt):
        tsi = self.Target.ControllingSizerItem
        ts = self.Target.ControllingSizer
        if ts is None:
            return
        val = self.expandChk.Value
        ts.setItemProp(tsi, "Expand", val)
        self.Form.layout()
        nm = self.Target.Name
        self.Form.logit(_("%(nm)s.Expand changed to '%(val)s'") % locals())

    def _setCaption(self, val):
        self.lblHeading.Caption = val

    def _getTarget(self):
        return self._target

    def _setTarget(self, val):
        self._target = val
        cs = val.ControllingSizer
        csi = val.ControllingSizerItem
        self.proportionSpinner.Value = cs.getItemProp(csi, "Proportion")
        self.expandChk.Value = cs.getItemProp(csi, "Expand")
        self.borderSpinner.Value = cs.getItemProp(csi, "Border")
        self.ddHAlign.Value = cs.getItemProp(csi, "HAlign")
        self.ddVAlign.Value = cs.getItemProp(csi, "VAlign")

    Caption = property(None, _setCaption)
    Target = property(_getTarget, _setTarget)


category = "Layout.dSizer"

overview = """
<p><b>dSizer</b> is the basic one-dimensional sizer for laying out items either
horizontally or vertically. You add controls to the sizer, which then takes care of
determining their relative sizes and positions.</p>

<p>The primary means for adding items to the sizer are its <b>append()</b> and
<b>insert()</b> methods. There is also a convenience method named
<b>append1x()</b>, which is a shorthand for append(<i>item</i>, 1, "x"),
which itself is a shorthand for adding an item with a Proportion of 1 and
set to Expand in the non-sizer direction.</p>
"""
