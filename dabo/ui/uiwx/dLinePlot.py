# -*- coding: utf-8 -*-
import wx
import wx.lib.plot as plot

try:
	import numpy.oldnumeric as _Numeric
except ImportError:
	_Numeric = False
except StandardError, e:
	# Report the error, and abandon the import
	dabo.log.error(_("Error importing numpy.oldnumeric: %s") % e)
	_Numeric = False

import dabo
from dabo.ui import makeDynamicProperty
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlMixin as cm
from dabo.dLocalize import _
from dabo.lib.utils import ustr



class _TraceMixin(object):
		#Property Getters and Setters
	def _getCaption(self):
		return self.attributes['legend']

	def _setCaption(self, val):
		self.attributes['legend'] = ustr(val)


	def _getPoints(self):
		return self._points

	def _setPoints(self, val):
		for point in val:
			if not ((point is tuple) and (len(point) == 2)):
				raise ValueError('Points must be tuples of length 2')


	def _getTraceColor(self):
		return self.attributes['colour']

	def _setTraceColor(self, val):
		self.attributes['colour'] = val


	def _getTraceWidth(self):
		return self.attributes['width']

	def _setTraceWidth(self, val):
		self.attributes['width'] = int(val)


	#Property Definitions
	Caption = property(_getCaption, _setCaption, None,
			_("The caption in the legend (default='') (str)"))

	Points = property(_getPoints, _setPoints, None,
			_("The points that are plotted on the trace (list)"))

	TraceColor = property(_getTraceColor, _setTraceColor, None,
			_("The color of the plotted trace.  Must be a wx.NamedColour (default='black') (str)"))

	TraceWidth = property(_getTraceWidth, _setTraceWidth, None,
			_("The width of the plotted trace (default=1) (int)"))



class PlotLine(_TraceMixin, plot.PolyLine):
	def __init__(self, *args, **kwargs):
		self._lineStyle = "solid"
		plot.PolyLine.__init__(self, *args, **kwargs)


	#Property Getters and Setters
	def _getLineStyle(self):
		return self._lineStyle

	def _setLineStyle(self, val):
		if val in ['solid', 'dot', 'dash']:
			self.attributes['style'] = dict(solid=wx.SOLID, dot=wx.DOT, dash=wx.DOT_DASH)[val]
			self._lineStyle = val
		else:
			raise ValueError("LineStyle must be either 'solid', 'dash', or 'dot'")


	#Property Definitions
	LineStyle = property(_getLineStyle, _setLineStyle, None,
			_("The drawn style of the plotted line (default='solid') ('solid', 'dot', or 'dash')"))



class PlotMarkers(_TraceMixin, plot.PolyMarker):
	def __init__(self, *args, **kwargs):
		self._fillStyle = "solid"
		plot.PolyMarker.__init__(self, *args, **kwargs)


	#Property getters and setters
	def _getFillStyle(self):
		return self._fillStyle

	def _setFillStyle(self, val):
		if val in ['solid', 'empty']:
			self.attributes['style'] = dict(solid=wx.SOLID, empty=wx.TRANSPARENT)[val]
			self._fillStyle = val
		else:
			raise ValueError("LineStyle must be either 'solid' or 'empty'")


	def _getMarkerShape(self):
		return self.attributes['marker']

	def _setMarkerShape(self, val):
		if val in ['circle', 'dot', 'square', 'triangle', 'triangle_down', 'cross', 'plus']:
			self.attributes['marker'] = val
		else:
			raise ValueError("MarkerShape must be either 'circle', 'dot', 'square', 'triangle', 'triangle_down', 'cross', or 'plus'")


	def _getMarkerSize(self):
		return self.attributes['size']

	def _setMarkerSize(self, val):
		self.attributes['size'] = int(val)


	#Property definitions
	FillStyle = property(_getFillStyle, _setFillStyle, None,
			_("The fill style for the marker (default='solid') ('solid' or 'empty')"))

	MarkerShape = property(_getMarkerShape, _setMarkerShape, None,
			_("""The style for the marker (default='circle) (str)

			The marker style can be any of the following:
				- 'circle'
				- 'dot'
				- 'square'
				- 'triangle'
				- 'triangle_down'
				- 'cross'
				- 'plus'"""))

	MarkerSize = property(_getMarkerSize, _setMarkerSize, None,
			_("The size of the marker (default=2) (int)"))



class dLinePlot(cm.dControlMixin, plot.PlotCanvas):
	"""Creates a panel that can load and display a line graph."""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		if not _Numeric:
			raise ImportError("numpy.oldnumeric is not present, so dLinePlot cannot instantiate.")
		self._plotManager = plot.PlotGraphics([])

		self._baseClass = dLinePlot
		plot.PlotCanvas.__init__(self, parent)
		name, _explicitName = self._processName(kwargs, self.__class__.__name__)
		cm.dControlMixin.__init__(self, name, properties=properties,
				attProperties=attProperties, _explicitName=_explicitName, *args, **kwargs)

		self.SetPointLabelFunc(self.DrawPointLabel)
		self.setDefaults()
		if self.Traces:
			self.Draw(self._plotManager)


	def appendLineFromEquation(self, equation, Start, End, points=1000.0, LineColor='black', LineStyle='solid',
				LineWidth=1, Caption=""):
		spacing = (float(End) - float(Start))/float(points)
		pointList = Start + (_Numeric.arange(points) * spacing)
		coordinates = []
		s = "value = %s" % equation
		for index in range(len(pointList)):
			exec(s % pointList[index])
			coordinates.append((pointList[index], value))
		self.appendLineFromPoints(coordinates, LineColor, LineStyle, LineWidth, Caption)


	def appendLineFromPoints(self, points, LineColor='black', LineStyle='solid', LineWidth=1, Caption=""):
		if Caption == "":
			Caption = "Line %s" % len(self.Traces)
		line = PlotLine(points, legend=Caption, colour=LineColor, width=LineWidth)
		line.LineStyle = LineStyle
		self.Traces.append(line)
		self.Redraw()


	def appendMarkerFromPoints(self, points, Color='black', MarkerShape='circle', Width=1,
				FillStyle='solid', MarkerSize=2, Caption=""):
		if Caption == "":
			Caption = "Set %s" % len(self.Traces)
		marker = PlotMarkers(points, legend=Caption, colour=Color, width=Width, marker=MarkerShape, size=MarkerSize)
		marker.FillStyle = FillStyle
		self.Traces.append(marker)
		self.Redraw()


	def OnSize(self,event):
		# The Buffer init is done here, to make sure the buffer is always
		# the same size as the Window
		Size  = self.canvas.GetClientSize()
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
		dc.SetBrush(wx.Brush( wx.BLACK, wx.SOLID ) )

		# scaled x,y of closest point
		sx, sy = mDataDict["scaledXY"]
		# 10by10 square centered on point
		dc.DrawRectangle(sx-5, sy-5, 10, 10)
		px,py = mDataDict["pointXY"]
		cNum = mDataDict["curveNum"]
		pntIn = mDataDict["pIndex"]
		legend = mDataDict["legend"]
		# make a string to display
		s = "Crv# %i, '%s', Pt. (%.2f,%.2f), PtInd %i" %(cNum, legend, px, py, pntIn)
		dc.DrawText(s, sx , sy+1)
		# -----------


	def setDefaults(self):
		self.SetFont(wx.Font(10,wx.SWISS,wx.NORMAL,wx.NORMAL))
		self.SetFontSizeAxis(10)
		self.SetFontSizeLegend(7)
		self.setLogScale((False,False))
		self.SetXSpec('auto')
		self.SetYSpec('auto')


	#Property getters and setters
	def _getAxisFontSize(self):
		return self._fontSizeAxis

	def _setAxisFontSize(self, val):
		if self._constructed():
			self._fontSizeAxis = int(val)
			self.Redraw()
		else:
			self._properties["AxisFontSize"] = val


	def _getCaption(self):
		return self._plotManager.getTitle()

	def _setCaption(self, val):
		if self._constructed():
			self._plotManager.setTitle(val)
			self.Redraw()
		else:
			self._properties["Caption"] = val


	def _getEnableDrag(self):
		return self._dragEnabled

	def _setEnableDrag(self, val):
		self.SetEnableDrag(val)


	def _getEnableZoom(self):
		return self._zoomEnabled

	def _setEnableZoom(self, val):
		self.SetEnableZoom(val)


	def _getFontSize(self):
		return self._fontSizeTitle

	def _setFontSize(self, val):
		self._fontSizeTitle = val


	def _getLegendFontSize(self):
		return self._fontSizeLegend

	def _setLegendFontSize(self, val):
		self._fontSizeLegend = int(val)
		self.Redraw()


	def _getLogScale(self):
		return self._logscale

	def _setLogScale(self, val):
		if self._constructed():
			self.setLogScale(val)
			self.Redraw()
		else:
			self._properties["LogScale"] = val


	def _getShowCaption(self):
		return self._titleEnabled

	def _setShowCaption(self, val):
		if self._constructed():
			self.SetEnableTitle(val)
		else:
			self._properties["ShowCaption"] = val


	def _getShowGrid(self):
		return self._gridEnabled

	def _setShowGrid(self, val):
		if self._constructed():
			return self.SetEnableGrid(val)
		else:
			self._properties["ShowGrid"] = val


	def _getShowLegend(self):
		return self._legendEnabled

	def _setShowLegend(self, val):
		if self._constructed():
			self.SetEnableLegend(val)
		else:
			self._properties["ShowLegend"] = val


	def _getShowPointLabel(self):
		return self._pointLabelEnabled

	def _setShowPointLabel(self, val):
		if self._constructed():
			self.SetEnablePointLabel = True
		else:
			self._properties["ShowPointLabel"] = val


	def _getShowScrollbars(self):
		return self.GetShowScrollbars()

	def _setShowScrollbars(self, val):
		if self._constructed():
			if val:
				self.SetShowScrollbars(True)
			else:
				self.SetShowScrollbars(False)
			self.Redraw()
		else:
			self._properties["ShowScrollbars"] = val


	def _getTraces(self):
		return self._plotManager.objects

	def _setTraces(self, val):
		self._plotManager.objects = val


	def _getUseScientificNotation(self):
		return self._useScientificNotation

	def _setUseScientificNotation(self, val):
		if self._constructed():
			if val:
				self._useScientificNotation = True
			else:
				self._useScientificNotation = False
			self.Redraw()
		else:
			self._properties["UseScientificNotation"] = val


	def _getXAxisLabel(self):
		return self._plotManager.getXLabel()

	def _setXAxisLabel(self, val):
		if self._constructed():
			self._plotManager.setXLabel(val)
			self.Redraw()
		else:
			self._properties["XAxisLabel"] = val


	def _getXAxisType(self):
		return self._xSpec

	def _setXAxisType(self, val):
		if self._constructed():
			if val in ['auto', 'min', 'none']:
				self._xSpec = val
				self.Redraw()
			else:
				raise ValueError("XAxisType must be either 'none', 'min', or 'auto'")
		else:
			self._properties["XAxisType"] = val


	def _getYAxisLabel(self):
		return self._plotManager.getYLabel()

	def _setYAxisLabel(self, val):
		if self._constructed():
			self._plotManager.setYLabel(val)
			self.Redraw()
		else:
			self._properties["YAxisLabel"] = val


	def _getYAxisType(self):
		return self._ySpec

	def _setYAxisType(self, val):
		if self._constructed():
			if val in ['auto', 'min', 'none']:
				self._ySpec = val
				self.Redraw()
			else:
				raise ValueError("YAxisType must be either 'none', 'min', or 'auto'")
		else:
			self._properties["YAxisType"] = val


	#Property definitions
	AxisFontSize = property(_getAxisFontSize, _setAxisFontSize, None,
			_("Font size of the axis labels (default=15) (int)"))

	Caption = property(_getCaption, _setCaption, None,
			_("Title of the graph (str)"))

	EnableDrag = property(_getEnableDrag, _setEnableDrag, None,
			_("Determines whether drag is enabled (bool)"))

	EnableZoom = property(_getEnableZoom, _setEnableZoom, None,
			_("Determines whether zoom is enabled"))

	FontSize = property(_getFontSize, _setFontSize, None,
			_("The font size of the caption"))

	LegendFontSize = property(_getLegendFontSize, _setLegendFontSize, None,
			_("Font size of the legend (default=7) (int)"))

	LogScale = property(_getLogScale, _setLogScale, None,
			_("Determines whether each axis is on a logscale (tuple)"))

	ShowCaption = property(_getShowCaption, _setShowCaption, None,
			_("Determines if the Caption is show (default=True) (bool)"))

	ShowGrid = property(_getShowGrid, _setShowGrid, None,
			_("Determines if grid lines are shown (default=False) (bool)"))

	ShowLegend = property(_getShowLegend, _setShowLegend, None,
			_("Determines if the legend is shown (default=False) (bool)"))

	ShowPointLabel = property(_getShowPointLabel, _setShowPointLabel, None,
			_("Determines if the point labels are shown (bool)"))

	ShowScrollbars = property(_getShowScrollbars, _setShowScrollbars, None,
			_("Determines if scrollbars are shown (default=False)  (bool)"))

	Traces = property(_getTraces, _setTraces, None,
			_("List of all of the traces currently being plotted (list)"))

	UseScientificNotation = property(_getUseScientificNotation, _setUseScientificNotation, None,
			_("Determines if scientific notation is used for the display (default=False) (bool)"))

	XAxisLabel = property(_getXAxisLabel, _setXAxisLabel, None,
			_("Label for the x-axis (string)"))

	XAxisType = property(_getXAxisType, _setXAxisType, None,
			_( """Defines x axis type. Can be 'none', 'min' or 'auto'
	where:
		'none' - shows no axis or tick mark values
		'min' - shows min bounding box values
		'auto' - rounds axis range to sensible values"""))

	YAxisLabel = property(_getYAxisLabel, _setYAxisLabel, None,
			_("Label for the y-axis (string)"))

	YAxisType = property(_getYAxisType, _setYAxisType, None,
			_( """defines y axis type. Can be 'none', 'min' or 'auto'
	where:
		'none' - shows no axis or tick mark values
		'min' - shows min bounding box values
		'auto' - rounds axis range to sensible values"""))



class _dLinePlot_test(dLinePlot):
	def initProperties(self):
		self.XAxisLabel = "X Axis"
		self.YAxisLabel = "Y Axis"
		self.Caption = "Title of Graph"


	def afterInit(self):
		# 1000 points cos function, plotted as blue line
		self.appendLineFromEquation("2*_Numeric.cos(%s)", 5, 10, Caption="Blue Line", LineWidth=2, LineColor="blue")

		line = []
		for i in range(10):
			line.append((i, float(i)/2))
		self.appendLineFromPoints(line)

		data1 = 2.*_Numeric.pi*_Numeric.arange(200)/200.
		data1.shape = (100, 2)
		data1[:,1] = _Numeric.sin(data1[:,0])
		self.appendMarkerFromPoints(data1, Caption='Green Markers', Color='green', MarkerShape='circle', MarkerSize=1)

		# A few more points...
		points = [(0., 0.), (_Numeric.pi/4., 1.), (_Numeric.pi/2, 0.), (3.*_Numeric.pi/4., -1)]
		self.appendMarkerFromPoints(points, Caption='Cross Legend', Color='blue', MarkerShape='cross')



if __name__ == "__main__":
	import test
	test.Test().runTest(_dLinePlot_test)
