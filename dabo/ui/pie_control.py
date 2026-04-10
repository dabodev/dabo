import math

import wx
from wx.lib.agw.piectrl import PieCtrl, ProgressPie, PiePart

from . import dControlMixin
from . import dPemMixin
from .. import color_tools
from .. import ui
from ..localization import _


DUMMY_WEDGE_CAPTION = "Initial Wedge abcdefg"


class _LegendProxy:
    def __init__(self, control):
        self._control = control
        self._legend = control.GetLegend()

    @property
    def BackColor(self):
        return self._legend.GetBackColour()

    @BackColor.setter
    def BackColor(self, val):
        val = self._control.getWxColour(val)
        self._legend.SetBackColour(val)

    @property
    def FontBold(self):
        wxfont = self._legend.GetLabelFont()
        return wxfont.GetWeight() == wx.FONTWEIGHT_BOLD

    @FontBold.setter
    def FontBold(self, val):
        wxfont = self._legend.GetLabelFont()
        wxfont.SetWeight(wx.FONTWEIGHT_BOLD if val else wx.FONTWEIGHT_NORMAL)
        self._legend.SetFont(wxfont)

    @property
    def FontFace(self):
        wxfont = self._legend.GetLabelFont()
        return wxfont.GetFaceName()

    @FontFace.setter
    def FontFace(self, val):
        wxfont = self._legend.GetLabelFont()
        wxfont.SetFaceName(val)
        self._legend.SetFont(wxfont)

    @property
    def FontItalic(self):
        wxfont = self._legend.GetLabelFont()
        return wxfont.GetStyle() == wx.FONTSTYLE_ITALIC

    @FontItalic.setter
    def FontItalic(self, val):
        wxfont = self._legend.GetLabelFont()
        wxfont.SetStyle(wx.FONTSTYLE_ITALIC if val else wx.FONTSTYLE_NORMAL)
        self._legend.SetFont(wxfont)

    @property
    def FontSize(self):
        wxfont = self._legend.GetLabelFont()
        return wxfont.GetPointSize()

    @FontSize.setter
    def FontSize(self, val):
        wxfont = self._legend.GetLabelFont()
        wxfont.SetPointSize(val)
        self._legend.SetFont(wxfont)

    @property
    def FontUnderline(self):
        wxfont = self._legend.GetLabelFont()
        return wxfont.GetUnderlined()

    @FontUnderline.setter
    def FontUnderline(self, val):
        wxfont = self._legend.GetLabelFont()
        wxfont.SetUnderlined(val)
        self._legend.SetFont(wxfont)

    @property
    def ForeColor(self):
        return self._legend.GetLabelColour()

    @ForeColor.setter
    def ForeColor(self, val):
        val = self._control.getWxColour(val)
        self._legend.SetLabelColour(val)

    @property
    def Left(self):
        return self._legend.GetHorizontalBorder()

    @Left.setter
    def Left(self, val):
        self._legend.SetHorizontalBorder(val)

    @property
    def Top(self):
        return self._legend.GetVerticalBorder()

    @Top.setter
    def Top(self, val):
        self._legend.SetVerticalBorder(val)

    @property
    def Transparent(self):
        return self._legend.IsTransparent()

    @Transparent.setter
    def Transparent(self, val):
        self._legend.SetTransparent(val)

    @property
    def WindowStyle(self):
        return self._legend.GetWindowStyle()

    @WindowStyle.setter
    def WindowStyle(self, val):
        # Not used
        pass

    @property
    def Visible(self):
        return self._legend.IsShown()

    @Visible.setter
    def Visible(self, val):
        if val:
            self._legend.Show()
        else:
            self._legend.Hide()


class dPieWedge(dPemMixin, PiePart):
    def __init__(self, parent=None, *args, **kwargs):
        """These are not wx objects; they represent values, so no Parent is needed"""
        self._caption = "Wedge"
        self._value = 1
        if "Caption" not in kwargs:
            # Wedges need a caption to be rendered
            kwargs["Caption"] = _("-untitled-")
            print("Adding color:", kwargs["Caption"])
        if "Color" not in kwargs:
            # Wedges need a color to be rendered
            kwargs["Color"] = color_tools.randomColorName()
            print("Adding color:", kwargs["Color"])

        super().__init__(parent=None, *args, **kwargs)

    def __repr__(self):
        return f"Wedge '{self.Caption}'; Value={self.Value}"

    @property
    def Caption(self):
        return self._caption

    @Caption.setter
    def Caption(self, val):
        if self._constructed():
            self._caption = f"{val}"
            self.SetLabel(self._caption)
        else:
            self._properties["Caption"] = val

    @property
    def Color(self):
        return self.GetColour()

    @Color.setter
    def Color(self, val):
        if self._constructed():
            if isinstance(val, str):
                val = self.getWxColour(val)
            if val is None:
                self.SetColour(wx.NullColour)
            else:
                self.SetColour(val)
            # Background color changes don't result in an automatic refresh.
            self.refresh()
        else:
            self._properties["Color"] = val

    @property
    def Value(self):
        return self._value

    @Value.setter
    def Value(self, val):
        if self._constructed():
            self._value = val
            self.SetValue(val)
        else:
            self._properties["Value"] = val


class dPieControl(dControlMixin, PieCtrl):
    """Creates a pie-chart control that can be used to display relative values"""

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dPieControl
        self._legend_proxy = None
        self._use_degrees = True
        self._wedges = []

        preClass = PieCtrl

        dControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )
        if not self.Wedges:
            dummy = dPieWedge(Caption=DUMMY_WEDGE_CAPTION, Color="pink", Value=1)
            self.add_wedge(dummy)

    def create_wedge(self, value, caption=None, color=None):
        """creates a wedge with the passed values and adds it to the pie"""
        wedge = dPieWedge(Caption=caption, Color=color, Value=value)
        self.add_wedge(wedge)
        return wedge

    def add_wedge(self, wedge):
        if self._wedges and (self._wedges[0].Caption == DUMMY_WEDGE_CAPTION):
            self._wedges = [wedge]
            self._series.remove(self._series[0])
        else:
            self._wedges.append(wedge)
        self._series.append(wedge)
        self.Parent.layout()
        return wedge

    append_wedge = add_wedge

    def remove_wedge(self, wedge):
        if wedge not in self.Wedges:
            raise ValueError("The requested wedge is not part of this pie")
        self._wedges.remove(wedge)
        self._series.remove(wedge)
        self.Parent.layout()

    def hide_legend(self):
        self.Legend.Visible = False

    def show_legend(self):
        self.Legend.Visible = True

    # Property definitions
    @property
    def Legend(self):
        """Acts as a proxy between the pie control and its legend"""
        if self._legend_proxy is None:
            self._legend_proxy = _LegendProxy(self)
        return self._legend_proxy

    @property
    def RotationAngle(self):
        """The angle to rotate the pie"""
        rot = self.GetRotationAngle()
        return round(rot * (180 / math.pi)) if self.UseDegrees else rot

    @RotationAngle.setter
    def RotationAngle(self, val):
        if self._constructed():
            val = float(val)
            rad = (val * (math.pi / 180)) if self.UseDegrees else val
            self.SetRotationAngle(rad)
            self.Parent.layout()
        else:
            self._properties["RotationAngle"] = val

    @property
    def Thickness(self):
        """The thickness of the pie"""
        return self.GetHeight()

    @Thickness.setter
    def Thickness(self, val):
        if self._constructed():
            self.SetHeight(int(val))
            self.Parent.layout()
        else:
            self._properties["Thickness"] = val

    @property
    def TiltAngle(self):
        """
        The angle that the pie is tilted at.

        Ranges from 0.0 degrees (flat line; not interesting) to 90.0 degrees (full circle), or from
        0 to π/2 radians.
        """
        tilt = self.GetAngle()
        return round(tilt * (180 / math.pi)) if self.UseDegrees else tilt

    @TiltAngle.setter
    def TiltAngle(self, val):
        if self._constructed():
            val = float(val)
            rad = (val * (math.pi / 180)) if self.UseDegrees else val
            self.SetAngle(rad)
            self.Parent.layout()
        else:
            self._properties["TiltAngle"] = val

    @property
    def UseDegrees(self):
        """
        Determines if TiltAngle and RotationAngle values are interpreted as degrees (True)
        or radians (False)
        """
        return self._use_degrees

    @UseDegrees.setter
    def UseDegrees(self, val):
        if self._constructed():
            self._use_degrees = val
        else:
            self._properties["UseDegrees"] = val

    @property
    def Wedges(self):
        """
        The wedges represented in this pie.

        The wedges will all be instances of dPieWedge. If none are passed at creation, a single
        wedge will be added so that the control can render. Adding a wedge after will replace this
        placeholder wedge.
        """
        return self._wedges

    @Wedges.setter
    def Wedges(self, val):
        if self._constructed():
            if not all([isinstance(v, dPieWedge) for v in val]):
                raise ValueError("All wedges must be instances of dPieWedge")
            self._wedges = val
            self._series = val
            self.Parent.layout()
        else:
            self._properties["Wedges"] = val


ui.dPieControl = dPieControl
ui.dPieWedge = dPieWedge


class _dPieCtrl_test(dPieControl):
    def afterInit(self):
        self.Height = 300
        self.Width = 300
        self.Legend.Transparent = True
        self.Legend.HorizontalBorder = 10
        self.Legend.FontSize = 16
        self.Legend.FontFace = "Courier New"


if __name__ == "__main__":
    from ..application import dApp

    class PieControlTestForm(ui.dForm):
        def afterInit(self):
            self.Caption = "PieControl Test"
            pnl = ui.dPanel(self)
            self.Sizer.append1x(pnl)
            sz = pnl.Sizer = ui.dSizer("v")
            sz.appendSpacer(25)
            self.pie = _dPieCtrl_test(pnl)
            sz.append1x(self.pie, border=10)

            wedge1 = dPieWedge(Caption="First", Value=20, Color="red")
            self.pie.append_wedge(wedge1)
            wedge2 = dPieWedge(Caption="Second", Value=80, Color="green")
            self.pie.append_wedge(wedge2)
            wedge3 = dPieWedge(Caption="Third", Value=55, Color="blue")
            self.pie.append_wedge(wedge3)

            self.update()
            ui.callAfterInterval(200, self.layout)

    app = dApp(MainFormClass=PieControlTestForm)
    app.start()
