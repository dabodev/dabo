# -*- coding: utf-8 -*-
import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _

try:
    import numpy.oldnumeric as _Numeric
except ImportError:
    _Numeric = None


from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer
from dabo.ui import dTextBox
from dabo.ui import dGridSizer
from dabo.ui import dBorderSizer


class TestPanel(dPanel):
    def afterInit(self):
        if not _Numeric:
            txt = _("The numpy oldnumeric module is not installed")
            dLabel(self, Caption=txt, FontSize=12, ForeColor="red")
            return
        self.linePlot = self.createLinePlot()
        sz = self.Sizer = dSizer("h")
        sz.append(self.createControlPanel(self.linePlot), "expand")
        sz.appendSpacer(10)
        sz.append1x(self.linePlot)

    def createControlPanel(self, linePlot):
        bs = dBorderSizer(self, Caption="Control Panel", orientation="v")
        gs = dGridSizer(MaxCols=2, HGap=5, VGap=5)
        gs.setColExpand(True, 1)

        txtTitle = dTextBox(self, DataSource=linePlot, DataField="Caption", Width=200)
        txtXAxisLabel = dTextBox(self, DataSource=linePlot, DataField="XAxisLabel")
        txtYAxisLabel = dTextBox(self, DataSource=linePlot, DataField="YAxisLabel")

        gs.append(dLabel(self, Caption="Title"), halign="right")
        gs.append(txtTitle, "expand")

        gs.append(dLabel(self, Caption="X Axis Label"), halign="right")
        gs.append(txtXAxisLabel, "expand")

        gs.append(dLabel(self, Caption="Y Axis Label"), halign="right")
        gs.append(txtYAxisLabel, "expand")

        bs.append(gs, "x")
        return bs

    def createLinePlot(self):
        linePlot = dLinePlot(self)
        linePlot.XAxisLabel = "X Axis"
        linePlot.YAxisLabel = "Y Axis"
        linePlot.Caption = "Title of Graph"

        # 1000 points cos function, plotted as blue line
        linePlot.appendLineFromEquation(
            "2*_Numeric.cos(%s)",
            5,
            10,
            Caption="Blue Line",
            LineWidth=2,
            LineColor="blue",
        )

        line = []
        for i in range(10):
            line.append((i, float(i) / 2))
        linePlot.appendLineFromPoints(line)

        data1 = 2.0 * _Numeric.pi * _Numeric.arange(200) / 200.0
        data1.shape = (100, 2)
        data1[:, 1] = _Numeric.sin(data1[:, 0])
        linePlot.appendMarkerFromPoints(
            data1,
            Caption="Green Markers",
            Color="green",
            MarkerShape="circle",
            MarkerSize=1,
        )

        # A few more points...
        points = [
            (0.0, 0.0),
            (_Numeric.pi / 4.0, 1.0),
            (_Numeric.pi / 2, 0.0),
            (3.0 * _Numeric.pi / 4.0, -1),
        ]
        linePlot.appendMarkerFromPoints(
            points, Caption="Cross Legend", Color="blue", MarkerShape="cross"
        )

        linePlot.Draw(linePlot._plotManager)

        return linePlot


category = "Controls.dLinePlot"

overview = """
<p><b>A Line Plot</b> allows you to present data in a graph form.  The graph can have
as many lines as necessary that can be generated either by an equation on by data points.
</p>

<p><b>dLinePlot</b> is the class that controlls this. The user can
control a multitude of properties include label content and apperance, placement
of different components of the graph, title and legend information, and much
more.  The Apperance of the graph can be completely customized within Dabo.</p>
"""
