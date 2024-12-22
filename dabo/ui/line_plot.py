# -*- coding: utf-8 -*-
import wx

from .. import application

dabo_module = settings.get_dabo_package()


try:
    import wx.lib.plot as plot
except ModuleNotFoundError:
    plot = None

try:
    # JFCS 11/5/2019 ADDED BELOW
    import numpy

    # numpy = numpy.oldnumeric
    ##import numpy.oldnumeric as numpy
except ImportError:
    numpy = False
except Exception as e:
    # Report the error, and abandon the import
    dabo_module.error(_("Error importing numpy.oldnumeric: %s") % e)
    numpy = False

from ..dLocalize import _
from ..lib.utils import ustr
from . import dControlMixin, makeDynamicProperty


class _TraceMixin(object):
    # Property Definitions
    @property
    def Caption(self):
        """The caption in the legend (default='') (str)"""
        return self.attributes["legend"]

    @Caption.setter
    def Caption(self, val):
        self.attributes["legend"] = ustr(val)

    @property
    def Points(self):
        """The points that are plotted on the trace (list)"""
        return self._points

    @Points.setter
    def Points(self, val):
        for point in val:
            if not ((point is tuple) and (len(point) == 2)):
                raise ValueError("Points must be tuples of length 2")

    @property
    def TraceColor(self):
        """The color of the plotted trace. Must be a wx.NamedColour (default='black') (str)"""
        return self.attributes["colour"]

    @TraceColor.setter
    def TraceColor(self, val):
        self.attributes["colour"] = val

    @property
    def TraceWidth(self):
        """The width of the plotted trace (default=1) (int)"""
        return self.attributes["width"]

    @TraceWidth.setter
    def TraceWidth(self, val):
        self.attributes["width"] = int(val)


class PlotLine(_TraceMixin, plot.PolyLine):
    def __init__(self, *args, **kwargs):
        self._lineStyle = "solid"
        plot.PolyLine.__init__(self, *args, **kwargs)

    # Property Definitions
    @property
    def LineStyle(self):
        """The drawn style of the plotted line (default='solid') ('solid', 'dot', or 'dash')"""
        return self._lineStyle

    @LineStyle.setter
    def LineStyle(self, val):
        if val in ["solid", "dot", "dash"]:
            self.attributes["style"] = dict(
                solid=wx.PENSTYLE_SOLID, dot=wx.PENSTYLE_DOT, dash=wx.PENSTYLE_DOT_DASH
            )[val]
            self._lineStyle = val
        else:
            raise ValueError("LineStyle must be either 'solid', 'dash', or 'dot'")


class PlotMarkers(_TraceMixin, plot.PolyMarker):
    def __init__(self, *args, **kwargs):
        self._fillStyle = "solid"
        plot.PolyMarker.__init__(self, *args, **kwargs)

    # Property definitions
    @property
    def FillStyle(self):
        """The fill style for the marker (default='solid') ('solid' or 'empty')"""
        return self._fillStyle

    @FillStyle.setter
    def FillStyle(self, val):
        if val in ["solid", "empty"]:
            self.attributes["style"] = dict(solid=wx.PENSTYLE_SOLID, empty=wx.PENSTYLE_TRANSPARENT)[
                val
            ]
            self._fillStyle = val
        else:
            raise ValueError("LineStyle must be either 'solid' or 'empty'")

    @property
    def MarkerShape(self):
        """
        The style for the marker (default='circle) (str)

        The marker style can be any of the following:
            - 'circle'
            - 'dot'
            - 'square'
            - 'triangle'
            - 'triangle_down'
            - 'cross'
            - 'plus'
        """
        return self.attributes["marker"]

    @MarkerShape.setter
    def MarkerShape(self, val):
        if val in [
            "circle",
            "dot",
            "square",
            "triangle",
            "triangle_down",
            "cross",
            "plus",
        ]:
            self.attributes["marker"] = val
        else:
            raise ValueError(
                "MarkerShape must be either 'circle', 'dot', 'square', 'triangle', "
                "'triangle_down', 'cross', or 'plus'"
            )

    @property
    def MarkerSize(self):
        """The size of the marker (default=2) (int)"""
        return self.attributes["size"]

    @MarkerSize.setter
    def MarkerSize(self, val):
        self.attributes["size"] = int(val)


class dLinePlot(dControlMixin, plot.PlotCanvas):
    """Creates a panel that can load and display a line graph."""

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        if not numpy:
            raise ImportError("numpy.oldnumeric is not present, so dLinePlot cannot instantiate.")
        self._plotManager = plot.PlotGraphics([])

        self._baseClass = dLinePlot
        plot.PlotCanvas.__init__(self, parent)
        name, _explicitName = self._processName(kwargs, self.__class__.__name__)
        dControlMixin.__init__(
            self,
            name,
            properties=properties,
            attProperties=attProperties,
            _explicitName=_explicitName,
            *args,
            **kwargs,
        )

        self.SetPointLabelFunc(self.DrawPointLabel)
        self.setDefaults()
        if self.Traces:
            self.Draw(self._plotManager)

    def appendLineFromEquation(
        self,
        equation,
        Start,
        End,
        points=1000.0,
        LineColor="black",
        LineStyle="solid",
        LineWidth=1,
        Caption="",
    ):
        spacing = (float(End) - float(Start)) / float(points)
        pointList = Start + (numpy.arange(points) * spacing)
        coordinates = []
        s = "value = %s" % equation
        for index in range(len(pointList)):
            exec(s % pointList[index])
            # coordinates.append((pointList[index], value))
            coordinates.append((pointList[index]))
        self.appendLineFromPoints(coordinates, LineColor, LineStyle, LineWidth, Caption)

    def appendLineFromPoints(
        self, points, LineColor="black", LineStyle="solid", LineWidth=1, Caption=""
    ):
        if Caption == "":
            Caption = "Line %s" % len(self.Traces)
        line = PlotLine(points, legend=Caption, colour=LineColor, width=LineWidth)
        line.LineStyle = LineStyle
        self.Traces.append(line)
        self.Redraw()

    def appendMarkerFromPoints(
        self,
        points,
        Color="black",
        MarkerShape="circle",
        Width=1,
        FillStyle="solid",
        MarkerSize=2,
        Caption="",
    ):
        if Caption == "":
            Caption = "Set %s" % len(self.Traces)
        marker = PlotMarkers(
            points,
            legend=Caption,
            colour=Color,
            width=Width,
            marker=MarkerShape,
            size=MarkerSize,
        )
        marker.FillStyle = FillStyle
        self.Traces.append(marker)
        self.Redraw()

    def OnSize(self, event):
        # The Buffer init is done here, to make sure the buffer is always
        # the same size as the Window
        Size = self.canvas.GetClientSize()
        Size.width = max(1, Size.width)
        Size.height = max(1, Size.height)

        # Make new offscreen bitmap: this bitmap will always have the
        # current drawing in it, so it can be used to save the image to
        # a file, or whatever.
        self._Buffer = wx.EmptyBitmap(Size.width, Size.height)
        plot.PlotCanvas._setSize(self)
        # Reset PointLable
        self.last_PointLabel = None

        if self.last_draw is None:
            self.Clear()
        else:
            self.Draw(self._plotManager)

    def DrawPointLabel(self, dc, mDataDict):
        """
        This is the fuction that defines how the pointLabels are plotted

            dc - DC that will be passed
            mDataDict - Dictionary of data that you want to use for the pointLabel

            As an example I have decided I want a box at the curve point
            with some text information about the curve plotted below.
            Any wxDC method can be used.
        """
        # ----------
        dc.SetPen(wx.Pen(wx.BLACK))
        dc.SetBrush(wx.Brush(wx.BLACK, wx.PENSTYLE_SOLID))

        # scaled x,y of closest point
        sx, sy = mDataDict["scaledXY"]
        # 10by10 square centered on point
        dc.DrawRectangle(round(sx - 5), round(sy - 5), 10, 10)
        px, py = mDataDict["pointXY"]
        cNum = mDataDict["curveNum"]
        pntIn = mDataDict["pIndex"]
        legend = mDataDict["legend"]
        # make a string to display
        s = "Crv# %i, '%s', Pt. (%.2f,%.2f), PtInd %i" % (cNum, legend, px, py, pntIn)
        dc.DrawText(s, int(sx), int(sy) + 1)
        # -----------

    def setDefaults(self):
        self.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL))
        self.SetFontSizeAxis(10)
        self.SetFontSizeLegend(7)
        self.setLogScale((False, False))
        self.SetXSpec("auto")
        self.SetYSpec("auto")

    # Property definitions
    @property
    def AxisFontSize(self):
        """Font size of the axis labels (default=15) (int)"""
        return self._fontSizeAxis

    @AxisFontSize.setter
    def AxisFontSize(self, val):
        if self._constructed():
            self._fontSizeAxis = int(val)
            self.Redraw()
        else:
            self._properties["AxisFontSize"] = val

    @property
    def Caption(self):
        """Title of the graph (str)"""
        return self._plotManager.getTitle()

    @Caption.setter
    def Caption(self, val):
        if self._constructed():
            self._plotManager.setTitle(val)
            self.Redraw()
        else:
            self._properties["Caption"] = val

    @property
    def EnableDrag(self):
        """Determines whether drag is enabled (bool)"""
        return self._dragEnabled

    @EnableDrag.setter
    def EnableDrag(self, val):
        self.SetEnableDrag(val)

    @property
    def EnableZoom(self):
        """Determines whether zoom is enabled"""
        return self._zoomEnabled

    @EnableZoom.setter
    def EnableZoom(self, val):
        self.SetEnableZoom(val)

    @property
    def FontSize(self):
        """The font size of the caption"""
        return self._fontSizeTitle

    @FontSize.setter
    def FontSize(self, val):
        self._fontSizeTitle = val

    @property
    def LegendFontSize(self):
        """Font size of the legend (default=7) (int)"""
        return self._fontSizeLegend

    @LegendFontSize.setter
    def LegendFontSize(self, val):
        self._fontSizeLegend = int(val)
        self.Redraw()

    @property
    def LogScale(self):
        """Determines whether each axis is on a logscale (tuple)"""
        return self._logscale

    @LogScale.setter
    def LogScale(self, val):
        if self._constructed():
            self.setLogScale(val)
            self.Redraw()
        else:
            self._properties["LogScale"] = val

    @property
    def ShowCaption(self):
        """Determines if the Caption is shown (default=True) (bool)"""
        return self._titleEnabled

    @ShowCaption.setter
    def ShowCaption(self, val):
        if self._constructed():
            self.SetEnableTitle(val)
        else:
            self._properties["ShowCaption"] = val

    @property
    def ShowGrid(self):
        """Determines if grid lines are shown (default=False) (bool)"""
        return self._gridEnabled

    @ShowGrid.setter
    def ShowGrid(self, val):
        if self._constructed():
            return self.SetEnableGrid(val)
        else:
            self._properties["ShowGrid"] = val

    @property
    def ShowLegend(self):
        """Determines if the legend is shown (default=False) (bool)"""
        return self._legendEnabled

    @ShowLegend.setter
    def ShowLegend(self, val):
        if self._constructed():
            self.SetEnableLegend(val)
        else:
            self._properties["ShowLegend"] = val

    @property
    def ShowPointLabel(self):
        """Determines if the point labels are shown (bool)"""
        return self._pointLabelEnabled

    @ShowPointLabel.setter
    def ShowPointLabel(self, val):
        if self._constructed():
            self.SetEnablePointLabel = True
        else:
            self._properties["ShowPointLabel"] = val

    @property
    def ShowScrollbars(self):
        """Determines if scrollbars are shown (default=False)  (bool)"""
        return self.GetShowScrollbars()

    @ShowScrollbars.setter
    def ShowScrollbars(self, val):
        if self._constructed():
            if val:
                self.SetShowScrollbars(True)
            else:
                self.SetShowScrollbars(False)
            self.Redraw()
        else:
            self._properties["ShowScrollbars"] = val

    @property
    def Traces(self):
        """List of all of the traces currently being plotted (list)"""
        return self._plotManager.objects

    @Traces.setter
    def Traces(self, val):
        self._plotManager.objects = val

    @property
    def UseScientificNotation(self):
        """Determines if scientific notation is used for the display (default=False) (bool)"""
        return self._useScientificNotation

    @UseScientificNotation.setter
    def UseScientificNotation(self, val):
        if self._constructed():
            if val:
                self._useScientificNotation = True
            else:
                self._useScientificNotation = False
            self.Redraw()
        else:
            self._properties["UseScientificNotation"] = val

    @property
    def XAxisLabel(self):
        """Label for the x-axis (string)"""
        return self._plotManager.getXLabel()

    @XAxisLabel.setter
    def XAxisLabel(self, val):
        if self._constructed():
            self._plotManager.setXLabel(val)
            self.Redraw()
        else:
            self._properties["XAxisLabel"] = val

    @property
    def XAxisType(self):
        """
        Defines x axis type. Can be 'none', 'min' or 'auto' where:
            'none' - shows no axis or tick mark values
            'min' - shows min bounding box values
            'auto' - rounds axis range to sensible values
        """
        return self._xSpec

    @XAxisType.setter
    def XAxisType(self, val):
        if self._constructed():
            if val in ["auto", "min", "none"]:
                self._xSpec = val
                self.Redraw()
            else:
                raise ValueError("XAxisType must be either 'none', 'min', or 'auto'")
        else:
            self._properties["XAxisType"] = val

    @property
    def YAxisLabel(self):
        """Label for the y-axis (string)"""
        return self._plotManager.getYLabel()

    @YAxisLabel.setter
    def YAxisLabel(self, val):
        if self._constructed():
            self._plotManager.setYLabel(val)
            self.Redraw()
        else:
            self._properties["YAxisLabel"] = val

    @property
    def YAxisType(self):
        """
        Defines y axis type. Can be 'none', 'min' or 'auto' where:
            'none' - shows no axis or tick mark values
            'min' - shows min bounding box values
            'auto' - rounds axis range to sensible values
        """
        return self._ySpec

    @YAxisType.setter
    def YAxisType(self, val):
        if self._constructed():
            if val in ["auto", "min", "none"]:
                self._ySpec = val
                self.Redraw()
            else:
                raise ValueError("YAxisType must be either 'none', 'min', or 'auto'")
        else:
            self._properties["YAxisType"] = val


ui.dLinePlot = dLinePlot


class _dLinePlot_test(dLinePlot):
    def initProperties(self):
        self.XAxisLabel = "X Axis"
        self.YAxisLabel = "Y Axis"
        self.Caption = "Title of Graph"

    def afterInit(self):
        # 1000 points cos function, plotted as blue line
        self.appendLineFromEquation(
            "2* numpy.cos(%s)",
            5,
            10,
            Caption="Blue Line",
            LineWidth=2,
            LineColor="blue",
        )

        line = []
        for i in range(10):
            line.append((i, float(i) / 2))
        self.appendLineFromPoints(line)

        data1 = 2.0 * numpy.pi * numpy.arange(200) / 200.0
        data1.shape = (100, 2)
        data1[:, 1] = numpy.sin(data1[:, 0])
        self.appendMarkerFromPoints(
            data1,
            Caption="Green Markers",
            Color="green",
            MarkerShape="circle",
            MarkerSize=1,
        )

        # A few more points...
        points = [
            (0.0, 0.0),
            (numpy.pi / 4.0, 1.0),
            (numpy.pi / 2, 0.0),
            (3.0 * numpy.pi / 4.0, -1),
        ]
        self.appendMarkerFromPoints(
            points, Caption="Cross Legend", Color="blue", MarkerShape="cross"
        )


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dLinePlot_test)
