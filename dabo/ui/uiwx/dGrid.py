import sys
import datetime
import locale
import operator
import wx
import wx.grid
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
import dabo.dException as dException
from dabo.dLocalize import _, n_
import dControlMixin as cm
import dKeys
import dUICursors
import dabo.biz
import dabo.dColors as dColors
from dabo.dObject import dObject

# See if the new decimal module is present. This is necessary 
# because if running under Python 2.4 or later and using MySQLdb,
# some values will be returned as decimals, and we need to 
# conditionally convert them for display.
_USE_DECIMAL = True
try:
	from decimal import Decimal
except ImportError:
	_USE_DECIMAL = False


class dGridDataTable(wx.grid.PyGridTableBase):
	def __init__(self, parent):
		super(dGridDataTable, self).__init__()

		self.grid = parent
		self._initTable()


	def _initTable(self):
		self.colDefs = []
		self._oldRowCount = 0
		self.grid.setTableAttributes(self)


	def GetAttr(self, row, col, kind=0):
		## dColumn maintains one attribute object that applies to every row 
		## in the column. This can be extended later with optional cell-specific
		## attributes to override the column-specific ones, but I'll wait for
		## the need to present itself... perhaps we can implement a VFP-inspired
		## DynamicBackColor, DynamicFont..., etc.

		# I have no idea what the kind arg is for. It is sent by wxGrid to this
		# function, it always seems to be either 0 or 4, and it isn't documented in the 
		# wxWidgets docs (but it does appear in the wxPython method signature 
		# but still isn't documented there.)
#		if kind not in (0, 4):
#			# I'd like to know when kind isn't 0, to make sure I've covered all the
#			# bases. Well okay, it's really because I'm just curious.
#			dabo.infoLog.write("dGrid.Table.GetAttr:: kind is not 0, it is %s." % kind)

		## The column attr object is maintained in dColumn:
		try:
			dcol = self.grid.Columns[col]
			attr = dcol._gridColAttr.Clone()
		except IndexError:
			# Something is out of order in the setting up of the grid: the grid table
			# has columns, but self.grid.Columns doesn't know about it yet. Just return
			# the default:
			return self.grid._defaultGridColAttr.Clone()
			# (further testing reveals that this really isn't a problem: the grid is 
			#  just empty - no columns or rows added yet)

		## Now, override with a custom renderer for this row/col if applicable.
		## Note that only the renderer is handled here, as we are segfaulting when
		## handling the editor here.
		r = dcol.getRendererClassForRow(row)
		if r is not None:
			attr.SetRenderer(r())
		# Now check for alternate row coloration
		if self.alternateRowColoring:
			attr.SetBackgroundColour((self.rowColorEven, self.rowColorOdd)[row % 2])
		return attr


	def GetRowLabelValue(self, row):
		try:
			return self.grid.RowLabels[row]
		except:
			return ""
	

	def GetColLabelValue(self, col):
		# The column headers are painted when the wxGrid queries this method, as
		# this is the most appropriate time to do so. We return "" so that wx 
		# doesn't draw the string itself.
		self.grid._paintHeader(col)
		return ""
		
			
	def setColumns(self, colDefs):
		"""Create columns based on passed list of column definitions."""
		# Column order should already be in the definition. If there is a custom
		# setting by the user, override it.

		# See if the defs have changed. If not, update any column info,
		# and return. If so, clear the data to force a re-draw of the table.
		if colDefs == self.colDefs:
			self.setColumnInfo()
			return

		for idx, col in enumerate(colDefs):
			nm = col.DataField
			while not nm:
				nm = str(idx)
				idx += 1
				if nm in colDefs:
					nm = ""
			colName = "Column_%s" % nm
			app = self.grid.Application
			form = self.grid.Form
			pos = None
			if app is not None and form is not None and not app.isDesigner:
				pos = app.getUserSetting("%s.%s.%s.%s" % (
						form.Name, 
						self.grid.Name,
						colName,
						"Order"))
			if pos is not None:
				col.Order = pos

			# If the data types are actual types and not strings, convert
			# them to common strings.
			if isinstance(type(col.DataType), type):
				typeDict = {
						str : "string", 
						unicode : "unicode", 
						bool : "bool",
						int : "integer",
						float : "float", 
						long : "long", 
						datetime.date : "date", 
						datetime.datetime : "datetime", 
						datetime.time : "time" }
				if _USE_DECIMAL:
					typeDict[Decimal] = "decimal"
				try:
					col.DataType = typeDict[col.DataType]
				except: pass
				
		# Make sure that all cols have an Order set
		for num in range(len(colDefs)):
			col = colDefs[num]
			if col.Order < 0:
				col.Order = num
		colDefs.sort(self.orderSort)
		self.colDefs = colDefs
		self.setColumnInfo()
	
	def orderSort(self, col1, col2):
		return cmp(col1.Order, col2.Order)
		
		
	def setColumnInfo(self):
		self.colDefs.sort(self.orderSort)


	def convertType(self, typ):
		"""Convert common types, names and abbreviations for 
		data types into the constants needed by the wx.grid.
		"""
		# Default
		ret = wx.grid.GRID_VALUE_STRING
		if type(typ) == str:
			lowtyp = typ.lower()
		else:
			lowtyp = typ
			if _USE_DECIMAL:
				if typ is Decimal:
					lowtyp = "decimal"
		if lowtyp in (bool, "bool", "boolean", "logical", "l"):
			ret = wx.grid.GRID_VALUE_BOOL
		if lowtyp in (int, long, "int", "integer", "bigint", "i", "long"):
			ret = wx.grid.GRID_VALUE_NUMBER
		elif lowtyp in (str, unicode, "char", "varchar", "text", "c", "s"):
			ret = wx.grid.GRID_VALUE_STRING
		elif lowtyp in (float, "float", "f", "decimal"):
			ret = wx.grid.GRID_VALUE_FLOAT
		elif lowtyp in (datetime.date, datetime.datetime, datetime.time, 
				"date", "datetime", "time", "d", "t"):
			ret = wx.grid.GRID_VALUE_DATETIME
		return ret

	
	def CanGetValueAs(self, row, col, typ):
		if self.grid.useCustomGetValue:
			return self.grid.customCanGetValueAs(row, col, typ)
		else:
			dcol = self.grid.Columns[col]
			return typ == self.convertType(dcol.DataType)

	def CanSetValueAs(self, row, col, typ):
		if self.grid.useCustomSetValue:
			return self.grid.customCanSetValueAs(row, col, typ)
		else:
			dcol = self.grid.Columns[col]
			return typ == self.convertType(dcol.DataType)

		
	def fillTable(self, force=False):
		""" Fill the grid's data table to match the data set."""
		_oldRowCount = self._oldRowCount

		# Get the data from the grid.
		bizobj = self.grid.getBizobj()

		if bizobj:
			dataSet = bizobj
			_newRowCount = dataSet.RowCount
		else:
			dataSet = self.grid.DataSet
			if dataSet is None:
				return
			_newRowCount = len(dataSet)
			if _oldRowCount is None:
				## still haven't tracked down why, but bizobj grids needed _oldRowCount
				## to be initialized to None, or extra rows would be added. Since we
				## aren't a bizobj grid, we need to change that None to 0 here so that
				## the rows can get appended below.
				_oldRowCount = 0

		if _oldRowCount == _newRowCount and not force:
			return

		self.grid._syncRowCount()
		# Column widths come from multiple places. In decreasing precedence:
		#   1) dApp user settings, 
		#   2) col.Width (as set by the Width prop or by the fieldspecs)
		#   3) have the grid autosize

		self.grid.BeginBatch()
		for idx, col in enumerate(self.colDefs):
			fld = col.DataField
			colName = "Column_%s" % fld
			gridCol = idx
			fieldType = col.DataType.lower()
			app = self.grid.Application

			# 1) Try to get the column width from the saved user settings:
			width = None
			if app is not None and not app.isDesigner:
				width = app.getUserSetting("%s.%s.%s.%s" % (self.grid.Form.Name, 
						self.grid.Name, colName, 
						"Width"))

			if width is None:
				# 2) Try to get the column width from the column definition:
				width = col.Width

			if width is None or (width < 0):
				# 3) Have the grid autosize:
				self.grid.autoSizeCol(gridCol)
			else:
				col.Width = width
				#self.grid.SetColSize(gridCol, width)
			
		# Show the row labels, if any
		for idx, label in enumerate(self.grid.RowLabels):
			self.SetRowLabelValue(idx, label)
		self.grid.EndBatch()

		self._oldRowCount = _newRowCount

	
	# The following methods are required by the grid, to find out certain
	# important details about the underlying table.                
	def GetNumberRows(self):
		bizobj = self.grid.getBizobj()
		if bizobj:
			return bizobj.RowCount
		try:
			num = len(self.grid.DataSet)
		except:
			num = 0
		return num


	def GetNumberCols(self):
		return self.grid.ColumnCount


	def IsEmptyCell(self, row, col):
		if row >= self.grid.RowCount:
			return True

		bizobj = self.grid.getBizobj()
		field = self.grid.Columns[col].DataField
		if bizobj:
			if field:
				return not bizobj.getFieldVal(field, row)
			else:
				return True
		if field:
			ret = True
			try:
				rec = self.grid.DataSet[row]
				if rec and rec.has_key(field):
					ret = not self.grid.DataSet[row][field]
				return ret
			except: pass
			return ret
		return True


	def GetValue(self, row, col):
		if row >= self.grid.RowCount:
			return ""

		bizobj = self.grid.getBizobj()
		field = self.grid.Columns[col].DataField
		
		if bizobj:
			if field:
				return bizobj.getFieldVal(field, row)
			else:
				return ""
		try:
			ret = self.grid.DataSet[row][field]
		except:
			ret = ""
		return ret


	def SetValue(self, row, col, value):
		field = self.grid.Columns[col].DataField
		bizobj = self.grid.getBizobj()
		if bizobj:
			# make sure we are on the correct row already (we should be already):
			bizobj.RowNumber = row
			bizobj.setFieldVal(field, value)
		else:
			self.grid.DataSet[row][field] = value



class dColumn(dabo.ui.dPemMixinBase.dPemMixinBase):
	""" These aren't the actual columns that appear in the grid; rather,
	they provide a way to interact with the underlying grid table in a more
	straightforward manner.
	"""
	_call_beforeInit, _call_afterInit, _call_initProperties = False, True, True

	def __init__(self, parent, properties=None, *args, **kwargs):
		self._isConstructed = False
		self._beforeInit()
		kwargs["Parent"] = parent
		# dColumn maintains one attr object that the grid table will use:
		a = self._gridColAttr = parent._defaultGridColAttr.Clone()
		a.SetFont(self._getDefaultFont())

		super(dColumn, self).__init__(properties, *args, **kwargs)
		self._baseClass = dColumn


	def _beforeInit(self):
		super(dColumn, self)._beforeInit()
		# Define the cell renderer and editor classes
		import gridRenderers
		self.stringRendererClass = wx.grid.GridCellStringRenderer
		self.boolRendererClass = gridRenderers.BoolRenderer
		self.intRendererClass = wx.grid.GridCellNumberRenderer
		self.longRendererClass = wx.grid.GridCellNumberRenderer
		self.decimalRendererClass = wx.grid.GridCellNumberRenderer
		self.floatRendererClass = wx.grid.GridCellFloatRenderer
		self.listRendererClass = wx.grid.GridCellStringRenderer
		self.stringEditorClass = wx.grid.GridCellTextEditor
		self.boolEditorClass = wx.grid.GridCellBoolEditor
		self.intEditorClass = wx.grid.GridCellNumberEditor
		self.longEditorClass = wx.grid.GridCellNumberEditor
		self.decimalEditorClass = wx.grid.GridCellNumberEditor
		self.floatEditorClass = wx.grid.GridCellFloatEditor
		self.listEditorClass = wx.grid.GridCellChoiceEditor		
		
		self.defaultRenderers = {
			"str" : self.stringRendererClass, 
			"string" : self.stringRendererClass, 
			"bool" : self.boolRendererClass, 
			"int" : self.intRendererClass, 
			"long" : self.longRendererClass, 
			"decimal" : self.decimalRendererClass,
			"float" : self.floatRendererClass, 
			"list" : self.listRendererClass  }
		self.defaultEditors = {
			"str" : self.stringEditorClass, 
			"string" : self.stringEditorClass, 
			"bool" : self.boolEditorClass, 
			"int" : self.intEditorClass, 
			"long" : self.longEditorClass, 
			"decimal" : self.decimalEditorClass,
			"float" : self.floatEditorClass, 
			"list" : self.listEditorClass }
		

	def _afterInit(self):
		self._isConstructed = True
		super(dColumn, self)._afterInit()
		

	def _getDefaultFont(self):
		font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.LIGHT)
		if sys.platform[:3] == "win":
			# The wx default is quite ugly
			font.SetFaceName("Arial")
			font.SetPointSize(9)
		return font


	def _constructed(self):
		return self._isConstructed


	def _setEditor(self, row):
		"""Set the editor for the entire column based on the editor for this row.

		This is a workaround to a problem that is preventing us from setting the
		editor for a specific cell at the time the grid needs it.
		"""
		edClass = self.getEditorClassForRow(row)
		attr = self._gridColAttr.Clone()
		if edClass:
			kwargs = {}
			if edClass in (wx.grid.GridCellChoiceEditor,):
				kwargs["choices"] = self.getListEditorChoicesForRow(row)
			editor = edClass(**kwargs)
			attr.SetEditor(editor)
		self._gridColAttr = attr


	def getListEditorChoicesForRow(self, row):
		"""Return the list of choices for the list editor for the given row."""
		choices = self.CustomListEditorChoices.get(row)
		if choices is None:
			choices = self.ListEditorChoices
		return choices


	def getEditorClassForRow(self, row):
		"""Return the cell editor class for the passed row."""
		d = self.CustomEditors
		e = d.get(row)
		if e is None:
			e = self.EditorClass
		return e


	def getRendererClassForRow(self, row):
		"""Return the cell renderer class for the passed row."""
		d = self.CustomRenderers
		r = d.get(row)
		if r is None:
			r = self.RendererClass
		return r


	def _getHeaderRect(self):
		"""Return the rect of this header in the header window."""
		grid = self.Parent
		height = self.Parent.HeaderHeight
		width = self.Width
		top = 0

		# Thanks Roger Binns:
		left = -grid.GetViewStart()[0] * grid.GetScrollPixelsPerUnit()[0]

		for col in range(self.Parent.ColumnCount):
			colObj = self.Parent.Columns[col]
			if colObj == self:
				break
			left += colObj.Width

		return wx.Rect(left, top, width, height)


	def _refreshHeader(self):
		"""Refresh just this column's header."""
		if self.Parent:
			# This will trigger wx to query GetColLabelValue(), which will in turn
			# call paintHeader() on just this column. It's roundabout, but gives the
			# best overall results, but risks relying on wx implementation details. 
			# Other options, in case this starts to fail, are: 
			#		self.Parent.Header.Refresh()
			#		self.Parent._paintHeader(self._GridColumnIndex)
			self.Parent.SetColLabelValue(self._GridColumnIndex, "")


	def _refreshGrid(self):
		"""Refresh the grid region, not the header region."""
		if self.Parent:
			gw = self.Parent.GetGridWindow()
			gw.Refresh()


	def _persist(self, prop):
		"""Persist the current prop setting to the user settings table."""
		app = self.Application
		grid = self.Parent
		colName = "column_%s" % self.DataField
		val = getattr(self, prop)
		settingName = "%s.%s.%s.%s" % (grid.Form.Name, grid.Name, colName, prop)
		app.setUserSetting(settingName, val)


	def _getGridColumnIndex(self):
		"""Return our column index in the grid, or -1."""
		gridCol = -1
		try:
			grid = self.Parent
		except:
			grid = None
		if grid is not None:
			for idx, dCol in enumerate(grid.Columns):
				if dCol == self:
					gridCol = idx
					break
		return gridCol

	
	def _updateEditor(self):
		"""The Field, DataType, or CustomEditor has changed: set in the attr"""
		editorClass = self.EditorClass
		if editorClass is None:
			editor = None
		else:
			kwargs = {}
			if editorClass in (wx.grid.GridCellChoiceEditor,):
				kwargs["choices"] = self.ListEditorChoices
			editor = editorClass(**kwargs)
		self._gridColAttr.SetEditor(editor)


	def _updateRenderer(self):
		"""The Field, DataType, or CustomRenderer has changed: set in the attr"""
		rendClass = self.RendererClass
		if rendClass is None:
			renderer = None
		else:
			renderer = rendClass()
		self._gridColAttr.SetRenderer(renderer)
	

	def _getCaption(self):
		try:
			v = self._caption
		except AttributeError:
			v = self._caption = "Column"
		return v

	def _setCaption(self, val):
		if self._constructed():
			self._caption = val
			self._refreshHeader()
		else:
			self._properties["Caption"] = val


	def _getCustomEditorClass(self):
		try:
			v = self._customEditorClass
		except AttributeError:
			v = self._customEditorClass = None
		return v

	def _setCustomEditorClass(self, val):
		if self._constructed():
			self._customEditorClass = val
			self._updateEditor()
		else:
			self._properties["CustomEditorClass"] = val


	def _getCustomEditors(self):
		try:
			v = self._customEditors
		except AttributeError:
			v = self._customEditors = {}
		return v

	def _setCustomEditors(self, val):
		self._customEditors = val


	def _getCustomListEditorChoices(self):
		try:
			v = self._customListEditorChoices
		except AttributeError:
			v = self._customListEditorChoices = {}
		return v

	def _setCustomListEditorChoices(self, val):
		self._customListEditorChoices = val


	def _getCustomRendererClass(self):
		try:
			v = self._customRendererClass
		except AttributeError:
			v = self._customRendererClass = None
		return v

	def _setCustomRendererClass(self, val):
		if self._constructed():
			self._customRendererClass = val
			self._updateRenderer()
		else:
			self._properties["CustomRendererClass"] = val


	def _getCustomRenderers(self):
		try:
			v = self._customRenderers
		except AttributeError:
			v = self._customRenderers = {}
		return v

	def _setCustomRenderers(self, val):
		self._customRenderers = val


	def _getDataType(self):
		try:
			v = self._dataType
		except AttributeError:
			v = self._dataType = ""
		return v

	def _setDataType(self, val):
		if self._constructed():
			self._dataType = val
			if "Automatic" in self.HorizontalAlignment:
				self._setAutoHorizontalAlignment()
			self._updateRenderer()
			self._updateEditor()
		else:
			self._properties["DataType"] = val


	def _getEditable(self):
		return not self._gridColAttr.IsReadOnly()

	def _setEditable(self, val):
		if self._constructed():
			self._gridColAttr.SetReadOnly(not val)
			if self.Parent:
				self.Parent.refresh()
		else:
			self._properties["Editable"] = val			


	def _getEditorClass(self):
		v = self.CustomEditorClass
		if v is None:
			v = self.defaultEditors.get(self.DataType)
		return v


	def _getDataField(self):
		try:
			v = self._dataField
		except AttributeError:
			v = self._dataField = ""
		return v

	def _setDataField(self, val):
		if self._constructed():
			self._dataField = val
			if not self.Name or self.Name == "?":
				self._name = _("col_%s") % val
			self._updateRenderer()
			self._updateEditor()
		else:
			self._properties["DataField"] = val


	def _getFont(self):
		return self._gridColAttr.GetFont()
	
	def _setFont(self, val):
		if self._constructed():
			assert isinstance(val, wx.Font)
			self._gridColAttr.SetFont(val)
			self._refreshGrid()
		else:
			self._properties["Font"] = val

	
	def _getFontBold(self):
		return self.Font.GetWeight() == wx.BOLD
	
	def _setFontBold(self, val):
		if self._constructed():
			font = self.Font
			if val:
				font.SetWeight(wx.BOLD)
			else:
				font.SetWeight(wx.LIGHT)
			self.Font = font
		else:
			self._properties["FontBold"] = val

	def _getFontDescription(self):
		f = self.Font
		ret = f.GetFaceName() + " " + str(f.GetPointSize())
		if f.GetWeight() == wx.BOLD:
			ret += " B"
		if f.GetStyle() == wx.ITALIC:
			ret += " I"
		return ret
	
	def _getFontInfo(self):
		return self.Font.GetNativeFontInfoDesc()

		
	def _getFontItalic(self):
		return self.Font.GetStyle() == wx.ITALIC
	
	def _setFontItalic(self, val):
		if self._constructed():
			font = self.Font
			if val:
				font.SetStyle(wx.ITALIC)
			else:
				font.SetStyle(wx.NORMAL)
			self.Font = font
		else:
			self._properties["FontItalic"] = val

	
	def _getFontFace(self):
		return self.Font.GetFaceName()

	def _setFontFace(self, val):
		if self._constructed():
			f = self.Font
			f.SetFaceName(val)
			self.Font = f
		else:
			self._properties["FontFace"] = val

	
	def _getFontSize(self):
		return self.Font.GetPointSize()
	
	def _setFontSize(self, val):
		if self._constructed():
			font = self.Font
			font.SetPointSize(int(val))
			self.Font = font
		else:
			self._properties["FontSize"] = val
	
	def _getFontUnderline(self):
		return self.Font.GetUnderlined()
	
	def _setFontUnderline(self, val):
		if self._constructed():
			# underlining doesn't seem to be working...
			font = self.Font
			font.SetUnderlined(bool(val))
			self.Font = font
		else:
			self._properties["FontUnderline"] = val


	def _getHeaderFont(self):
		try:
			v = self._headerFont
		except AttributeError:
			v = self._getDefaultFont()
			v.SetWeight(wx.BOLD)
		return v
	
	def _setHeaderFont(self, val):
		if self._constructed():
			self._headerFont = val
			self._refreshHeader()
		else:
			self._properties["HeaderFont"] = val

	
	def _getHeaderFontBold(self):
		return self.HeaderFont.GetWeight() == wx.BOLD
	
	def _setHeaderFontBold(self, val):
		if self._constructed():
			font = self.HeaderFont
			if val:
				font.SetWeight(wx.BOLD)
			else:
				font.SetWeight(wx.LIGHT)    # wx.NORMAL doesn't seem to work...
			self.HeaderFont = font
		else:
			self._properties["HeaderFontBold"] = val

	def _getHeaderFontDescription(self):
		f = self.HeaderFont
		ret = f.GetFaceName() + " " + str(f.GetPointSize())
		if f.GetWeight() == wx.BOLD:
			ret += " B"
		if f.GetStyle() == wx.ITALIC:
			ret += " I"
		return ret
	
	def _getHeaderFontInfo(self):
		return self.HeaderFont.GetNativeFontInfoDesc()

		
	def _getHeaderFontItalic(self):
		return self.HeaderFont.GetStyle() == wx.ITALIC
	
	def _setHeaderFontItalic(self, val):
		if self._constructed():
			font = self.HeaderFont
			if val:
				font.SetStyle(wx.ITALIC)
			else:
				font.SetStyle(wx.NORMAL)
			self.HeaderFont = font
		else:
			self._properties["HeaderFontItalic"] = val

	
	def _getHeaderFontFace(self):
		return self.HeaderFont.GetFaceName()

	def _setHeaderFontFace(self, val):
		if self._constructed():
			f = self.HeaderFont
			f.SetFaceName(val)
			self.HeaderFont = f
		else:
			self._properties["HeaderFontFace"] = val

	
	def _getHeaderFontSize(self):
		return self.HeaderFont.GetPointSize()
	
	def _setHeaderFontSize(self, val):
		if self._constructed():
			font = self.HeaderFont
			font.SetPointSize(int(val))
			self.HeaderFont = font
		else:
			self._properties["HeaderFontSize"] = val
	
	def _getHeaderFontUnderline(self):
		return self.HeaderFont.GetUnderlined()
	
	def _setHeaderFontUnderline(self, val):
		if self._constructed():
			# underlining doesn't seem to be working...
			font = self.HeaderFont
			font.SetUnderlined(bool(val))
			self.HeaderFont = font
		else:
			self._properties["HeaderFontUnderline"] = val


	def _getHeaderBackgroundColor(self):
		try:
			v = self._headerBackgroundColor
		except AttributeError:
			v = self._headerBackgroundColor = None
		return v

	def _setHeaderBackgroundColor(self, val):
		if self._constructed():
			if isinstance(val, basestring):
				val = dColors.colorTupleFromName(val)
			self._headerBackgroundColor = val
			self._refreshHeader()
		else:
			self._properties["HeaderBackgroundColor"] = val

	
	def _getHeaderForegroundColor(self):
		try:
			v = self._headerForegroundColor
		except AttributeError:
			v = self._headerForegroundColor = None
		return v

	def _setHeaderForegroundColor(self, val):
		if self._constructed():
			if isinstance(val, basestring):
				val = dColors.colorTupleFromName(val)
			self._headerForegroundColor = val
			self._refreshHeader()
		else:
			self._properties["HeaderForegroundColor"] = val

	
	def _getHeaderHorizontalAlignment(self):
		try:
			val = self._headerHorizontalAlignment
		except AttributeError:
			val = self._headerHorizontalAlignment = None
		return val

	def _setHeaderHorizontalAlignment(self, val):
		if self._constructed():
			v = self._expandPropStringValue(val, ("Left", "Right", "Center", None))
			self._headerHorizontalAlignment = v
			self._refreshHeader()
		else:
			self._properties["HeaderHorizontalAlignment"] = val


	def _getHeaderVerticalAlignment(self):
		try:
			val = self._headerVerticalAlignment
		except AttributeError:
			val = self._headerVerticalAlignment = None
		return val

	def _setHeaderVerticalAlignment(self, val):
		if self._constructed():
			v = self._expandPropStringValue(val, ("Top", "Bottom", "Center", None))
			self._headerVerticalAlignment = v
			self._refreshHeader()
		else:
			self._properties["HeaderVerticalAlignment"] = val


	def _getHorizontalAlignment(self):
		try:
			auto = self._autoHorizontalAlignment
		except AttributeError:
			auto = self._autoHorizontalAlignment = True
		mapping = {wx.ALIGN_LEFT: "Left", wx.ALIGN_RIGHT: "Right",
				wx.ALIGN_CENTRE: "Center"}
		wxAlignment = self._gridColAttr.GetAlignment()[0]
		try:
			val = mapping[wxAlignment]
		except KeyError:
			val = "Left"
		if auto:
			val = "%s (Automatic)" % val
		return val

	def _setAutoHorizontalAlignment(self):
		dt = self.DataType
		if isinstance(dt, basestring):
			if dt in ("decimal", "float", "long", "integer"):
				self._setHorizontalAlignment("Right", _autoAlign=True)
		
	def _setHorizontalAlignment(self, val, _autoAlign=False):
		if self._constructed():
			val = self._expandPropStringValue(val, ("Automatic", "Left", "Right", "Center"))
			if val == "Automatic" and not _autoAlign:
				self._autoHorizontalAlignment = True
				self._setAutoHorizontalAlignment()
				return
			if val != "Automatic" and not _autoAlign:
				self._autoHorizontalAlignment = False
			mapping = {"Left": wx.ALIGN_LEFT, "Right": wx.ALIGN_RIGHT,
					"Center": wx.ALIGN_CENTRE}
			try:
				wxHorAlign = mapping[val]
			except KeyError:
				wxHorAlign = mapping["Left"]
				val = "Left"
			wxVertAlign = self._gridColAttr.GetAlignment()[1]
			self._gridColAttr.SetAlignment(wxHorAlign, wxVertAlign)
			self._refreshGrid()
		else:
			self._properties["HorizontalAlignment"] = val

	
	def _getListEditorChoices(self):
		try:
			v = self._listEditorChoices
		except:
			v = []
		return v

	def _setListEditorChoices(self, val):
		if self._constructed():
			self._listEditorChoices = val
		else:
			self._properties["ListEditorChoices"] = val


	def _getRendererClass(self):
		v = self.CustomRendererClass
		if v is None:
			v = self.defaultRenderers.get(self.DataType)
		return v


	def _getOrder(self):
		try:
			v = self._order
		except AttributeError:
			v = self._order = -1
		return v

	def _setOrder(self, val):
		if self._constructed():
			self._order = val
		else:
			self._properties["Order"] = val


	def _getSearchable(self):
		try:
			v = self._searchable
		except:
			v = self._searchable = True
		return v

	def _setSearchable(self, val):
		if self._constructed():
			self._searchable = bool(val)
		else:
			self._properties["Searchable"] = val


	def _getSortable(self):
		try:
			v = self._sortable
		except:
			v = self._sortable = True
		return v

	def _setSortable(self, val):
		if self._constructed():
			self._sortable = bool(val)
		else:
			self._properties["Sortable"] = val


	def _getVerticalAlignment(self):
		mapping = {wx.ALIGN_TOP: "Top", wx.ALIGN_BOTTOM: "Bottom",
				wx.ALIGN_CENTRE: "Center"}
		wxAlignment = self._gridColAttr.GetAlignment()[1]
		try:
			val = mapping[wxAlignment]
		except KeyError:
			val = "Top"
		return val

	def _setVerticalAlignment(self, val):
		if self._constructed():
			val = self._expandPropStringValue(val, ("Top", "Bottom", "Center"))
			mapping = {"Top": wx.ALIGN_TOP, "Bottom": wx.ALIGN_BOTTOM,
					"Center": wx.ALIGN_CENTRE}
			try:
				wxVertAlign = mapping[val]
			except KeyError:
				wxVertAlign = mapping["Top"]
				val = "Top"
			wxHorAlign = self._gridColAttr.GetAlignment()[0]
			self._gridColAttr.SetAlignment(wxHorAlign, wxVertAlign)
			self._refreshGrid()
		else:
			self._properties["VerticalAlignment"] = val


	def _getWidth(self):
		try:
			v = self._width
		except AttributeError:
			v = self._width = -1
		if self.Parent:
			idx = self._GridColumnIndex
			if idx >= 0:
				# Make sure the grid is in sync:
				self.Parent.SetColSize(idx, v)
		return v

	def _setWidth(self, val):
		if self._constructed():
			self._width = val
			if self.Parent:
				idx = self._GridColumnIndex
				if idx >= 0:
					# Change the size in the wx grid:
					self.Parent.SetColSize(idx, val)
					self.Parent.refresh()
		else:
			self._properties["Width"] = val
	

	Caption = property(_getCaption, _setCaption, None,
			_("Caption displayed in this column's header  (str)") )

	CustomEditorClass = property(_getCustomEditorClass, 
			_setCustomEditorClass, None,
			_("""Custom Editor class for this column. Default: None. 

			Set this to override the default editor class, which Dabo will 
			select based on the data type of the field."""))

	CustomEditors = property(_getCustomEditors, _setCustomEditors, None,
			_("""Dictionary of custom editors for this column. Default: {}. 

			Set this to override the default editor class on a row-by-row basis. 
			If there is no custom editor class for a given row in CustomEditors, 
			the CustomEditor property setting will apply."""))

	CustomListEditorChoices = property(_getCustomListEditorChoices, 
			_setCustomListEditorChoices, None,
			_("""Dictionary of custom list choices for this column. Default: {}. 

			Set this to override the default list choices on a row-by-row basis. 
			If there is no custom entry for a given row in CustomListEditorChoices, 
			the ListEditorChoices property setting will apply."""))

	CustomRendererClass = property(_getCustomRendererClass, 
			_setCustomRendererClass, None,
			_("""Custom Renderer class for this column. Default: None. 

			Set this to override the default renderer class, which Dabo will select based 
			on the data type of the field."""))

	CustomRenderers = property(_getCustomRenderers, _setCustomRenderers, None,
			_("""Dictionary of custom renderers for this column. Default: {}. 

			Set this to override the default renderer class on a row-by-row basis. 
			If there is no custom renderer for a given row in CustomRenderers, the 
			CustomRendererClass property setting will apply."""))

	DataType = property(_getDataType, _setDataType, None,
			_("Description of the data type for this column  (str)") )

	Editable = property(_getEditable, _setEditable, None,
			_("""If True, and if the grid is set as Editable, the cell values in this
				column are editable by the user. If False, the cells in this column 
				cannot be edited no matter what the grid setting is. When editable, 
				incremental searching will not be enabled, regardless of the 
				Searchable property setting.  (bool)""") )

	EditorClass = property(_getEditorClass, None, None,
			_("""Returns the editor class used for cells in the column. This 
				will be self.CustomEditorClass if set, or the default editor for the 
				datatype of the field.  (varies)"""))

	DataField = property(_getDataField, _setDataField, None,
			_("Field key in the data set to which this column is bound.  (str)") )

	Font = property(_getFont, _setFont, None,
			_("The font properties of the column's cells. (obj)") )
	
	FontBold = property(_getFontBold, _setFontBold, None,
			_("Specifies if the cell font is bold-faced. (bool)") )
	
	FontDescription = property(_getFontDescription, None, None, 
			_("Human-readable description of the column's cell font settings. (str)") )
	
	FontFace = property(_getFontFace, _setFontFace, None,
			_("Specifies the font face for the column cells. (str)") )
	
	FontInfo = property(_getFontInfo, None, None,
			_("Specifies the platform-native font info string for the column cells. Read-only. (str)") )
	
	FontItalic = property(_getFontItalic, _setFontItalic, None,
			_("Specifies whether the column's cell font is italicized. (bool)") )
	
	FontSize = property(_getFontSize, _setFontSize, None,
			_("Specifies the point size of the column's cell font. (int)") )
	
	FontUnderline = property(_getFontUnderline, _setFontUnderline, None,
			_("Specifies whether cell text is underlined. (bool)") )

	HeaderBackgroundColor = property(_getHeaderBackgroundColor, _setHeaderBackgroundColor, None,
			_("Optional color for the background of the column header  (str)") )

	HeaderFont = property(_getHeaderFont, _setHeaderFont, None,
			_("The font properties of the column's header. (obj)") )
	
	HeaderFontBold = property(_getHeaderFontBold, _setHeaderFontBold, None,
			_("Specifies if the header font is bold-faced. (bool)") )
	
	HeaderFontDescription = property(_getHeaderFontDescription, None, None, 
			_("Human-readable description of the current header font settings. (str)") )
	
	HeaderFontFace = property(_getHeaderFontFace, _setHeaderFontFace, None,
			_("Specifies the font face for the column header. (str)") )
	
	HeaderFontInfo = property(_getHeaderFontInfo, None, None,
			_("Specifies the platform-native font info string for the column header. Read-only. (str)") )
	
	HeaderFontItalic = property(_getHeaderFontItalic, _setHeaderFontItalic, None,
			_("Specifies whether the header font is italicized. (bool)") )
	
	HeaderFontSize = property(_getHeaderFontSize, _setHeaderFontSize, None,
			_("Specifies the point size of the header font. (int)") )
	
	HeaderFontUnderline = property(_getHeaderFontUnderline, _setHeaderFontUnderline, None,
			_("Specifies whether column header text is underlined. (bool)") )

	HeaderForegroundColor = property(_getHeaderForegroundColor, _setHeaderForegroundColor, None,
			_("Optional color for the foreground (text) of the column header  (str)") )

	HeaderHorizontalAlignment = property(_getHeaderHorizontalAlignment, _setHeaderHorizontalAlignment, None,
			_("Specifies the horizontal alignment of the header caption. ('Left', 'Center', 'Right')"))

	HeaderVerticalAlignment = property(_getHeaderVerticalAlignment, _setHeaderVerticalAlignment, None,
			_("Specifies the vertical alignment of the header caption. ('Top', 'Center', 'Bottom')"))

	HorizontalAlignment = property(_getHorizontalAlignment, _setHorizontalAlignment, None,
			_("""Horizontal alignment for all cells in this column. (str)
				Acceptable values are:
					'Automatic': The cell's contents will align right for numeric data, left for text. (default)
					'Left'
					'Center'
					'Right' """))

	ListEditorChoices = property(_getListEditorChoices, _setListEditorChoices, None,
		_("""Specifies the list of choices that will appear in the list. Only applies 
		if the DataType is set as "list".  (list)"""))

	Order = property(_getOrder, _setOrder, None,
			_("""Order of this column. Columns in the grid are arranged according
			to their relative Order. (int)""") )

	RendererClass = property(_getRendererClass, None, None,
			_("""Returns the renderer class used for cells in the column. This will be 
			self.CustomRendererClass if set, or the default renderer class for the 
			datatype of the field.  (varies)"""))

	Searchable = property(_getSearchable, _setSearchable, None,
			_("""Specifies whether this column's incremental search is enabled. 
			Default: True. The grid's Searchable property will override this setting.
			(bool)"""))

	Sortable = property(_getSortable, _setSortable, None,
			_("""Specifies whether this column can be sorted. Default: True. The grid's 
			Sortable property will override this setting.  (bool)"""))

	VerticalAlignment = property(_getVerticalAlignment, _setVerticalAlignment, None,
			_("""Vertical alignment for all cells in this column. Acceptable values 
			are 'Top', 'Center', and 'Bottom'.  (str)"""))

	Width = property(_getWidth, _setWidth, None,
			_("Width of this column  (int)") )
	
	_GridColumnIndex = property(_getGridColumnIndex)


class dGrid(wx.grid.Grid, cm.dControlMixin):
	"""Creates a grid, with rows and columns to represent records and fields.

	Grids are powerful controls for allowing reading and writing of data. A 
	grid can have any number of dColumns, which themselves have lots of properties
	to manipulate. The grid is virtual, meaning that large amounts of data can
	be accessed efficiently: only the data that needs to be shown on the current 
	screen is copied and displayed.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dGrid
		preClass = wx.grid.Grid
		
		# Internal flag to determine if the prior sort order needs to be restored:
		self._sortRestored = False
		
		# Used to provide 'data' when the DataSet is empty.
		self.emptyRowsToAdd = 0

		# dColumn maintains its own cell attribute object, but this is the default:
		self._defaultGridColAttr = self._getDefaultGridColAttr()
		
		# Some applications (I'm thinking the UI Designer here) need to be able
		# to set Editing = True, but still disallow editing. This attribute does that.
		self._vetoAllEditing = False
		
		# These hold the values that affect row/col hiliting
		self._selectionForeColor = "black"
		self._selectionBackColor = "yellow"
		self._selectionMode = "cell"
		self._modeSet = False
		# Track the last row and col selected
		self._lastRow = self._lastCol = None
		self._alternateRowColoring = False
		self._rowColorEven = "white"
		self._rowColorOdd = (212, 255, 212)		# very light green

		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
		
		# Need to sync the size reported by wx to the size reported by Dabo:
		self.RowHeight = self.RowHeight
		self.ShowRowLabels = self.ShowRowLabels


	def _afterInit(self):
		# When doing an incremental search, do we stop
		# at the nearest matching value?
		self.searchNearest = True
		# Do we do case-sensitive incremental searches?
		self.searchCaseSensitive = False
		# How many characters of strings do we display?
		self.stringDisplayLen = 64
		
		# When calculating auto-size widths, we don't want to use
		# the normal means of getting data sets.
		self.inAutoSizeCalc = False

		self.currSearchStr = ""
		self.incSearchTimer = dabo.ui.dTimer(self)
		self.incSearchTimer.bindEvent(dEvents.Hit, self.onIncSearchTimer)

		# By default, row labels are not shown. They can be displayed
		# if desired by setting ShowRowLabels = True, and their size
		# can be adjusted by setting RowLabelWidth = <width>
		self.SetRowLabelSize(self.RowLabelWidth)
		self.EnableEditing(self.Editable)

		# These need to be set to True, and custom methods provided,
		# if a grid with variable types in a single column is used.
		self.useCustomGetValue = False
		self.useCustomSetValue = False
		
		# What color/size should the little sort indicator arrow be?
		self.sortIndicatorColor = "DarkSlateGrey"
		self.sortIndicatorSize = 6
		self.sortIndicatorBuffer = 3

		# flags used by mouse motion event handlers:
		self._headerDragging = False
		self._headerDragFrom = 0
		self._headerDragTo = 0
		self._headerSizing = False

		self.sortedColumn = None
		self.sortOrder = None
		self.caseSensitiveSorting = False

		# If there is a custom sort method, set this to True
		self.customSort = False

		super(dGrid, self)._afterInit()
		
		# Set the header props/events
		self.initHeader()


	def initEvents(self):
		self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.__onWxMouseLeftDoubleClick)
		self.Bind(wx.grid.EVT_GRID_ROW_SIZE, self.__onWxGridRowSize)
		self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.__onWxGridSelectCell)
		self.Bind(wx.grid.EVT_GRID_COL_SIZE, self.__onWxGridColSize)
		self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.__onWxMouseLeftClick)
		self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.__onWxMouseRightClick)
		self.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.__onWxGridCellChange)
		self.Bind(wx.grid.EVT_GRID_RANGE_SELECT, self.__onWxGridRangeSelect)

		gridWindow = self.GetGridWindow()

		gridWindow.Bind(wx.EVT_MOTION, self.__onWxMouseMotion)
		gridWindow.Bind(wx.EVT_LEFT_DCLICK, self.__onWxMouseLeftDoubleClick)
		gridWindow.Bind(wx.EVT_LEFT_DOWN, self.__onWxMouseLeftDown)
		gridWindow.Bind(wx.EVT_LEFT_UP, self.__onWxMouseLeftUp)
		gridWindow.Bind(wx.EVT_RIGHT_DOWN, self.__onWxMouseRightDown)
		gridWindow.Bind(wx.EVT_RIGHT_UP, self.__onWxMouseRightUp)
		gridWindow.Bind(wx.EVT_CONTEXT_MENU, self.__onWxContextMenu)

		self.bindEvent(dEvents.KeyDown, self._onKeyDown)
		self.bindEvent(dEvents.GridRowSize, self._onGridRowSize)
		self.bindEvent(dEvents.GridCellSelected, self._onGridCellSelected)
		self.bindEvent(dEvents.GridColSize, self._onGridColSize)
		self.bindEvent(dEvents.GridCellEdited, self._onGridCellEdited)
		self.bindEvent(dEvents.GridMouseLeftClick, self._onGridMouseLeftClick)

		## wx.EVT_CONTEXT_MENU doesn't appear to be working for dGrid yet:
#		self.bindEvent(dEvents.GridContextMenu, self._onContextMenu)
		self.bindEvent(dEvents.GridMouseRightClick, self._onGridMouseRightClick)


	def initHeader(self):
		""" Initialize behavior for the grid header region."""
		header = self._getWxHeader()
		self.defaultHdrCursor = header.GetCursor()
		self._headerNeedsRedraw = False
		self._headerMousePosition = (0,0)
		self._headerMouseLeftDown, self._headerMouseRightDown = False, False


		header.Bind(wx.EVT_LEFT_DCLICK, self.__onWxHeaderMouseLeftDoubleClick)
		header.Bind(wx.EVT_LEFT_DOWN, self.__onWxHeaderMouseLeftDown)
		header.Bind(wx.EVT_LEFT_UP, self.__onWxHeaderMouseLeftUp)
		header.Bind(wx.EVT_RIGHT_DOWN, self.__onWxHeaderMouseRightDown)
		header.Bind(wx.EVT_RIGHT_UP, self.__onWxHeaderMouseRightUp)
		header.Bind(wx.EVT_MOTION, self.__onWxHeaderMouseMotion)
		header.Bind(wx.EVT_PAINT, self.__onWxHeaderPaint)
		header.Bind(wx.EVT_CONTEXT_MENU, self.__onWxHeaderContextMenu)
		header.Bind(wx.EVT_ENTER_WINDOW, self.__onWxHeaderMouseEnter)
		header.Bind(wx.EVT_LEAVE_WINDOW, self.__onWxHeaderMouseLeave)
		header.Bind(wx.EVT_IDLE, self.__onWxHeaderIdle)


		self.bindEvent(dEvents.GridHeaderMouseLeftDown, self._onGridHeaderMouseLeftDown)
		self.bindEvent(dEvents.GridHeaderMouseMove, self._onGridHeaderMouseMove)
		self.bindEvent(dEvents.GridHeaderMouseLeftUp, self._onGridHeaderMouseLeftUp)
		self.bindEvent(dEvents.GridHeaderMouseRightUp, self._onGridHeaderMouseRightUp)
		self.bindEvent(dEvents.GridHeaderMouseRightClick, self._onGridHeaderMouseRightClick)


	def GetCellValue(self, row, col):
		try:
			ret = self._Table.GetValue(row, col)
		except:
			ret = super(dGrid, self).GetCellValue(row, col)
		return ret

	def GetValue(self, row, col):
		try:
			ret = self._Table.GetValue(row, col)
		except:
			ret = super(dGrid, self).GetValue(row, col)
		return ret

	def SetValue(self, row, col, val):
		try:
			self._Table.SetValue(row, col, val)
		except StandardError, e:
			super(dGrid, self).SetCellValue(row, col, val)
		# Update the main data source
		try:
			fld = self.Columns[col].DataField
			biz = self.getBizobj()
			if biz:
				biz.RowNumber = row
				biz.setFieldVal(fld, val)
			else:
				self.DataSet[row][fld] = val
		except StandardError, e:
			dabo.errorLog.write("Cannot update data set: %s" % e)

	# Wrapper methods to Dabo-ize these calls.
	def getValue(self, row, col):
		return self.GetValue(row, col)
	def setValue(self, row, col, val):
		return self.SetValue(row, col, val)

	# These two methods need to be customized if a grid has columns
	# with more than one type of data in them.	
	def customCanGetValueAs(self, row, col, typ): pass
	def customCanSetValueAs(self, row, col, typ): pass


	# Wrap the native wx methods
	def setEditorForCell(self, row, col, edt):
		## dColumn maintains a dict of overriding editor mappings, but keep this 
		## function for convenience.
		dcol = self.Columns[col]
		dcol.CustomEditors[row] = edt
		#self.SetCellEditor(row, col, edt)

	def setRendererForCell(self, row, col, rnd):
		## dColumn maintains a dict of overriding renderer mappings, but keep this
		## function for convenience.
		dcol = self.Columns[col]
		dcol.CustomRenderers[row] = rnd
		#self.SetCellRenderer(row, col, rnd)
				
	
	def setTableAttributes(self, tbl):
		"""Set the attributes for table display"""
		tbl.alternateRowColoring = self.AlternateRowColoring
		tbl.rowColorOdd = self._getWxColour(self.RowColorOdd)
		tbl.rowColorEven = self._getWxColour(self.RowColorEven)
		
		
	def fillGrid(self, force=False):
		""" Refresh the grid to match the data in the data set."""
		# Save the focus, if any
		currFocus = self.FindFocus()
		currDataField = None
	
		# if the current focus is data-aware, we must temporarily remove it's binding
		# or the value of the control will flow to other records in the bizobj, but
		# I admit that I'm not entirely sure why. 
		if currFocus:
			try:
				currDataField = currFocus.DataField
				currFocus.DataField = ""
			except AttributeError:
				pass

		# Get the default row size from dApp's user settings
		app = self.Application
		form = self.Form
		if app is not None and form is not None and not app.isDesigner:
			s = app.getUserSetting("%s.%s.%s" % (form.Name, 
					self.Name, "RowSize"))
		else:
			s = None
		if s:
			self.SetDefaultRowSize(s)
		tbl = self._Table
		
		if self.emptyRowsToAdd and self.Columns:
			# Used for display purposes when no data is present.
			self._addEmptyRows()
		
		tbl.setColumns(self.Columns)
		tbl.fillTable(force)

		if force:
			row = max(0, self.CurrentRow)
			col = max(0, self.CurrentColumn)
			# Needed on Linux to get the grid to have the focus:
			for window in self.Children:
				window.SetFocus()
			# Needed on win and mac to get the grid to have the focus:
			self.GetGridWindow().SetFocus()
			if  not self.IsVisible(row, col):
				self.MakeCellVisible(row, col)
				self.MakeCellVisible(row, col)
			self.SetGridCursor(row, col)
		
#		self.SetColLabelAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

		if currFocus is not None:
			# put the data binding back and re-set the focus:
			try:
				currFocus.setFocus()
				currFocus.DataField = currDataField
				currFocus.refresh()
			except: pass

		if not self._sortRestored:	
			dabo.ui.callAfter(self._restoreSort)
			self._sortRestored = True

		# This will make sure that the current selection mode is activated.
		# We can't do it until after the first time the grid is filled.
		if not self._modeSet:
			self._modeSet = True
			self.SelectionMode = self.SelectionMode


	def _restoreSort(self):
		self.sortedColumn = self._getUserSetting("sortedColumn")
		self.sortOrder = self._getUserSetting("sortOrder")
	
		if self.sortedColumn is not None:
			sortCol = None
			for idx, col in enumerate(self.Columns):
				if col.DataField == self.sortedColumn:
					sortCol = idx
					break
			if sortCol is not None:
				self.CurrentColumn = sortCol
				if self.RowCount > 0:
					self.processSort(sortCol, toggleSort=False)

	
	def _addEmptyRows(self):
		"""Adds blank rows of data to the grid. Used mostly by
		the Designer to display a grid that actually looks like a grid.
		"""
		# First, get the type and field name for each column, and
		# add an empty value to a dict.
		colDict = {}
		for col in self.Columns:
			val = " " * 10
			dt = col.DataType
			if dt is "bool":
				val = False
			elif dt in ("int", "long"):
				val = 0
			elif dt in ("float", "decimal"):
				val = 0.00
			colDict[col.DataField] = val
		# Now add as many rows as specified
		ds = []
		for cnt in xrange(self.emptyRowsToAdd):
			ds.append(colDict)

		self.emptyRowsToAdd = 0
		self.DataSet = ds
		
		
	def buildFromDataSet(self, ds, keyCaption=None, 
			includeFields=None, colOrder=None, colWidths=None, colTypes=None,
			autoSizeCols=True):
		"""Add columns with properties set based on the passed dataset.

		A dataset is defined as one of:
			+ a sequence of dicts, containing fieldname/fieldvalue pairs.
			+ a string, which maps to a bizobj on the form.

		The columns will be taken from the first record of the dataset,	with each 
		column header caption being set to the field name, unless	the optional 
		keyCaption parameter is passed. This parameter is a 1:1 dict containing 
		the data set keys as its keys, and the desired caption as the 
		corresponding value.

		If the includeFields parameter is a sequence, the only columns added will 
		be the fieldnames included in the includeFields sequence. If the 
		includeFields	parameter is None, all fields will be added to the grid.

		The columns will be in the order returned by ds.keys(), unless the 
		optional colOrder parameter is passed. Like the keyCaption property, 
		this is a 1:1 dict containing key:order.
		"""
		if not ds:
			return False

		if colOrder is None:
			colOrder = {}

		if colWidths is None:
			colWidths = {}

		if colTypes is None:
			colTypes = {}

		if isinstance(ds, basestring):
			# Assume it is a bizobj datasource.
			if self.DataSource != ds:
				self.DataSource = ds
		else:
			self.DataSource = None
			self.DataSet = ds
		bizobj = self.getBizobj()

		if bizobj:
			data = bizobj.getDataSet(rows=1)
			if data:
				firstRec = data[0]
			else:
				# Ok, the bizobj doesn't have any records, yet we still want to build
				# the grid. We can get enough info from getDataStructureFromDescription():
				structure = bizobj.getDataStructureFromDescription()
				firstRec = {}
				for field in structure:
					firstRec[field[0]] = None
					if not colTypes.has_key(field[0]):
						colTypes[field[0]] = field[1]
		else:
			# not a bizobj datasource
			firstRec = ds[0]

		colKeys = [key for key in firstRec.keys()
				if (includeFields is None or key in includeFields)]

		# Add the columns
		for colKey in colKeys:
			# Use the keyCaption values, if possible
			try:
				cap = keyCaption[colKey]
			except:
				cap = colKey
			col = self.addColumn()
			col.Caption = cap
			col.DataField = colKey

			## pkm: Get the datatype from what is specified in fieldspecs, not from
			##      the actual type of the record. 
			try:
				dt = colTypes[colKey]
			except KeyError:
				# But if it didn't exist in the fieldspecs, use the actual type:
				dt = type(firstRec[colKey])

			if dt is type(None):
				if bizobj:
					for idx in range(bizobj.RowCount)[1:]:
						val = bizobj.getFieldVal(colKey, idx)
						if val is not None:
							dt = type(val)
							break
				else:
					for rec in ds[1:]:
						val = rec[colKey]
						if val is not None:
							dt = type(val)
							break
			col.DataType = dt
			if dt is type(None):
				# Default to string type
				dt = col.DataType = str
				
			# See if any order was specified
			if colOrder.has_key(colKey):
				col.Order = colOrder[colKey]

			# See if any width was specified
			if colWidths.has_key(colKey):
				col.Width = colWidths[colKey]
			else:
				# Use a default width
				col.Width = -1

		# Populate the grid
		self.fillGrid(True)
		if autoSizeCols:
			self.autoSizeCol("all")
		return True


	def autoSizeCol(self, colNum, persist=False):
		"""Set the column to the minimum width necessary to display its data.

		Set colNum='all' to auto-size all columns. Set persist=True to persist the
		new width to the user settings table.
		"""	
		maxWidth = 250  ## limit the width of the column to something reasonable
		# lock the screen
		self.lockDisplay()
		# We also don't want the Table's call to grid.getDataSet()
		# to wipe out our temporary changes.
		self.inAutoSizeCalc = True
		# We need to account for header caption width, too. Add
		# a row to the data set containing the header captions, and 
		# then remove the row afterwards.
		capRow = {}
		for col in self.Columns:
			capRow[col.DataField] = col.Caption

		## This function will get used in both if/elif below:
		def _setColSize(idx):
				## breathing room around header caption:
				capBuffer = 5
				## add additional room to account for possible sort indicator:
				capBuffer += ((2*self.sortIndicatorSize) + (2*self.sortIndicatorBuffer))
				colObj = self.Columns[idx]
				autoWidth = self.GetColSize(idx)
				
				# Account for the width of the header caption:
				cw = dabo.ui.fontMetricFromFont(colObj.Caption, 
						colObj.HeaderFont)[0] + capBuffer
				w = max(autoWidth, cw)
				w = min(w, maxWidth)
				colObj.Width = w

				if persist:
					colObj._persist("Width")
		
		if isinstance(colNum, str):
			## autosize all columns:
			try:
				self.AutoSizeColumns(setAsMin=False)
			except:
				# Having a problem with Unicode in the native function
				pass

			# Regardless of whether or not the native call worked, make sure that the
			# column widths as wx has them are propagated to the column widths as
			# dColumn has them:
			for ii in range(len(self.Columns)):
				_setColSize(ii)
						
		elif isinstance(colNum, (int, long)):
			try:
				self.AutoSizeColumn(colNum, setAsMin=False)
			except:
				pass
			_setColSize(colNum)

		self.inAutoSizeCalc = False
		self.refresh()
		self.unlockDisplay()		


	def _paintHeader(self, col=None):
		if col is None:
			cols = range(self.ColumnCount)
		else:
			cols = (col,)
		w = self._getWxHeader()
		dc = wx.ClientDC(w)

		for col in cols:
			sortIndicator = False

			colObj = self.Columns[col]
			rect = colObj._getHeaderRect()
			dc.SetClippingRegion(rect.x, rect.y, rect.width, rect.height)

			fcolor = colObj.HeaderForegroundColor
			if fcolor is None:
				fcolor = self.HeaderForegroundColor

			bcolor = colObj.HeaderBackgroundColor
			if bcolor is None:
				bcolor = self.HeaderBackgroundColor

			dc.SetTextForeground(fcolor)
			font = colObj.HeaderFont			

			holdBrush = dc.GetBrush()
			holdPen = dc.GetPen()
			
			if bcolor is not None:
				dc.SetBrush(wx.Brush(bcolor, wx.SOLID))
				dc.SetPen(wx.Pen(None, width=0))
				dc.DrawRectangle(rect[0] - (col != 0 and 1 or 0), 
					rect[1], 
					rect[2] + (col != 0 and 1 or 0), 
					rect[3])
			dc.SetPen(holdPen)
			dc.SetBrush(holdBrush)

			if self.Columns[col].DataField == self.sortedColumn:
				sortIndicator = True
				# draw a triangle, pointed up or down, at the top left 
				# of the column. TODO: Perhaps replace with prettier icons
				left = rect[0] + self.sortIndicatorBuffer
				top = rect[1] + self.sortIndicatorBuffer

				brushColor = dColors.colorTupleFromName(self.sortIndicatorColor)
				dc.SetBrush(wx.Brush(brushColor, wx.SOLID))
				if self.sortOrder == "DESC":
					# Down arrow
					dc.DrawPolygon([(left, top), (left+self.sortIndicatorSize, top), 
							(left+self.sortIndicatorBuffer, top+self.sortIndicatorSize)])
				elif self.sortOrder == "ASC":
					# Up arrow
					dc.DrawPolygon([(left+self.sortIndicatorBuffer, top), 
							(left+self.sortIndicatorSize, top+self.sortIndicatorSize), 
							(left, top+self.sortIndicatorSize)])
				else:
					# Column is not sorted, so don't draw.
					sortIndicator = False
			
			dc.SetFont(font)
			ah = colObj.HeaderHorizontalAlignment
			av = colObj.HeaderVerticalAlignment
			if ah is None:
				ah = self.HeaderHorizontalAlignment
			if av is None:
				av = self.HeaderVerticalAlignment
			if ah is None:
				ah = "Center"
			if av is None:
				av = "Center"

			wxah = {"Center": wx.ALIGN_CENTRE_HORIZONTAL, 
					"Left": wx.ALIGN_LEFT, 
					"Right": wx.ALIGN_RIGHT}[ah]

			wxav = {"Center": wx.ALIGN_CENTRE_VERTICAL, 
					"Top": wx.ALIGN_TOP,
					"Bottom": wx.ALIGN_BOTTOM}[av]

			# Give some more space around the rect - some platforms use a 3d look
			# and anyway it looks better if left/right aligned text isn't right on 
			# the line.
			horBuffer = 3
			vertBuffer = 2
			sortBuffer = horBuffer
			if sortIndicator:
				# If there's a sort indicator, we'll nudge the caption over
				sortBuffer += (self.sortIndicatorBuffer + self.sortIndicatorSize)
			trect = list(rect)
			trect[0] = trect[0] + sortBuffer
			trect[1] = trect[1] + vertBuffer
			if ah == "Center":
				trect[2] = trect[2] - (2*sortBuffer)
			else:	
				trect[2] = trect[2] - (horBuffer+sortBuffer)
			trect[3] = trect[3] - (2*vertBuffer)
			trect = wx.Rect(*trect)
			dc.DrawLabel("%s" % colObj.Caption, trect, wxav|wxah)
			dc.DestroyClippingRegion()


	def moveColumn(self, colNum, toNum):
		""" Move the column to a new position."""
		oldCol = self.Columns[colNum]
		self.Columns.remove(oldCol)
		if toNum > colNum:
			self.Columns.insert(toNum-1, oldCol)
		else:
			self.Columns.insert(toNum, oldCol)
		for col in self.Columns:
			col.Order = self.Columns.index(col) * 10
			col._persist("Order")
		self.fillGrid(True)


	def sizeToColumns(self, scrollBarFudge=True):
		"""Set the width of the grid equal to the sum of the widths	of the columns.

		If scrollBarFudge is True, additional space will be added to account for
		the width of the vertical scrollbar.
		"""
		fudge = 5
		if scrollBarFudge:
			fudge = 18
		self.Width = reduce(operator.add, [col.Width for col in self.Columns]) + fudge
		

	def sizeToRows(self, maxHeight=500, scrollBarFudge=True):
		"""Set the height of the grid equal to the sum of the heights of the rows.

		This is intended to be used only when the number of rows is expected to be
		low. Set maxHeight to whatever you want the maximum height to be.
		"""
		fudge = 5
		if scrollBarFudge:
			fudge = 18
		self.Height = min(self.RowHeight * self.RowCount, maxHeight) + fudge
	

	def onIncSearchTimer(self, evt):
		""" Occurs when the incremental search timer reaches its interval. 
		It is time to run the search, if there is any search in the buffer.
		"""
		if len(self.currSearchStr) > 0:
			self.runIncSearch()
		else:
			self.incSearchTimer.stop()

	
	##----------------------------------------------------------##
	##               begin: user hook methods                   ##
	##----------------------------------------------------------##

	def fillContextMenu(self, menu):
		""" User hook called just before showing the context menu.

		User code can append menu items, or replace/remove the menu entirely. 
		Return a dMenu or None from this hook. Default: no context menu.
		"""
		return menu


	def fillHeaderContextMenu(self, menu):
		""" User hook called just before showing the context menu for the header.

		User code can append menu items, or replace/remove the menu entirely. 
		Return a dMenu or None from this hook. The default menu includes an
		option to autosize the column.
		"""
		return menu


	def onEnterKeyAction(self):
		"Customize in subclasses"
		pass

		
	def onDeleteKeyAction(self):
		"Customize in subclasses"
		pass

	
	def onEscapeAction(self):
		"Customize in subclasses"
		pass

	
	def processKeyPress(self, char):
		"""Hook method for classes that need to process 
		keys in addition to Enter, Delete and Escape.
		Example:
			if keyCode == dKeys.keyStrings["f2"]:    # F2
				self.processSort()
		"""
		# Return False to prevent the keypress from being 'eaten'
		return False

	##----------------------------------------------------------##
	##                end: user hook methods                    ##
	##----------------------------------------------------------##


	def processSort(self, gridCol=None, toggleSort=True):
		""" Sort the grid column.

		Toggle between ascending and descending. If the grid column index isn't 
		passed, the currently active grid column will be sorted.
		"""
		if gridCol == None:
			gridCol = self.CurrentColumn
			
		if isinstance(gridCol, dColumn):
			colObj = gridCol
			canSort = (self.Sortable and gridCol.Sortable)
			columnToSort = gridCol
			sortCol = self.Columns.index(gridCol)
			dataType = self.Columns[gridCol].DataType
		else:
			colObj = self.Columns[gridCol]
			sortCol = gridCol
			columnToSort = self.Columns[gridCol].DataField
			canSort = (self.Sortable and self.Columns[gridCol].Sortable)
			dataType = None  ## will hunt for the dataType below

		if not canSort:
			# Some columns, especially those with mixed values,
			# should not be sorted.
			return
			
		sortOrder="ASC"
		if columnToSort == self.sortedColumn:
			sortOrder = self.sortOrder
			if toggleSort:
				if sortOrder == "ASC":
					sortOrder = "DESC"
				else:
					sortOrder = "ASC"
		self.sortOrder = sortOrder
		self.sortedColumn = columnToSort
		
		biz = self.getBizobj()

		if self.customSort:
			# Grids tied to bizobj cursors may want to use their own sorting.
			self.sort()
		elif biz:
			# Use the default sort() in the bizobj:
			try:
				biz.sort(columnToSort, sortOrder, self.caseSensitiveSorting)
			except dException.NoRecordsException:
				# no records to sort: who cares.
				pass
		else:
			# Create the list to hold the rows for sorting
			caseSensitive = self.caseSensitiveSorting
			sortList = []
			rowNum = 0
			rowlabels = self.RowLabels
			if self.DataSet:
				for row in self.DataSet:
					if rowlabels:
						sortList.append([row[columnToSort], row, rowlabels[rowNum]])
						rowNum += 1
					else:
						sortList.append([row[columnToSort], row])
			# At this point we have a list consisting of lists. Each of these member
			# lists contain the sort value in the zeroth element, and the row as
			# the first element.
			# First, see if we are comparing strings
			if dataType is None:
				f = sortList[0][0]
				if f is None:
					# We are just poking around, trying to glean the datatype, which is prone
					# to error. The record we just checked is None, so try the last record and
					# then give up.
					f = sortList[-1][0]
				#pkm: I think grid column DataType properties should store raw python
				#     types, not string renditions of them. But for now, convert to
				#     string renditions. I also think that this codeblock should be 
				#     obsolete once all dabo grids use dColumn objects.
				if isinstance(f, datetime.date):
					dataType = "date"
				elif isinstance(f, datetime.datetime):
					dataType = "datetime"
				elif isinstance(f, unicode):
					dataType = "unicode"
				elif isinstance(f, str):
					dataType = "string"
				elif isinstance(f, long):
					dataType = "long"
				elif isinstance(f, int):
					dataType = "int"
				elif _USE_DECIMAL and isinstance(f, decimal.Decimal):
					dataType = "decimal"
				else:
					dataType = None
				sortingStrings = isinstance(sortList[0][0], basestring)
			else:
				sortingStrings = dataType in ("unicode", "string")
			
			sortfunc = None
			if sortingStrings and not caseSensitive:
				sortfunc = lambda x, y: cmp(x[0].lower(), y[0].lower())
			elif dataType in ("date", "datetime"):
				# can't compare NoneType to these types:
				def datetimesort(v,w):
					x, y = v[0], w[0]
					if x is None and y is None:
						return 0
					elif x is None and y is not None:
						return -1
					elif x is not None and y is None:
						return 1
					else:
						return cmp(x,y)
				sortfunc = datetimesort	
			sortList.sort(sortfunc)
			
			# Unless DESC was specified as the sort order, we're done sorting
			if sortOrder == "DESC":
				sortList.reverse()
			# Extract the rows into a new list, then set the dataSet to the new list
			newRows = []
			newLabels = []
			for elem in sortList:
				newRows.append(elem[1])
				if self.RowLabels:
					newLabels.append(elem[2])
			self.RowLabels = newLabels
			self.DataSet = newRows

		if biz:
			self.CurrentRow = biz.RowNumber
		
		self.refresh()

		self._setUserSetting("sortedColumn")
		self._setUserSetting("sortOrder")


	def runIncSearch(self):
		""" Run the incremental search."""
		gridCol = self.CurrentColumn
		if gridCol < 0:
			gridCol = 0
		fld = self.Columns[gridCol].DataField
		if self.RowCount <= 0:
			# Nothing to seek within!
			return
		if not (self.Searchable and self.Columns[gridCol].Searchable):
			# Doesn't apply to this column.
			self.currSearchStr = ""
			return
		newRow = self.CurrentRow
		biz = self.getBizobj()
		ds = self.DataSet
		srchStr = origSrchStr = self.currSearchStr
		self.currSearchStr = ""
		near = self.searchNearest
		caseSensitive = self.searchCaseSensitive
		# Copy the specified field vals and their row numbers to a list, and 
		# add those lists to the sort list
		sortList = []
		for i in range(0, self.RowCount):
			if biz:
				val = biz.getFieldVal(fld, i)
			else:
				val = ds[i][fld]
			sortList.append( [val, i] )

		# Determine if we are seeking string values
		compString = isinstance(sortList[0][0], basestring)
		if not compString:
			# coerce srchStr to be the same type as the field type
			if isinstance(sortList[0][0], int):
				try:
					srchStr = int(srchStr)
				except ValueError:
					srchStr = int(0)
			elif isinstance(sortList[0][0], long):
				try:
					srchStr = long(srchStr)
				except ValueError:
					srchStr = long(0)
			elif isinstance(sortList[0][0], float):
				try:
					srchStr = float(srchStr)
				except ValueError:
					srchStr = float(0)

		if compString and not caseSensitive:
			# Use a case-insensitive sort.
			sortList.sort(lambda x, y: cmp(x[0].lower(), y[0].lower()))
		else:
			sortList.sort()

		# Now iterate through the list to find the matching value. I know that 
		# there are more efficient search algorithms, but for this purpose, we'll
		# just use brute force
		for fldval, row in sortList:
			if not isinstance(fldval, basestring):
				fldval = str(fldval)
			if not compString or caseSensitive:
				match = (fldval == srchStr)
			else:
				# Case-insensitive string search.
				match = (fldval.lower() == srchStr.lower())
			if match:
				newRow = row
				break
			else:
				if near:
					newRow = row
				# If we are doing a near search, see if the row is less than the
				# requested matching value. If so, update the value of 'ret'. If not,
				# we have passed the matching value, so there's no point in 
				# continuing the search, but we mu
				if compString and not caseSensitive:
					toofar = fldval.lower() > srchStr.lower()
				else:
					toofar = fldval > srchStr
				if toofar:
					break
		self.CurrentRow = newRow

		if self.Form is not None:
			# Add a '.' to the status bar to signify that the search is
			# done, and clear the search string for next time.
			self.Form.setStatusText("Search: %s." % origSrchStr)
		self.currSearchStr = ""


	def addToSearchStr(self, key):
		""" Add a character to the current incremental search.

		Called by KeyDown when the user pressed an alphanumeric key. Add the 
		key to the current search and start the timer.        
		"""
		app = self.Application
		searchDelay = self.SearchDelay
		if searchDelay is None:
			if app is not None:
				searchDelay = self.Application.SearchDelay
			else:
				# use a default
				searchDelay = 300

		self.incSearchTimer.stop()
		self.currSearchStr = "".join((self.currSearchStr, key))
		if self.Form is not None:
			self.Form.setStatusText("Search: %s" % self.currSearchStr)
		self.incSearchTimer.start(searchDelay)


	def getColNumByX(self, x):
		""" Given the x-coordinate, return the column number."""
		col = self.XToCol(x + (self.GetViewStart()[0]*self.GetScrollPixelsPerUnit()[0]))
		if col == wx.NOT_FOUND:
			col = -1
		return col


	def getColByX(self, x):
		""" Given the x-coordinate, return the column object."""
		colNum = self.getColNumByX(x)
		if (colNum < 0) or (colNum > self.ColumnCount-1):
			return None
		else:
			return self.Columns[colNum]


	def getColByDataField(self, df):
		""" Given a DataField value, return the corresponding column."""
		try:
			ret = [col for col in self.Columns
					if col.DataField == df][0]
		except IndexError:
			ret = None
		return ret	


	def maxColOrder(self):
		""" Return the highest value of Order for all columns."""
		ret = -1
		if len(self.Columns) > 0:
			ret = max([cc.Order for cc in self.Columns])
		return ret
		
		
	def addColumn(self, col=None, inBatch=False):
		""" Adds a column to the grid. If no column is passed, a 
		blank column is added, which can be customized later.
		"""
		if col is None:
			col = self.ColumnClass(self)
		else:
			col.Parent = self
		if col.Order == -1:
			col.Order = self.maxColOrder() + 10
		self.Columns.append(col)
		if not inBatch:
			self._syncColumnCount()

		try:
			## Set the Width property last, otherwise it won't stick:
			if not col.Width:
				col.Width = 75
			else:
				## If Width was specified in the dColumn subclass or in the constructor,
				## it's been set as the property but because it wasn't part of the grid
				## yet it hasn't yet taken effect: force it.
				col.Width = col.Width
		except:
			# If the underlying wx grid doesn't yet know about the column, such
			# as when adding columns with inBatch=True, this can throw an error
			# For now, just log it
			dabo.infoLog.write(_("Cannot set width of column %s") % col.Order)
		return col


	def removeColumn(self, col=None):
		""" Removes a column from the grid. 

		If no column is passed, the last column is removed. The col argument can
		be either a column index or a dColumn instance.
		"""
		colNum = None
		if col is None:
			colNum = self.ColumnCount - 1
		elif isinstance(col, int):
			colNum = col
		else:
			# They probably passed a specific column instance
			colNum = self.Columns.index(col)
			if colNum == -1:
				# No such column
				# raise an error?
				return
		del self.Columns[colNum]
		self._syncColumnCount()
		self.fillGrid(True)

	
	def cell(self, row, col):
		class GridCell(object):
			def __init__(self, parent, row, col):
				self.parent = parent
				self.row = row
				self.col = col
			
			def _getVal(self):
				return self.parent.GetValue(self.row, self.col)
			def _setVal(self, val):
				self.parent.SetValue(self.row, self.col, val)
			Value = property(_getVal, _setVal)
		return GridCell(self, row, col)
		

	def getBizobj(self):
		ds = self.DataSource
		if isinstance(ds, basestring) and self.Form is not None:
			return self.Form.getBizobj(ds)
		return None


	def refresh(self):
		self._syncCurrentRow()
		self._syncColumnCount()
		self._syncRowCount()
		super(dGrid, self).refresh()


	def _getWxHeader(self):
		"""Return the wx grid header window."""
		return self.GetGridColLabelWindow()


	def _syncCurrentRow(self):
		"""Sync the CurrentRow of the grid to the RowNumber of the bizobj.

		Has no effect if the grid's DataSource isn't a link to a bizobj.
		"""
		bizobj = self.getBizobj()
		if bizobj:
			self.CurrentRow = bizobj.RowNumber


	def _syncColumnCount(self):
		"""Sync wx's rendition of column count with our self.ColumnCount"""
		msg = None
		self.BeginBatch()
		wxColumnCount = self.GetNumberCols()
		daboColumnCount = len(self.Columns)
		diff = daboColumnCount - wxColumnCount
		if diff < 0:
			msg = wx.grid.GridTableMessage(self._Table,
					wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED,
					0, abs(diff))

		elif diff > 0:
			msg = wx.grid.GridTableMessage(self._Table,
					wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED,
					diff)

		if msg:
			self.ProcessTableMessage(msg)
		self.EndBatch()


	def _syncRowCount(self):
		"""Sync wx's rendition of row count with our self.RowCount"""
		msg = None
		self.BeginBatch()
		wxRowCount = self.GetNumberRows()
		daboRowCount = self.RowCount
		diff = daboRowCount - wxRowCount
		if diff < 0:
			msg = wx.grid.GridTableMessage(self._Table,
					wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED,
					0,
					abs(diff))

		elif diff > 0:
			msg = wx.grid.GridTableMessage(self._Table,
					wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED,
					diff)

		if msg:
			self.ProcessTableMessage(msg)
		self.EndBatch()


	def _getDefaultGridColAttr(self):
		""" Return the GridCellAttr that will be used for all columns by default."""
		attr = wx.grid.GridCellAttr()
		attr.SetAlignment(wx.ALIGN_TOP, wx.ALIGN_LEFT)
		attr.SetReadOnly(True)
		return attr
	

	def _getUserSetting(self, prop):
		"""Get the value of prop from the user settings table."""
		app = self.Application
		form = self.Form
		ret = None
		if app is not None and form is not None and not app.isDesigner:
			settingName = "%s.%s.%s" % (form.Name, self.Name, prop)
			ret = app.getUserSetting(settingName)
		return ret

	def _setUserSetting(self, prop):
		"""Persist the value of prop to the user settings table."""
		app = self.Application
		form = self.Form
		if app is not None and form is not None and not app.isDesigner:
			val = getattr(self, prop)
			settingName = "%s.%s.%s" % (form.Name, self.Name, prop)
			app.setUserSetting(settingName, val)


	##----------------------------------------------------------##
	##        begin: dEvent callbacks for internal use          ##
	##----------------------------------------------------------##
	def __onRowNumChanged(self, evt):
		# The form reports that the rownum has changed: sync the grid CurrentRow
		self._syncCurrentRow()

		
	def _onGridCellEdited(self, evt):
		bizobj = self.getBizobj()
		row, col = evt.EventData["row"], evt.EventData["col"]
		fld = self.Columns[col].DataField
		newVal = self.GetCellValue(row, col)
		if bizobj:
			oldVal = bizobj.getFieldVal(fld, row)
		else:
			oldVal = self.DataSet[row][fld]
		if newVal != oldVal:
			# Update the local copy of the data
			if bizobj:
				# Put on correct RowNumber if not already (this should already be the case)
				bizobj.RowNumber = row
				bizobj.setFieldVal(fld, newVal)
			else:
				self.DataSet[row][fld] = newVal


	def _onGridColSize(self, evt):
		"Occurs when the user resizes the width of the column."
		colNum = evt.EventData["col"]
		col = self.Columns[colNum]
		colName = "Column_%s" % col.DataField

		# Sync our column object up with what the grid is reporting, and because
		# the user made this change, save to the userSettings:
		width = col.Width = self.GetColSize(colNum)
		app = self.Application
		if app is not None:
			col._persist("Width")
	

	def _onGridHeaderMouseMove(self, evt):
		headerIsDragging = self._headerDragging
		headerIsSizing = self._headerSizing
		dragging = evt.EventData["mouseDown"]
		header = self._getWxHeader()
		self._headerMousePosition = evt.EventData["mousePosition"]

		if dragging:
			x,y = evt.EventData["mousePosition"]

			if not headerIsSizing and (
				self.getColNumByX(x) == self.getColNumByX(x-2) == self.getColNumByX(x+2)):
				if not headerIsDragging:
					# A header reposition is beginning
					self._headerDragging = True
					self._headerDragFrom = (x,y)
				else:
					# already dragging.
					begCol = self.getColNumByX(self._headerDragFrom[0])
					curCol = self.getColNumByX(x)

					# The visual indicators (changing the mouse cursor) isn't currently
					# working. It would work without the evt.Skip() below, but that is 
					# needed for when the column is resized.
					uic = dUICursors
					if begCol == curCol:
						# Give visual indication that a move is initiated
						header.SetCursor(uic.getStockCursor(uic.Cursor_Size_WE))
					else:
						# Give visual indication that this is an acceptable drop target
						header.SetCursor(uic.getStockCursor(uic.Cursor_Bullseye))
			else:
				# A size action is happening
				self._headerSizing = True


	def _onGridHeaderMouseLeftUp(self, evt):
		""" Occurs when the left mouse button is released in the grid header.

		Basically, this comes down to two possibilities: the end of a drag
		operation, or a single-click operation. If we were dragging, then
		it is possible a column needs to change position. If we were clicking,
		then it is a sort operation.
		"""
		x,y = evt.EventData["mousePosition"]
		if self._headerDragging:
			# A drag action is ending
			self._headerDragTo = (x,y)

			begCol = self.getColNumByX(self._headerDragFrom[0])
			curCol = self.getColNumByX(x)

			if begCol != curCol:
				if curCol > begCol:
					curCol += 1
				self.moveColumn(begCol, curCol)
			self._getWxHeader().SetCursor(self.defaultHdrCursor)
		elif self._headerSizing:
			pass
		else:
			# we weren't dragging, and the mouse was just released.
			# Find out the column we are in based on the x-coord, and
			# do a processSort() on that column.
			if self.DataSet:
				# No need to sort if there is no data.
				col = self.getColNumByX(x)
				self.processSort(col)
		self._headerDragging = False
		self._headerSizing = False
		## pkm: commented out the evt.Continue=False because it doesn't appear
		##      to be needed, and it prevents the native UI from responding.
		#evt.Continue = False


	def _onGridHeaderMouseRightClick(self, evt):
		# Make the popup menu appear in the location that was clicked. We init
		# the menu here, then call the user hook method to optionally fill the
		# menu. If we get a menu back from the user hook, we display it.

		menu = dabo.ui.dMenu()

		# Fill the default menu item(s):
		def _autosizeColumn(evt):
			self.autoSizeCol(self.getColNumByX(self._headerMousePosition[0]), persist=True)
		menu.append(_("&Autosize Column"), bindfunc=_autosizeColumn, 
				help=_("Autosize the column based on the data in the column."))

		menu = self.fillHeaderContextMenu(menu)

		if menu is not None and len(menu.Children) > 0:
			self.showContextMenu(menu)


	def _onGridHeaderMouseRightUp(self, evt):
		""" Occurs when the right mouse button goes up in the grid header."""
		pass

	
	def _onGridMouseRightClick(self, evt):
		# Make the popup menu appear in the location that was clicked. We init
		# the menu here, then call the user hook method to optionally fill the
		# menu. If we get a menu back from the user hook, we display it.

		# First though, make the cell the user right-clicked on the current cell:
		self.CurrentRow = evt.row
		self.CurrentColumn = evt.col

		menu = dabo.ui.dMenu()
		menu = self.fillContextMenu(menu)

		if menu is not None and len(menu.Children) > 0:
			self.showContextMenu(menu)
	

	def _onGridHeaderMouseLeftDown(self, evt):
		# We need to eat this event, because the native wx grid will select all
		# rows in the column, which is a spreadsheet-like behavior, not a data-
		# aware grid-like behavior. However, let's keep our eyes out for a better
		# way to handle this, because eating events could cause some hard-to-debug
		# problems later (there could be other, more critical code, that isn't 
		# being allowed to run).
		evt.Continue = False


	def _onGridMouseLeftClick(self, evt):
		self.ShowCellEditControl()


	def _onGridRowSize(self, evt):
		""" Occurs when the user sizes the height of the row. If the
		property 'SameSizeRows' is True, Dabo overrides the wxPython 
		default and applies that size change to all rows, not just the row 
		the user sized.
		"""
		row = evt.EventData["row"]
		size = self.GetRowSize(row)

		if self.SameSizeRows:
			self.RowHeight = size


	def _onGridCellSelected(self, evt):
		""" Occurs when the grid's cell focus has changed."""

		## pkm 2005-09-28: This works around a nasty segfault:
		self.HideCellEditControl()
		## but periodically test it. My current version: 2.6.1.1pre

		oldRow = self.CurrentRow
		newRow = evt.EventData["row"]
		newCol = evt.EventData["col"]
		try:
			col = self.Columns[newCol]
		except:
			col = None

		if col:
			## pkm 2005-09-28: Part of the editor segfault workaround. This sets the
			##                 editor for the entire column, at a point in time before
			##                 the grid is actually asking for the editor, and in a 
			##                 fashion that ensures the editor instance doesn't go
			##                 out of scope prematurely.
			col._setEditor(newRow)

		if col and self.Editable and col.Editable and self.ActivateEditorOnSelect:
			dabo.ui.callAfter(self.EnableCellEditControl)
		if oldRow != newRow:
			bizobj = self.getBizobj()
			if bizobj:
				if bizobj.RowCount > newRow:
					# First attempt to go through the form.
					if self.Form and hasattr(self.Form, "moveToRowNumber"):
							self.Form.moveToRowNumber(newRow, dataSource=bizobj.DataSource)
					else:
						# set the RowNumber on the bizobj directly
						bizobj.RowNumber = newRow
				else:
					# We are probably trying to select row 0 when there are no records
					# in the bizobj.
					##pkm: the following call causes an assertion on Mac, and appears to be
					##     unneccesary.
					#self.SetGridCursor(0,0)
					pass
		if self.Form is not None:
			dabo.ui.callAfter(self.Form.refreshControls, grid=self)


	def _onKeyDown(self, evt): 
		""" Occurs when the user presses a key inside the grid. 
		Default actions depend on the key being pressed:
					Enter:  edit the record
						Del:  delete the record
						F2:  sort the current column
				AlphaNumeric:  incremental search
		"""
		if self.Editable and self.Columns[self.CurrentColumn].Editable:
			# Can't search and edit at the same time
			return

		keyCode = evt.EventData["keyCode"]
		try:
			char = chr(keyCode)
		except ValueError:       # keycode not in ascii range
			char = None

		if keyCode == dKeys.keyStrings["enter"]:           # Enter
			self.onEnterKeyAction()
			evt.stop()
		else:
			if keyCode == dKeys.keyStrings["delete"]:      # Del
				self.onDeleteKeyAction()
				evt.stop()
			elif keyCode == dKeys.keyStrings["escape"]:
				self.onEscapeAction()
				evt.stop()
			elif char and (self.Searchable and self.Columns[self.CurrentColumn].Searchable) \
				and (char.isalnum() or char.isspace() and not evt.hasModifiers):
				self.addToSearchStr(char)
				# For some reason, without this the key happens twice
				evt.stop()
			else:
				if self.processKeyPress(keyCode):
					# Key was handled
					evt.stop()
		
	
	##----------------------------------------------------------##
	##        end: dEvent callbacks for internal use            ##
	##----------------------------------------------------------##


	##----------------------------------------------------------##
	##      begin: wx callbacks to re-route to dEvents          ##
	##----------------------------------------------------------##
	
	## dGrid has to reimplement all of this to augment what dPemMixin does,
	## to offer separate events in the grid versus the header region.
	def __onWxContextMenu(self, evt):
		self.raiseEvent(dEvents.GridContextMenu, evt)
		evt.Skip()

	def __onWxGridColSize(self, evt):
		self.raiseEvent(dEvents.GridColSize, evt)
		evt.Skip()
	
	def __onWxGridRangeSelect(self, evt):
		self.raiseEvent(dEvents.GridRangeSelected, evt)
		
	def __onWxGridCellChange(self, evt):
		self.raiseEvent(dEvents.GridCellEdited, evt)
		evt.Skip()

	def __onWxGridRowSize(self, evt):
		self.raiseEvent(dEvents.GridRowSize, evt)
		evt.Skip()

	def __onWxGridSelectCell(self, evt):
		self.raiseEvent(dEvents.GridCellSelected, evt)
		evt.Skip()
		self._lastRow, self._lastCol = evt.GetRow(), evt.GetCol()
		try:
			mode = self.GetSelectionMode()
			if mode == wx.grid.Grid.wxGridSelectRows:
				self.SelectRow(evt.GetRow())
			elif mode == wx.grid.Grid.wxGridSelectColumns:
				self.SelectCol(evt.GetCol())
		except wx._core.PyAssertionError:
			# No table yet
			pass

	def __onWxHeaderContextMenu(self, evt):
		self.raiseEvent(dEvents.GridHeaderContextMenu, evt)
		evt.Skip()

	def __onWxHeaderIdle(self, evt):
		self.raiseEvent(dEvents.GridHeaderIdle, evt)
		evt.Skip()

	def __onWxHeaderMouseEnter(self, evt):
		self.raiseEvent(dEvents.GridHeaderMouseEnter, evt)
		
	def __onWxHeaderMouseLeave(self, evt):
		self._headerMouseLeftDown, self._headerMouseRightDown = False, False
		self.raiseEvent(dEvents.GridHeaderMouseLeave, evt)

	def __onWxHeaderMouseLeftDoubleClick(self, evt):
		self.raiseEvent(dEvents.GridHeaderMouseLeftDoubleClick, evt)
		evt.Skip()

	def __onWxHeaderMouseLeftDown(self, evt):
		self.raiseEvent(dEvents.GridHeaderMouseLeftDown, evt)
		self._headerMouseLeftDown = True
		#evt.Skip() #- don't skip or all the rows will be selected.

	def __onWxHeaderMouseLeftUp(self, evt):
		self.raiseEvent(dEvents.GridHeaderMouseLeftUp, evt)
		if self._headerMouseLeftDown:
			# mouse went down and up in the header: send a click:
			self.raiseEvent(dEvents.GridHeaderMouseLeftClick, evt)
			self._headerMouseLeftDown = False
		evt.Skip()

	def __onWxHeaderMouseMotion(self, evt):
		self.raiseEvent(dEvents.GridHeaderMouseMove, evt)
		evt.Skip()

	def __onWxHeaderMouseRightDown(self, evt):
		self.raiseEvent(dEvents.GridHeaderMouseRightDown, evt)
		self._headerMouseRightDown = True
		evt.Skip()

	def __onWxHeaderMouseRightUp(self, evt):
		self.raiseEvent(dEvents.GridHeaderMouseRightUp, evt)
		if self._headerMouseRightDown:
			# mouse went down and up in the header: send a click:
			self.raiseEvent(dEvents.GridHeaderMouseRightClick, evt)
			self._headerMouseRightDown = False
		evt.Skip()

	def __onWxHeaderPaint(self, evt):
		self.raiseEvent(dEvents.GridHeaderPaint, evt)
		evt.Skip()

	def __onWxMouseLeftDoubleClick(self, evt):
		self.raiseEvent(dEvents.GridMouseLeftDoubleClick, evt)
		evt.Skip()

	def __onWxMouseLeftClick(self, evt):
		self.raiseEvent(dEvents.GridMouseLeftClick, evt)
		evt.Skip()

	def __onWxMouseLeftDown(self, evt):
		self.raiseEvent(dEvents.GridMouseLeftDown, evt)
		evt.Skip()

	def __onWxMouseLeftUp(self, evt):
		self.raiseEvent(dEvents.GridMouseLeftUp, evt)
		evt.Skip()

	def __onWxMouseMotion(self, evt):
		self.raiseEvent(dEvents.GridMouseMove, evt)
		evt.Skip()

	def __onWxMouseRightClick(self, evt):
		self.raiseEvent(dEvents.GridMouseRightClick, evt)
		evt.Skip()

	def __onWxMouseRightDown(self, evt):
		self.raiseEvent(dEvents.GridMouseRightDown, evt)
		evt.Skip()

	def __onWxMouseRightUp(self, evt):
		self.raiseEvent(dEvents.GridMouseRightUp, evt)
		evt.Skip()

	##----------------------------------------------------------##
	##       end: wx callbacks to re-route to dEvents           ##
	##----------------------------------------------------------##

	

	##----------------------------------------------------------##
	##              begin: property definitions                 ##
	##----------------------------------------------------------##
	def _getActivateEditorOnSelect(self):
		try:
			v = self._activateEditorOnSelect
		except AttributeError:
			v = self._activateEditorOnSelect = True
		return v

	def _setActivateEditorOnSelect(self, val):
		self._activateEditorOnSelect = bool(val)

	
	def _getAlternateRowColoring(self):
		return self._alternateRowColoring

	def _setAlternateRowColoring(self, val):
		self._alternateRowColoring = val
		self.setTableAttributes(self._Table)


	def _getCellHighlightWidth(self):
		return self.GetCellHighlightPenWidth()

	def _setCellHighlightWidth(self, val):
		if self._constructed():
			self.SetCellHighlightPenWidth(val)
			self.SetCellHighlightROPenWidth(val)
		else:
			self._properties["CellHighlightWidth"] = val


	def _getColumns(self):
		if hasattr(self, "_columns"):
			v = self._columns
		else:
			v = self._columns = []
		return v
	
	
	def _getColumnClass(self):
		if hasattr(self, "_columnClass"):
			v = self._columnClass
		else:
			v = self._columnClass = dColumn
		return v

	def _setColumnClass(self, val):
		self._columnClass = val


	def _getColumnCount(self):
		return len(self.Columns)

	def _setColumnCount(self, val):
		if self._constructed():
			if val > -1:
				colChange = val - self.ColumnCount 
				if colChange == 0:
					# No change
					return
				elif colChange < 0:
					while self.ColumnCount > val:
						self.Columns.remove(self.Columns[-1])
				else:
					for cc in range(colChange):
						self.addColumn(inBatch=True)
				self._syncColumnCount()
				self.fillGrid(True)
		else:
			self._properties["ColumnCount"] = val


	def _getHeaderHeight(self):
		return self.GetColLabelSize()

	def _setHeaderHeight(self, val):
		if self._constructed():
			self.SetColLabelSize(val)
		else:
			self._properties["HeaderHeight"]
	
	
	def _getNoneDisp(self):
		try:
			# See if the Application has a value set
			ret = self.Application.NoneDisplay
		except:
			ret = _("<null>")
		return ret
		

	def _getRowCount(self):
		return self._Table.GetNumberRows()
		
	def _getCurrCellVal(self):
		return self.GetValue(self.GetGridCursorRow(), self.GetGridCursorCol())	

	def _setCurrCellVal(self, val):
		self.SetValue(self.GetGridCursorRow(), self.GetGridCursorCol(), val)	
		self.Refresh()


	def _getCurrentColumn(self):
		return self.GetGridCursorCol()

	def _setCurrentColumn(self, val):
		if self._constructed():
			if val > -1:
				val = min(val, self.ColumnCount)
				rn = self.CurrentRow
				self.SetGridCursor(rn, val)
				self.MakeCellVisible(rn, val)
		else:
			self._properties["CurrentColumn"] = val
		

	def _getCurrentField(self):
		return self.Columns[self.GetGridCursorCol()].DataField

	def _setCurrentField(self, val):
		if self._constructed():
			for ii in range(len(self.Columns)):
				if self.Columns[ii].DataField == val:
					self.CurrentColumn = ii
					break
		else:	
			self._properties["CurrentField"] = val


	def _getCurrentRow(self):
		return self.GetGridCursorRow()

	def _setCurrentRow(self, val):
		if self._constructed():
			val = min(val, self.RowCount-1)	
			if val > -1:
				cn = self.CurrentColumn
				self.SetGridCursor(val, cn)
				self.MakeCellVisible(val, cn)
		else:
			self._properties["CurrentRow"] = val		


	def _getDataSet(self):
		if self.DataSource is not None:
			ret = None
			bo = self.getBizobj()
			if bo:
				ret = bo.getDataSet()
			else:
				# See if the DataSource is a reference
				try:
					ret = eval(self.DataSource)
				except: pass
			self._dataSet = ret
		else:
			try:
				ret = self._dataSet
			except AttributeError:
				ret = self._dataSet = None
		return ret			

	def _setDataSet(self, val):
		if self._constructed():
			if (self.DataSource is not None) and not self.Application.isDesigner:
				raise ValueError, "Cannot set DataSet: DataSource defined."
			# We must make sure the grid's table is initialized first:
			self._Table
			self._dataSet = val
			self.fillGrid(True)
			biz = self.getBizobj()
			if biz:
				## I think I want to have the bizobj raise the RowNumChanged event,
				## but for now this will suffice:
				self.Form.bindEvent(dEvents.RowNumChanged, self.__onRowNumChanged)
		else:
			self._properties["DataSet"] = val


	def _getDataSource(self):
		try:
			v = self._dataSource
		except AttributeError:
			v = self._dataSource = None
		return v

	def _setDataSource(self, val):
		if self._constructed():
			# We must make sure the grid's table is initialized first:
			self._Table
			oldBizobj = self.getBizobj()
			if oldBizobj:
				oldBizobj.unbindEvent(dEvents.RowNumChanged, self.__onRowNumChanged)
			self._dataSet = None
			self._dataSource = val
			self.fillGrid(True)
			biz = self.getBizobj()
			if biz:
				## I think I want to have the bizobj raise the RowNumChanged event,
				## but for now this will suffice:
				self.Form.bindEvent(dEvents.RowNumChanged, self.__onRowNumChanged)
		else:
			self._properties["DataSource"] = val


	def _getEditable(self):
		if self._vetoAllEditing:
			return False
		else:
			return self.IsEditable()

	def _setEditable(self, val):
		if self._constructed():
			self.EnableEditing(val)
		else:
			self._properties["Editable"] = val
	
	
	def _getEncoding(self):
		bo = self.getBizobj()
		if bo is not None:
			ret = bo.Encoding
		else:
			try:
				ret = wx.GetDefaultPyEncoding()
			except AttributeError:
				# wx versions < 2.6 don't have the GetDefaultPyEncoding function
				ret = "utf-8"
		return ret
		

	def _getHeaderBackgroundColor(self):
		try:
			v = self._headerBackgroundColor
		except AttributeError:
			v = self._headerBackgroundColor = None
		return v

	def _setHeaderBackgroundColor(self, val):
		if self._constructed():
			if isinstance(val, basestring):
				val = dColors.colorTupleFromName(val)
			self._headerBackgroundColor = val
			self.refresh()
		else:
			self._properties["HeaderBackgroundColor"] = val

	
	def _getHeaderForegroundColor(self):
		try:
			v = self._headerForegroundColor
		except AttributeError:
			v = self._headerForegroundColor = None
		return v

	def _setHeaderForegroundColor(self, val):
		if self._constructed():
			if isinstance(val, basestring):
				val = dColors.colorTupleFromName(val)
			self._headerForegroundColor = val
			self.refresh()
		else:
			self._properties["HeaderForegroundColor"] = val

	
	def _getHeaderHorizontalAlignment(self):
		try:
			val = self._headerHorizontalAlignment
		except AttributeError:
			val = self._headerHorizontalAlignment = "Center"
		return val

	def _setHeaderHorizontalAlignment(self, val):
		if self._constructed():
			v = self._expandPropStringValue(val, ("Left", "Right", "Center"))
			self._headerHorizontalAlignment = v
			self.refresh()
		else:
			self._properties["HeaderHorizontalAlignment"] = val


	def _getHeaderVerticalAlignment(self):
		try:
			val = self._headerVerticalAlignment
		except AttributeError:
			val = self._headerVerticalAlignment = "Center"
		return val

	def _setHeaderVerticalAlignment(self, val):
		if self._constructed():
			v = self._expandPropStringValue(val, ("Top", "Bottom", "Center"))
			self._headerVerticalAlignment = v
			self.refresh()
		else:
			self._properties["HeaderVerticalAlignment"] = val


	def _getHorizontalScrolling(self):
		return self.GetScrollPixelsPerUnit()[0] > 0

	def _setHorizontalScrolling(self, val):
		if self._constructed():
			if val:
				self.SetScrollRate(20, self.GetScrollPixelsPerUnit()[1])
			else:
				self.SetScrollRate(0, self.GetScrollPixelsPerUnit()[1])
			self.refresh()
		else:
			self._properties["HorizontalScrolling"] = val


	def _getRowColorEven(self):
		return self._rowColorEven

	def _setRowColorEven(self, val):
		self._rowColorEven = val
		self.setTableAttributes(self._Table)


	def _getRowColorOdd(self):
		return self._rowColorOdd

	def _setRowColorOdd(self, val):
		self._rowColorOdd = val
		self.setTableAttributes(self._Table)


	def _getRowHeight(self):
		if hasattr(self, "_rowHeight"):
			v = self._rowHeight
		else:
			v = self._rowHeight = self.GetDefaultRowSize()
		return v

	def _setRowHeight(self, val):
		if self._constructed():
			if val != self._rowHeight:
				self._rowHeight = val
				self.SetDefaultRowSize(val, True)
				self.ForceRefresh()
				# Persist the new size
				app = self.Application
				form = self.Form
				if app is not None and form is not None:
					app.setUserSetting("%s.%s.%s" % (
							form.Name, self.Name, "RowSize"), val)
		else:
				self._properties["RowHeight"] = val


	def _getRowLables(self):
		if hasattr(self, "_rowLabels"):
			v = self._rowLabels
		else:
			v = self._rowLabels = []
		return v
	
	def _setRowLables(self, val):
		self._rowLabels = val
		self.fillGrid()


	def _getRowLabelWidth(self):
		if hasattr(self, "_rowLabelWidth"):
			v = self._rowLabelWidth
		else:
			v = self._rowLabelWidth = self.GetDefaultRowLabelSize()
		return v
		
	def _setRowLabelWidth(self, val):
		if self._constructed():
			self._rowLabelWidth = val
			if self.ShowRowLabels:
				self.SetRowLabelSize(val)
		else:
			self._properties["RowLabelWidth"] = val


	def _getSameSizeRows(self):
		if hasattr(self, "_sameSizeRows"):
			v = self._sameSizeRows
		else:
			v = self._sameSizeRows = True
		return v

	def _setSameSizeRows(self, val):
		self._sameSizeRows = bool(val)


	def _getSearchDelay(self):
		if hasattr(self, "_searchDelay"):
			v = self._searchDelay
		else:
			v = self._searchDelay = None
		return v

	def _setSearchDelay(self, val):
		self._searchDelay = val
		

	def _getSearchable(self):
		try:
			v = self._searchable
		except:
			v = self._searchable = True
		return v

	def _setSearchable(self, val):
		self._searchable = bool(val)


	def _getSelectionForeColor(self):
		return self._selectionForeColor

	def _setSelectionForeColor(self, val):
		self._selectionForeColor = val
		if isinstance(val, basestring):
			val = dColors.colorTupleFromName(val)
		self.SetSelectionForeground(val)


	def _getSelectionBackColor(self):
		return self._selectionBackColor

	def _setSelectionBackColor(self, val):
		self._selectionBackColor = val
		if isinstance(val, basestring):
			val = dColors.colorTupleFromName(val)
		self.SetSelectionBackground(val)

	
	def _getSelectionMode(self):
		return self._selectionMode

	def _setSelectionMode(self, val):
		self._selectionMode = val
		val2 = val.lower().strip()[:2]
		if val2 == "ro":
			self.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)
		elif val2 == "co":
			self.SetSelectionMode(wx.grid.Grid.wxGridSelectColumns)
		else:
			self.SetSelectionMode(wx.grid.Grid.wxGridSelectCells)


	def _getShowColumnLabels(self):
		return self._showColumnLabels

	def _setShowColumnLabels(self, val):
		if self._constructed():
			self._showColumnLabels = val
			if val:
				self.SetColLabelSize(self.ColumnLabelHeight)
			else:
				self.SetColLabelSize(0)
		else:
			self._properties["ShowColumnLabels"] = val


	def _getShowCellBorders(self):
		return self.GridLinesEnabled()

	def _setShowCellBorders(self, val):
		if self._constructed():
			self.EnableGridLines(val)
		else:
			self._properties["ShowCellBorders"] = val


	def _getShowRowLabels(self):
		if hasattr(self, "_showRowLabels"):
			v = self._showRowLabels
		else:
			v = self._showRowLabels = False
		return v

	def _setShowRowLabels(self, val):
		if self._constructed():
			self._showRowLabels = val
			if val:
				self.SetRowLabelSize(self.RowLabelWidth)
			else:
				self.SetRowLabelSize(0)
		else:
			self._properties["ShowRowLabels"] = val


	def _getSortable(self):
		try:
			v = self._sortable
		except:
			v = self._sortable = True
		return v

	def _setSortable(self, val):
		self._sortable = bool(val)


	def _getTable(self):
		## pkm: we can't call this until after the grid is fully constructed. Need to fix.
		try:
			tbl = self.GetTable()
		except:
			tbl = None
		if not tbl:
			tbl = dGridDataTable(self)
			self.SetTable(tbl, False)
		return tbl	

	def _setTable(self, tbl):
		if self._constructed():
			self.SetTable(tbl, True)
		else:
			self._properties["Table"] = value


	def _getVerticalScrolling(self):
		return self.GetScrollPixelsPerUnit()[1] > 0

	def _setVerticalScrolling(self, val):
		if self._constructed():
			if val:
				self.SetScrollRate(self.GetScrollPixelsPerUnit()[0], 20)
			else:
				self.SetScrollRate(self.GetScrollPixelsPerUnit()[0], 0)
			self.refresh()
		else:
			self._properties["VerticalScrolling"] = val


	ActivateEditorOnSelect = property(
			_getActivateEditorOnSelect, _setActivateEditorOnSelect, None,
			_("Specifies whether the cell editor, if any, is activated upon cell selection."))

	AlternateRowColoring = property(_getAlternateRowColoring, _setAlternateRowColoring, None,
			_("""When True, alternate rows of the grid are colored according to 
			the RowColorOdd and RowColorEven properties  (bool)"""))
	
	CellHighlightWidth = property(_getCellHighlightWidth, _setCellHighlightWidth, None,
			_("Specifies the width of the cell highlight box."))

	ColumnClass = property(_getColumnClass, _setColumnClass, None, 
			_("""Class to instantiate when a change to ColumnCount requires
			additional columns to be created. Default=dColumn.  (dColumn subclass)""") )
	
	ColumnCount = property(_getColumnCount, _setColumnCount, None, 
			_("Number of columns in the grid.  (int)") )
	
	Columns = property(_getColumns, None, None,
			_("List of dColumns.  (list)"))

	CurrentCellValue = property(_getCurrCellVal, _setCurrCellVal, None,
			_("Value of the currently selected grid cell  (varies)") )
			
	CurrentColumn = property(_getCurrentColumn, _setCurrentColumn, None,
			_("Currently selected column index. (int)") )
	
	CurrentField = property(_getCurrentField, _setCurrentField, None,
			_("Field for the currently selected column  (str)") )
			
	CurrentRow = property(_getCurrentRow, _setCurrentRow, None,
			_("Currently selected row  (int)") )

	DataSet = property(_getDataSet, _setDataSet, None,
			_("""The set of data displayed in the grid.  (set of dicts)

				When DataSource isn't defined, setting DataSet to a set of dicts,
				such as what you get from calling dBizobj.getDataSet(), will
				define the source of the data that the grid displays.

				If DataSource is defined, DataSet is read-only and returns the dataSet
				from the bizobj."""))
			
	DataSource = property(_getDataSource, _setDataSource, None,
			_("""The source of the data to display in the grid.  (str)

				This corresponds to a bizobj with a matching DataSource on the form,
				and setting this makes it impossible to set DataSet."""))
			
	Editable = property(_getEditable, _setEditable, None,
			_("""This setting enables/disables cell editing globally.  (bool)

			When False, no cells will be editable by the user. When True, cells in 
			columns set as Editable	will be editable by the user. Note that grids 
			and columns are both set with Editable=False by default, so to enable 
			cell editing you need to turn	it on in the appropriate column as well 
			as in the grid.""") )
			
	Encoding = property(_getEncoding, None, None,
			_("Name of encoding to use for unicode  (str)") )
			
	HeaderBackgroundColor = property(_getHeaderBackgroundColor, _setHeaderBackgroundColor, None,
			_("""Optional color for the background of the column headers.  (str or None)

			This is only the default: setting the corresponding dColumn property will
			override.""") )

	HeaderForegroundColor = property(_getHeaderForegroundColor, _setHeaderForegroundColor, None,
			_("""Optional color for the foreground (text) of the column headers.  (str or None)

			This is only the default: setting the corresponding dColumn property will
			override.""") )

	HeaderHorizontalAlignment = property(_getHeaderHorizontalAlignment, _setHeaderHorizontalAlignment, None,
			_("""The horizontal alignment of the header captions. ('Left', 'Center', 'Right')

			This is only the default: setting the corresponding dColumn property will
			override.""") )

	HeaderVerticalAlignment = property(_getHeaderVerticalAlignment, _setHeaderVerticalAlignment, None,
			_("""The vertical alignment of the header captions. ('Top', 'Center', 'Bottom')

			This is only the default: setting the corresponding dColumn property will
			override.""") )

	HeaderHeight = property(_getHeaderHeight, _setHeaderHeight, None, 
			_("Height of the column headers.  (int)") )
	
	HorizontalScrolling = property(_getHorizontalScrolling, _setHorizontalScrolling, None,
			_("Is scrolling enabled in the horizontal direction?  (bool)"))

	NoneDisplay = property(_getNoneDisp, None, None, 
			_("Text to display for null (None) values.  (str)") )
	
	RowColorEven = property(_getRowColorEven, _setRowColorEven, None,
			_("""When alternate row coloring is active, controls the color 
			of the even rows  (str or tuple)"""))
	
	RowColorOdd = property(_getRowColorOdd, _setRowColorOdd, None,
			_("""When alternate row coloring is active, controls the color 
			of the odd rows  (str or tuple)"""))
	
	RowCount = property(_getRowCount, None, None, 
			_("Number of rows in the grid.  (int)") )

	RowHeight = property(_getRowHeight, _setRowHeight, None,
			_("Row Height for all rows of the grid  (int)"))

	RowLabels = property(_getRowLables, _setRowLables, None, 
			_("List of the row labels.  (list)") )
	
	RowLabelWidth = property(_getRowLabelWidth, _setRowLabelWidth, None,
			_("""Width of the label on the left side of the rows. This only changes
			the grid if ShowRowLabels is True.  (int)"""))

	SameSizeRows = property(_getSameSizeRows, _setSameSizeRows, None,
			_("""Is every row the same height?  (bool)"""))

	Searchable = property(_getSearchable, _setSearchable, None,
			_("""Specifies whether the columns can be searched.   (bool)

				If True, columns that have their Searchable properties set to True
				will be searchable. 

				Default: True"""))

	SearchDelay = property(_getSearchDelay, _setSearchDelay, None,
			_("""Specifies the delay before incrementeal searching begins.  (int or None)

				As the user types, the search string is modified. If the time between
				keystrokes exceeds SearchDelay (milliseconds), the search will run and 
				the search string	will be cleared.

				If SearchDelay is set to None (the default), Application.SearchDelay will
				be used.""") )
	
	SelectionBackColor = property(_getSelectionBackColor, _setSelectionBackColor, None,
			_("BackColor of selected cells  (str or RGB tuple)"))
	
	SelectionForeColor = property(_getSelectionForeColor, _setSelectionForeColor, None,
			_("ForeColor of selected cells  (str or RGB tuple)"))
	
	SelectionMode = property(_getSelectionMode, _setSelectionMode, None,
			_("""Determines how the grid displays selections.  (str)
			Options are:
				Cells/Plain/None - no row/col highlighting	(default)
				Row - the row of the selected cell is highlighted
				Column - the column of the selected cell is highlighted

			The highlight color is determined by the SelectionBackColor and
			SelectionForeColor properties.
			"""))

	ShowColumnLabels = property(_getShowColumnLabels, _setShowColumnLabels, None,
			_("Are column labels shown?  (bool)") )

	ShowRowLabels = property(_getShowRowLabels, _setShowRowLabels, None,
			_("Are row labels shown?  (bool)") )

	ShowCellBorders = property(_getShowCellBorders, _setShowCellBorders, None,
			_("Are borders around cells shown?  (bool)") )

	Sortable = property(_getSortable, _setSortable, None,
			_("""Specifies whether the columns can be sorted. If True, 
			and if the column's Sortable property is True, the column 
			will be sortable. Default: True  (bool)"""))

	VerticalScrolling = property(_getVerticalScrolling, _setVerticalScrolling, None,
			_("Is scrolling enabled in the vertical direction?  (bool)"))

	_Table = property(_getTable, _setTable, None,
			_("Reference to the internal table class  (dGridDataTable)") )

	##----------------------------------------------------------##
	##               end: property definitions                  ##
	##----------------------------------------------------------##


class _dGrid_test(dGrid):
	def initProperties(self):
		self.DataSet = [{"name" : "Ed Leafe", "age" : 47, "coder" :  True, "color": "brown"},
				{"name" : "Mike Leafe", "age" : 18, "coder" :  False, "color": "purple"},
				{"name" : "Dan Leafe", "age" : 13, "coder" :  False, "color": "green"}]
		self.Width = 360
		self.Height = 150
		self.Editable = True
		#self.Sortable = False
		#self.Searchable = False


	def afterInit(self):
		_dGrid_test.doDefault()

		col = dColumn(self, Name="Geek", Order=10, DataField="coder",
				DataType="bool", Width=60, Caption="Geek?", Sortable=False,
				Searchable=False, Editable=True)
		self.addColumn(col)

		col.CustomRenderers[1] = col.stringRendererClass
		col.CustomEditors[1] = col.stringEditorClass
		col.HeaderFontBold = False

		col = dColumn(self, Name="Person", Order=20, DataField="name",
				DataType="string", Width=200, Caption="Customer Name",
				Sortable=True, Searchable=True, Editable=False)
		self.addColumn(col)
		
		col.HeaderFontItalic = True
		col.HeaderBackgroundColor = "orange"
		col.HeaderVerticalAlignment = "Top"
		col.HeaderHorizontalAlignment = "Left"

		col = dColumn(self, Name="Age", Order=30, DataField="age",
				DataType="integer", Width=40, Caption="Age",
				Sortable=True, Searchable=False, Editable=True)
		self.addColumn(col)

		col = dColumn(self, Name="Color", Order=40, DataField="color",
				DataType="string", Width=40, Caption="Favorite Color",
				Sortable=True, Searchable=False, Editable=True)
		self.addColumn(col)

		col.ListEditorChoices = ["green", "brown", "purple"]
		col.CustomEditorClass = col.listEditorClass

		col.HeaderVerticalAlignment = "Bottom"
		col.HeaderHorizontalAlignment = "Right"
		col.HeaderForegroundColor = "brown"

		self.RowLabels = ["a", "b", "3"]
		#self.ShowRowLabels = True

if __name__ == '__main__':
	class TestForm(dabo.ui.dForm):
		def afterInit(self):
			self.BackColor = "khaki"
			g = self.grid = _dGrid_test(self, RegID="sampleGrid")
			self.Sizer.append(g, 1, "x", border=40, borderFlags="all")
			self.Sizer.appendSpacer(10)
			
			chk = dabo.ui.dCheckBox(self, Caption="Edit Table", RegID="geekEdit",
					DataSource="sampleGrid", DataField="Editable")
			self.Sizer.append(chk, halign="Center")
			chk.refresh()

			
	app = dabo.dApp()
	app.MainFormClass = TestForm
	app.setup()
	app.start()
