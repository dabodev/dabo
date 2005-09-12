""" Grid.py

This is the base Dabo dGrid, usually used for showing a set of records
in a dataset, and optionally allowing the fields to be edited.
"""
import datetime
import locale
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

# See if the new decimal module is present. This is necessary 
# because if running under Python 2.4 or later and using MySQLdb,
# some values will be returned as decimals, and we need to 
# conditionally convert them for display.
_USE_DECIMAL = True
try:
	from decimal import Decimal
except ImportError:
	_USE_DECIMAL = False

# wx versions < 2.6 don't have the GetDefaultPyEncoding function:
try:
	defaultEncoding = wx.GetDefaultPyEncoding()
except AttributeError:
	defaultEncoding = "latin-1"


class dGridDataTable(wx.grid.PyGridTableBase):
	def __init__(self, parent):
		super(dGridDataTable, self).__init__()

		self.grid = parent
		self.bizobj = None		#self.grid.Form.getBizobj(parent.DataSource) 
		# Holds a copy of the current data to prevent unnecessary re-drawing
		self.__currData = []
		self._initTable()


	def _initTable(self):
		self.relativeColumns = []
		self.colLabels = []
		self.colNames = []
		self.colDefs = []
		self.dataTypes = []
		self.imageBaseThumbnails = []
		self.imageLists = {}
		self.data = []
		self.rowLabels = []
		# Call the hook
		self.initTable()


	def initTable(self):
		pass


	def setRowLabels(self, rowLbls):
		self.rowLabels = rowLbls
		
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
			return self.grid.Columns[col]._gridColAttr.Clone()
		except IndexError:
			# Something is out of order in the setting up of the grid: the grid table
			# has columns, but self.grid.Columns doesn't know about it yet. Just return
			# the default:
			return self.grid._defaultGridColAttr.Clone()
			# (further testing reveals that this really isn't a problem: the grid is 
			#  just empty - no columns or rows added yet)

	def GetRowLabelValue(self, row):
		try:
			return self.rowLabels[row]
		except:
			return ""
	
	def GetColLabelValue(self, col):
		try:
			return self.colDefs[col].Caption
		except:
			return ""
		
			
	def setColumns(self, colDefs):
		"""Create columns based on passed list of column definitions."""
		# Column order should already be in the definition. If there is a custom
		# setting by the user, override it.
		idx = 0
		colFlds = []

		# See if the defs have changed. If not, update any column info,
		# and return. If so, clear the data to force a re-draw of the table.
		if colDefs == self.colDefs:
			self.setColumnInfo()
			return
		else:
			self.__currData = []
		for col in colDefs:
			nm = col.Field
			while not nm:
				nm = str(idx)
				idx += 1
				if nm in colFlds:
					nm = ""
			colFlds.append(nm)
			colName = "Column_%s" % nm
			app = self.grid.Application
			pos = None
			if app is not None:
				pos = app.getUserSetting("%s.%s.%s.%s" % (
						self.grid.Form.Name, 
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
		self.colLabels = [col.Caption for col in self.colDefs]
		self.dataTypes = [self.convertType(col.DataType) 
				for col in self.colDefs]
		self.colNames = [col.Field for col in self.colDefs]


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
			return typ == self.dataTypes[col]

	def CanSetValueAs(self, row, col, typ):
		if self.grid.useCustomSetValue:
			return self.grid.customCanSetValueAs(row, col, typ)
		else:
			return typ == self.dataTypes[col]

		
	def fillTable(self, force=False):
		""" Fill the grid's data table to match the data set."""
		rows = self.GetNumberRows()
		oldRow = self.grid.CurrentColumn  # current row per the grid
		oldCol = self.grid.CurrentColumn  # current column per the grid
		if not oldCol:
			oldCol = 0
		# Get the data from the grid.
		dataSet = self.grid.getDataSet()
		if not force:
			if self.__currData == dataSet:
				# Nothing's changed; no need to re-fill the table
				return
		else:
			self.__currData = dataSet
		
		## pkm: Discovered this call isn't needed. Not sure if it improves anything
		##      without it, however:
		#self.Clear()

		self.data = []
		encod = self.grid.Encoding
		for record in dataSet:
			recordFmt = self.formatRowForData(record)
			self.data.append(recordFmt)
		self.grid.BeginBatch()
		# The data table is now current, but the grid needs to be
		# notified.
		if len(self.data) > rows:
			# tell the grid we've added row(s)
			num = len(self.data) - rows
			msg = wx.grid.GridTableMessage(self,       # The table
				wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED,  # what we did to it
				num)                                     # how many
			
		elif rows > len(self.data):
			# tell the grid we've deleted row(s)
			num = rows - len(self.data) 
			msg = wx.grid.GridTableMessage(self,      # The table
				wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED,  # what we did to it
				0,                                      # position
				num)                                    # how many
		else:
			msg = None
		if msg:        
			self.grid.ProcessTableMessage(msg)
		# Column widths come from multiple places. In decreasing precedence:
		#   1) dApp user settings, 
		#   2) the fieldSpecs
		#   3) have the grid autosize
		for idx, col in enumerate(self.colDefs):
			fld = col.Field
			colName = "Column_%s" % fld
			gridCol = idx
			fieldType = col.DataType.lower()
			app = self.grid.Application

			# 1) Try to get the column width from the saved user settings:
			width = None
			if app is not None:
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
		for ii in range(len(self.rowLabels)):
			self.SetRowLabelValue(ii, self.rowLabels[ii])
		self.grid.EndBatch()

	
	def formatRowForData(self, rec):
		"""Takes a row from a record set, and contructs a list
		that matches the column layout. Also encodes all unicode
		values to properly display.
		"""
		returnFmt = []
		for col in self.colDefs:
			fld = col.Field
			if rec.has_key(fld):
				recVal = rec[fld]
				recType = type(recVal)
				if recVal is None:
					recVal = self.grid.NoneDisplay
				recType = type(recVal)
				if isinstance(recVal, basestring):
					if recType is unicode:
						recVal = recVal.encode(defaultEncoding)
					else:
						try:
							recVal = unicode(recVal, defaultEncoding)
						except:
							encs = ("utf-8", "latin-1")
							ok = False
							for enc in encs:
								if enc != defaultEncoding:
									try:
										recVal = unicode(recVal, enc)
										ok = True
									except:
										pass
							if not ok:
								# Not sure how to handle this. For now, just use a dummy value
								#print "ENCODING PROBLEM:", recVal, defaultEncoding
								recVal = "##encoding problem##"
					# Limit to first 'n' chars...
					recVal = recVal[:self.grid.stringDisplayLen]
				elif col.DataType.lower() == "bool":
					# coerce to bool (could have been 0/1)
					if isinstance(recVal, basestring):
						recVal = bool(int(recVal))
					else:
						recVal = bool(recVal)
			else:
				# If there is no such value, don't display anything
				recVal = ""
			returnFmt.append(recVal)
		return returnFmt
	
	
	def addTempRow(self, row):
		"""Used by the autosize routine to add an individual row 
		containing the captions for the columns so that the autosize
		function takes them into account. It is then followed by a
		call to self.removeTempRow() to restore the data back to its
		original state.
		"""
		rowFmt = self.formatRowForData(row)
		self.data.append(rowFmt)
		self.grid.BeginBatch()
		msg = wx.grid.GridTableMessage(self,
				wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED, 1)
		self.grid.ProcessTableMessage(msg)
		self.grid.EndBatch()


	def removeTempRow(self):
		"""Removes the temp row that was added in a prior call to 
		addTempRow(). This method assumes that the last row
		in the data set is the row to remove.
		"""
		tmp = self.data.pop()
		self.grid.BeginBatch()
		msg = wx.grid.GridTableMessage(self,
				wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED,
				len(self.data), 1)
		self.grid.ProcessTableMessage(msg)
		self.grid.EndBatch()
	

	# The following methods are required by the grid, to find out certain
	# important details about the underlying table.                
	def GetNumberRows(self):
		try:
			num = len(self.data)
		except:
			num = 0
		return num

	def GetNumberCols(self):
		try:
			num = len(self.colLabels)
		except:
			num = 0
		return num


	def IsEmptyCell(self, row, col):
		try:
			return not self.data[row][col]
		except IndexError:
			return True

	def GetValue(self, row, col):
		try:
			ret = self.data[row][col]
		except:
			ret = ""
		return ret

	def SetValue(self, row, col, value):
		self.data[row][col] = value



class dColumn(dabo.common.dObject):
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
		self._gridColAttr = parent._defaultGridColAttr.Clone()

		super(dColumn, self).__init__(properties, *args, **kwargs)


	def _beforeInit(self):
		super(dColumn, self)._beforeInit()
		# Define the cell renderer and editor classes
		self.stringRendererClass = wx.grid.GridCellStringRenderer
		self.boolRendererClass = wx.grid.GridCellBoolRenderer
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
			"decimal" : self.decimalRendererClass,
			"float" : self.floatEditorClass, 
			"list" : self.listEditorClass }
		

	def _afterInit(self):
		self._isConstructed = True
		super(dColumn, self)._afterInit()
		
		
	def _constructed(self):
		return self._isConstructed


	def _persist(self, prop):
		"""Persist the current prop setting to the user settings table."""
		
		app = self.Application
		grid = self.Parent
		colName = "column_%s" % self.Field
		val = getattr(self, prop)
		settingName = "%s.%s.%s.%s" % (grid.Form.Name, grid.Name, colName, prop)

		app.setUserSetting(settingName, val)


	def changeMsg(self, prop):
		if self.Parent:
			self.Parent.onColumnChange(self, prop)
	
	
	def _getGridColumnIndex(self):
		"""Return our column index in the grid, or -1."""
		t = self.Parent._Table
		gridCol = -1
		if t is not None:
			for idx, dCol in enumerate(t.colDefs):
				if dCol == self:
					gridCol = idx
					break
		return gridCol

	
	def _updateEditor(self):
		"""The Field, DataType, or CustomEditor has changed: set in the attr"""
		editor = self.Editor
		if editor is not None:
			kwargs = {}
			if editor in (wx.grid.GridCellChoiceEditor,):
				kwargs["choices"] = self.ListEditorChoices
			editor = editor(**kwargs)
		self._gridColAttr.SetEditor(editor)
		

	def _updateRenderer(self):
		"""The Field, DataType, or CustomRenderer has changed: set in the attr"""
		renderer = self.Renderer
		if renderer is not None:
			renderer = renderer()
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
			if self.Parent:
				## note: may want to use RefreshRect just on the column header region
				self.Parent.refresh()
		else:
			self._properties["Caption"] = val

	def _getCustomEditor(self):
		try:
			v = self._customEditor
		except AttributeError:
			v = self._customEditor = None
		return v
	def _setCustomEditor(self, val):
		if self._constructed():
			self._customEditor = val
			self._updateEditor()
		else:
			self._properties["CustomEditor"] = val

	def _getCustomRenderer(self):
		try:
			v = self._customRenderer
		except AttributeError:
			v = self._customRenderer = None
		return v
	def _setCustomRenderer(self, val):
		if self._constructed():
			self._customRenderer = val
			self._updateRenderer()
		else:
			self._properties["CustomRenderer"] = val

	def _getDataType(self):
		try:
			v = self._dataType
		except AttributeError:
			v = self._dataType = ""
		return v
	def _setDataType(self, val):
		if self._constructed():
			self._dataType = val
			if "Automatic" in self.HorizontalCellAlignment:
				self._setAutoHorizontalCellAlignment()
			self._updateRenderer()
			self._updateEditor()
			#self.changeMsg("DataType")  ## don't think this is necessary, now that the attr handles.
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

	def _getEditor(self):
		v = self.CustomEditor
		if v is None:
			v = self.defaultEditors.get(self.DataType)
		return v

	def _getField(self):
		try:
			v = self._field
		except AttributeError:
			v = self._field = ""
		return v
	def _setField(self, val):
		if self._constructed():
			self._field = val
			self._updateRenderer()
			self._updateEditor()
			self.changeMsg("Field")
		else:
			self._properties["Field"] = val

	def _getHeaderBackgroundColor(self):
		try:
			v = self._headerBackgroundColor
		except AttributeError:
			v = self._headerBackgroundColor = None
		return v
	def _setHeaderBackgroundColor(self, val):
		if self._constructed():
			if isinstance(val, basestring):
				try:
					val = dColors.colorTupleFromName(val)
				except: 
					pass
			self._headerBackgroundColor = val
			if self.Parent:
				self.Parent.refresh()
		else:
			self._properties["HeaderBackgroundColor"] = val
	
	def _getHorizontalCellAlignment(self):
		try:
			auto = self._autoHorizontalCellAlignment
		except AttributeError:
			auto = self._autoHorizontalCellAlignment = True
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
	def _setAutoHorizontalCellAlignment(self):
		dt = self.DataType
		if isinstance(dt, basestring):
			if dt in ("decimal", "float", "long", "integer"):
				self._setHorizontalCellAlignment("Right", _autoAlign=True)
		
	def _setHorizontalCellAlignment(self, val, _autoAlign=False):
		if self._constructed():
			val = self._expandPropStringValue(val, ("Automatic", "Left", "Right", "Center"))
			if val == "Automatic" and not _autoAlign:
				self._autoHorizontalCellAlignment = True
				self._setAutoHorizontalCellAlignment()
				return
			if val != "Automatic" and not _autoAlign:
				self._autoHorizontalCellAlignment = False
			mapping = {"Left": wx.ALIGN_LEFT, "Right": wx.ALIGN_RIGHT,
					 "Center": wx.ALIGN_CENTRE}
			try:
				wxHorAlign = mapping[val]
			except KeyError:
				wxHorAlign = mapping["Left"]
				val = "Left"
			wxVertAlign = self._gridColAttr.GetAlignment()[1]
			self._gridColAttr.SetAlignment(wxHorAlign, wxVertAlign)
			if self.Parent:
				self.Parent.refresh()
		else:
			self._properties["HorizontalCellAlignment"] = val

	
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


	def _getRenderer(self):
		v = self.CustomRenderer
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
			self.changeMsg("Order")
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


	def _getVerticalCellAlignment(self):
		mapping = {wx.ALIGN_TOP: "Top", wx.ALIGN_BOTTOM: "Bottom",
	             wx.ALIGN_CENTRE: "Center"}
		wxAlignment = self._gridColAttr.GetAlignment()[1]
		try:
			val = mapping[wxAlignment]
		except KeyError:
			val = "Top"
		return val
	def _setVerticalCellAlignment(self, val):
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
			if self.Parent:
				self.Parent.refresh()
		else:
			self._properties["VerticalCellAlignment"] = val

	def _getWidth(self):
		try:
			v = self._width
		except AttributeError:
			v = self._width = -1
		if self.Parent:
			idx = self._GridColumnIndex
			if idx >= 0:
				# Make sure the grid is in sync:
				self.Parent.SetColSize(self._GridColumnIndex, v)
		return v
	def _setWidth(self, val):
		if self._constructed():
			self._width = val
			if self.Parent:
				idx = self._GridColumnIndex
				if idx >= 0:
					# Change the size in the wx grid:
					self.Parent.SetColSize(self._GridColumnIndex, val)
		else:
			self._properties["Width"] = val
	

	Caption = property(_getCaption, _setCaption, None,
			_("Caption displayed in this column's header  (str)") )

	CustomEditor = property(_getCustomEditor, _setCustomEditor, None,
			_("""Custom Editor for this column. Default: None. Set this to override 
			the default editor, which Dabo will select based on the data type of 
			the field.  (varies)"""))

	CustomRenderer = property(_getCustomRenderer, _setCustomRenderer, None,
			_("""Custom Renderer for this column. Default: None. Set this to 
			override the default renderer, which Dabo will select based on the 
			data type of the field.  (varies)"""))

	DataType = property(_getDataType, _setDataType, None,
			_("Description of the data type for this column  (str)") )

	Editable = property(_getEditable, _setEditable, None,
			_("""If True, and if the grid is set as Editable, the cell values in this
				column are editable by the user. If False, the cells in this column 
				cannot be edited no matter what the grid setting is. When editable, 
				incremental searching will not be enabled, regardless of the 
				Searchable property setting.  (bool)""") )

	Editor = property(_getEditor, None, None,
			_("""Returns the editor used for cells in the column. This will be 
				self.CustomEditor if set, or the default editor for the 
				datatype of the field.  (varies)"""))
  
	Field = property(_getField, _setField, None,
			_("Field key in the data set to which this column is bound.  (str)") )

	HeaderBackgroundColor = property(_getHeaderBackgroundColor, _setHeaderBackgroundColor, None,
			_("Optional color for the background of the column header  (str)") )

	HorizontalCellAlignment = property(_getHorizontalCellAlignment, _setHorizontalCellAlignment, None,
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

	Renderer = property(_getRenderer, None, None,
			_("""Returns the renderer used for cells in the column. This will be 
			self.CustomRenderer if set, or the default renderer for the datatype 
			of the field.  (varies)"""))
  
	Searchable = property(_getSearchable, _setSearchable, None,
			_("""Specifies whether this column's incremental search is enabled. 
			Default: True. The grid's Searchable property will override this setting.
			(bool)"""))

	Sortable = property(_getSortable, _setSortable, None,
			_("""Specifies whether this column can be sorted. Default: True. The grid's 
			Sortable property will override this setting.  (bool)"""))

	VerticalCellAlignment = property(_getVerticalCellAlignment, _setVerticalCellAlignment, None,
			_("""Vertical alignment for all cells in this column. Acceptable values 
			are 'Top', 'Center', and 'Bottom'.  (str)"""))

	Width = property(_getWidth, _setWidth, None,
			_("Width of this column  (int)") )
	
	_GridColumnIndex = property(_getGridColumnIndex)


class dGrid(wx.grid.Grid, cm.dControlMixin):
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dGrid
		preClass = wx.grid.Grid
		
		# Grab the DataSet parameter if passed
		self._passedDataSet = self.extractKey(kwargs, "DataSet")
		self.dataSet = []
		# List of Row Labels, if any
		self._rowLabels = []

		# dColumn maintains its own cell attribute object, but this is the default:
		self._defaultGridColAttr = self._getDefaultGridColAttr()

		# Columns notify the grid when their properties change
		# Sometimes the grid itself initiated the change, and doesn't
		# need to be notified.
		self._ignoreColUpdates = False

		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
		
		
	def _afterInit(self):
		self.bizobj = None
		self._header = None
		self.fieldSpecs = {}
		# This value is in milliseconds
		self._searchDelay = 600
		# When doing an incremental search, do we stop
		# at the nearest matching value?
		self.searchNearest = True
		# Do we do case-sensitive incremental searches?
		self.searchCaseSensitive = False
		# How many characters of strings do we display?
		self.stringDisplayLen = 64
		
		# Do we enforce that all rows are the same height? This
		# would normally be a property, but I'm making it a simple att
		# for now, since I don't see the immediate need for getter/setter
		# actions.
		self.SameSizeRows = True
		# Internal tracker for row height
		self._rowHeight = self.GetDefaultRowSize()

		# When calculating auto-size widths, we don't want to use
		# the normal means of getting data sets.
		self.inAutoSizeCalc = False

		self.currSearchStr = ""
		self.incSearchTimer = dabo.ui.dTimer(self)
		self.incSearchTimer.bindEvent(dEvents.Hit, self.onSearchTimer)

		self.sortedColumn = None
		self.sortOrder = ""
		self.caseSensitiveSorting = False
		# If there is a custom sort method, set this to True
		self.customSort = False

		# By default, row labels are not shown. They can be displayed
		# if desired by setting ShowRowLabels = True, and their size
		# can be adjusted by setting RowLabelWidth = <width>
		self._rowLabelWidth = self.GetDefaultRowLabelSize()
		self._showRowLabels = False
		self.SetRowLabelSize(0)
		self._editable = False
		self.EnableEditing(self._editable)
		
		# These need to be set to True, and custom methods provided,
		# if a grid with variable types in a single column is used.
		self.useCustomGetValue = False
		self.useCustomSetValue = False
		
		# Type of encoding to use with unicode data
		self.defaultEncoding = defaultEncoding
		# What color should the little sort indicator arrow be?
		self.sortArrowColor = "Silver"

		self._headerDragging = False    # flag used by mouse motion event handler
		self._headerDragFrom = 0
		self._headerDragTo = 0
		self._headerSizing = False
		#Call the default behavior
		super(dGrid, self)._afterInit()
		
		# Set the header props/events
		self.initHeader()		
		# If a data set was passed to the constructor, create the grid
		self.buildFromDataSet(self._passedDataSet)


	def initEvents(self):
		self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.__onWxMouseLeftDoubleClick)
		self.Bind(wx.grid.EVT_GRID_ROW_SIZE, self.__onWxGridRowSize)
		self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.__onWxGridSelectCell)
		self.Bind(wx.grid.EVT_GRID_COL_SIZE, self.__onWxGridColSize)
		self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.__onWxMouseLeftClick)
		self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.__onWxMouseRightClick)
		self.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.__onWxGridCellChange)

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
		self.bindEvent(dEvents.GridSelectCell, self._onGridSelectCell)
		self.bindEvent(dEvents.GridColSize, self._onGridColSize)
		self.bindEvent(dEvents.GridCellEdited, self._onGridCellEdited)

		## wx.EVT_CONTEXT_MENU doesn't appear to be working for dGrid yet:
#		self.bindEvent(dEvents.GridContextMenu, self._onContextMenu)
		self.bindEvent(dEvents.GridMouseRightClick, self._onGridMouseRightClick)


	def initHeader(self):
		""" Initialize behavior for the grid header region."""
		header = self.Header
		self.defaultHdrCursor = header.GetCursor()
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


		self.bindEvent(dEvents.GridHeaderMouseLeftDown, self._onGridHeaderMouseLeftDown)
		self.bindEvent(dEvents.GridHeaderPaint, self._onHeaderPaint)
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
			fld = self.Columns[col].Field
			self.dataSet[row][fld] = val
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
	#pkm: I wonder about putting these in dColumn as setEditorForRow() instead. Thoughts?
	def setEditorForCell(self, row, col, edt):
		self.SetCellEditor(row, col, edt)
	def setRendererForCell(self, row, col, rnd):
		print "SET RENDER", row, col, rnd
		self.SetCellRenderer(row, col, rnd)
				
		
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
		if app is not None:
			s = app.getUserSetting("%s.%s.%s" % (self.Form.Name, 
					self.GetName(), "RowSize"))
		else:
			s = None
		if s:
			self.SetDefaultRowSize(s)
		tbl = self._Table
		
		tbl.setColumns(self.Columns)
		tbl.setRowLabels(self.RowLabels)
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
		
	
	
	def buildFromDataSet(self, ds, keyCaption=None, 
			columnsToSkip=[], colOrder={}, colWidths={}, autoSizeCols=True):
		"""This method will create a grid for a given data set.
		A 'data set' is a sequence of dicts, each containing field/
		value pairs. The columns will be taken from ds[0].keys(),
		with each column header being set to the key name, unless
		the optional keyCaption parameter is passed. This parameter
		is a 1:1 dict containing the data set keys as its keys,
		and the desired caption as the corresponding value.
		If the columnsToSkip parameter is set, any column in the 
		data with a key in that list will not be added to the grid.
		The columns will be in the order returned by ds.keys(), unless
		the optional colOrder parameter is passed. Like the keyCaption
		property, this is a 1:1 dict containing key:order.
		"""
		if not ds:
			return
#		self.Form.lockDisplay()
		origColNum = self.ColumnCount
		self._columns = []
		self.dataSet = ds
		firstRec = ds[0]
		# Dabo cursors add some columns to the data set. These
		# artifacts need to be removed. They all begin with 'dabo-'.
		colKeys = [key for key in firstRec.keys()
				if (key[:5] != "dabo-") and (key not in columnsToSkip)]
		# Update the number of columns
		colChange = len(colKeys) - origColNum 
		if colChange != 0:
			msg = ""
			if colChange < 0:
				msg = wx.grid.GridTableMessage(self._Table,
						wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED,
						origColNum-1, abs(colChange))
			else:
				msg = wx.grid.GridTableMessage(self._Table,
						wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED,
						colChange)
			if msg:
				self.BeginBatch()
				self.ProcessTableMessage(msg)
				self.EndBatch()
		# Add the columns
		self._ignoreColUpdates = True
		for colKey in colKeys:
			# Use the keyCaption values, if possible
			try:
				cap = keyCaption[colKey]
			except:
				cap = colKey
			col = dColumn(self)
			col.Caption = cap
			col.Field = colKey
			dt = col.DataType = type(firstRec[colKey])
			if dt is type(None):
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

			self._columns.append(col)
		# Populate the grid
		self.fillGrid(True)
		if autoSizeCols:
			self.autoSizeCol("all")
		self._ignoreColUpdates = False
#		self.Form.unlockDisplay()


	def autoSizeCol(self, colNum, persist=False):
		"""Set the column to the minimum width necessary to display its data.

		Set colNum='all' to auto-size all columns. Set persist=True to persist the
		fact that the column should be auto-sized to the user settings table.
		"""	
		# lock the screen
		self.lockDisplay()
		# Changing the columns' Width prop will send an update
		# message back to this grid. We want to ignore that
		self._ignoreColUpdates = True
		# We also don't want the Table's call to grid.getDataSet()
		# to wipe out our temporary changes.
		self.inAutoSizeCalc = True
		# We need to account for header caption width, too. Add
		# a row to the data set containing the header captions, and 
		# then remove the row afterwards.
		capRow = {}
		for col in self.Columns:
			capRow[col.Field] = col.Caption
		self._Table.addTempRow(capRow)
		try:
			# Having a problem with Unicode in the native
			# AutoSize() function.
			if isinstance(colNum, str):
				#They passed "all"
				self.AutoSizeColumns(setAsMin=False)
				for ii in range(len(self.Columns)):
					self.Columns[ii].Width = self.GetColSize(ii)
					if persist:
						self.Columns[ii]._persist("Width")
						
			elif isinstance(colNum, (int, long)):
				self.AutoSizeColumn(colNum, setAsMin=False)
				self.Columns[colNum].Width = self.GetColSize(colNum)
				if persist:
					self.Columns[colNum]._persist("Width")
		except:
			pass
		self._Table.removeTempRow()
		self.inAutoSizeCalc = False
		self._ignoreColUpdates = False
		self.unlockDisplay()		


	def getDataSet(self):
		"""Customize to your needs. Default is to use an internal property,
		and if that is empty, simply ask the form."""
		ret = self.dataSet
		if not ret:
			try:
				ret = self.Form.getDataSet()
			except:
				ret = []
		return ret
		

	def onColumnChange(self, col, chgType):
		"""Called by the grid columns whenever any of their properties
		are directly changed, allowing the grid to react.
		"""
		if self._ignoreColUpdates:
			# The column is being updated after a grid change, so
			# no need to update the grid again.
			return
		if self._constructed():
			# Update the grid
			self.fillGrid(True)
		

	def _paintHeader(self):
		w = self.Header
		dc = wx.ClientDC(w)
		clientRect = w.GetClientRect()
		font = dc.GetFont()

		# Thanks Roger Binns for the correction to totColSize
		totColSize = -self.GetViewStart()[0] * self.GetScrollPixelsPerUnit()[0]

		# Get the height
		ht = self.GetColLabelSize()

		for col in range(self.ColumnCount):
			dc.SetBrush(wx.Brush("WHEAT", wx.TRANSPARENT))
			dc.SetTextForeground(wx.BLACK)
			colSize = self.GetColSize(col)
			rect = (totColSize, 0, colSize, ht)
			colObj = self.Columns[col]
			if colObj.HeaderBackgroundColor is not None:
				holdBrush = dc.GetBrush()
				dc.SetBrush(wx.Brush(colObj.HeaderBackgroundColor, wx.SOLID))
				dc.DrawRectangle(rect[0] - (col != 0 and 1 or 0), 
						rect[1], 
						rect[2] + (col != 0 and 1 or 0), 
						rect[3])
				dc.SetBrush(holdBrush)
			totColSize += colSize

			if self.Columns[col].Field == self.sortedColumn:
				font.SetWeight(wx.BOLD)
				# draw a triangle, pointed up or down, at the top left 
				# of the column. TODO: Perhaps replace with prettier icons
				left = rect[0] + 3
				top = rect[1] + 3

				dc.SetBrush(wx.Brush(self.sortArrowColor, wx.SOLID))
				if self.sortOrder == "DESC":
					# Down arrow
					dc.DrawPolygon([(left,top), (left+6,top), (left+3,top+6)])
				elif self.sortOrder == "ASC":
					# Up arrow
					dc.DrawPolygon([(left+3,top), (left+6, top+6), (left, top+6)])
				else:
					# Column is not sorted, so don't draw.
					pass    
			else:
				font.SetWeight(wx.NORMAL)

# 			dc.SetFont(font)
# 			dc.DrawLabel("%s" % self.GetTable().colLabels[col],
# 					rect, wx.ALIGN_CENTER | wx.ALIGN_TOP)


	def MoveColumn(self, colNum, toNum):
		""" Move the column to a new position."""
		self._ignoreColUpdates = True
		oldCol = self.Columns[colNum]
		self._columns.remove(oldCol)
		if toNum > colNum:
			self._columns.insert(toNum-1, oldCol)
		else:
			self._columns.insert(toNum, oldCol)
		for col in self.Columns:
			col.Order = self.Columns.index(col) * 10
			col._persist("Order")
		self.fillGrid(True)
		self._ignoreColUpdates = False


	def onSearchTimer(self, evt):
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


	def processSort(self, gridCol=None):
		""" Sort the grid column.

		Toggle between ascending and descending. If the grid column index isn't 
		passed, the currently active grid column will be sorted.
		"""
		if gridCol == None:
			gridCol = self.CurrentColumn
			
		if isinstance(gridCol, dColumn):
			canSort = (self.Sortable and gridCol.Sortable)
			columnToSort = gridCol
			sortCol = self.Columns.index(gridCol)
			dataType = self.Columns[gridCol].DataType
		else:
			sortCol = gridCol
			columnToSort = self.Columns[gridCol].Field
			canSort = (self.Sortable and self.Columns[gridCol].Sortable)
			dataType = None  ## will hunt for the dataType below

		if not canSort:
			# Some columns, especially those with mixed values,
			# should not be sorted.
			return
			
		sortOrder="ASC"
		if columnToSort == self.sortedColumn:
			sortOrder = self.sortOrder
			if sortOrder == "ASC":
				sortOrder = "DESC"
			else:
				sortOrder = "ASC"
		self.sortOrder = sortOrder
		self.sortedColumn = columnToSort
		
		if self.customSort:
			# Grids tied to bizobj cursors may want to use their own
			# sorting.
			self.sort()
		else:
			# Create the list to hold the rows for sorting
			caseSensitive = self.caseSensitiveSorting
			sortList = []
			rowNum = 0
			for row in self.dataSet:
				if self.RowLabels:
					sortList.append([row[columnToSort], row, self.RowLabels[rowNum]])
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
			self.dataSet = newRows
			self.RowLabels = newLabels

		## pkm: We don't need to refill the grid, just the data table. This change
		##      saves about 1/10 of a sec. on a grid with 2200 rows and 6 fields.
		#self.fillGrid(True)
		self._Table.fillTable(False)

		## I'm also going to experiment with ditching the table.data list and just 
		## linking directly to the dataset. Then when requery/sort/add/delete 
		## operations happen, we just need to fill one dataset, not two. The other 
		## major avenue for improvement would be to implement efficient sorting,
		## which I've seen good recipes for on the internet.


	def runIncSearch(self):
		""" Run the incremental search."""
		gridCol = self.CurrentColumn
		if gridCol < 0:
			gridCol = 0
		fld = self.Columns[gridCol].Field
		if self.RowCount <= 0:
			# Nothing to seek within!
			return
		if not (self.Searchable and self.Columns[gridCol].Searchable):
			# Doesn't apply to this column.
			self.currSearchStr = ""
			return
		newRow = self.CurrentRow
		ds = self.getDataSet()
		srchStr = origSrchStr = self.currSearchStr
		self.currSearchStr = ""
		near = self.searchNearest
		caseSensitive = self.searchCaseSensitive
		# Copy the specified field vals and their row numbers to a list, and 
		# add those lists to the sort list
		sortList = []
		for i in range(0, self.RowCount):
			sortList.append( [ds[i][fld], i] )

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

		# Add a '.' to the status bar to signify that the search is
		# done, and clear the search string for next time.
		self.Form.setStatusText("Search: %s." % origSrchStr)
		self.currSearchStr = ""


	def addToSearchStr(self, key):
		""" Add a character to the current incremental search.

		Called by KeyDown when the user pressed an alphanumeric key. Add the 
		key to the current search and start the timer.        
		"""
		self.incSearchTimer.stop()
		self.currSearchStr = "".join((self.currSearchStr, key))
		self.Form.setStatusText("Search: %s"
				% self.currSearchStr)
		self.incSearchTimer.start(self.SearchDelay)


	def getColByX(self, x):
		""" Given the x-coordinate, return the column number.
		"""
		col = self.XToCol(x + (self.GetViewStart()[0]*self.GetScrollPixelsPerUnit()[0]))
		if col == wx.NOT_FOUND:
			col = -1
		return col


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
			col = dColumn(self)
		if col.Order == -1:
			col.Order = self.maxColOrder() + 10
		self._columns.append(col)
		if not inBatch:
			msg = wx.grid.GridTableMessage(self._Table,
					wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED,
					1)
			self.ProcessTableMessage(msg)
			self.fillGrid(True)


	def removeColumn(self, col=None):
		""" Removes a column to the grid. If no column is passed, 
		the last column is removed.
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
		del self._columns[colNum]
		msg = wx.grid.GridTableMessage(self._Table,
				wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED,
				colNum, 1)
		self.ProcessTableMessage(msg)
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
		

	##----------------------------------------------------------##
	##        begin: dEvent callbacks for internal use          ##
	##----------------------------------------------------------##
	def _onGridCellEdited(self, evt):
		row, col = evt.EventData["row"], evt.EventData["col"]
		rowData = self.getDataSet()[row]
		fld = self.Columns[col].Field
		newVal = self.GetCellValue(row, col)
		oldVal = rowData[fld]
		if newVal != oldVal:
			# Update the local copy of the data
			rowData[fld] = self.GetCellValue(row, col)


	def _onGridColSize(self, evt):
		"Occurs when the user resizes the width of the column."
		colNum = evt.EventData["rowOrCol"]
		col = self.Columns[colNum]
		colName = "Column_%s" % col.Field

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
		header = self.Header
		self._headerMousePosition = evt.EventData["mousePosition"]

		if dragging:
			x,y = evt.EventData["mousePosition"]

			if not headerIsSizing and (
				self.getColByX(x) == self.getColByX(x-2) == self.getColByX(x+2)):
				if not headerIsDragging:
					# A header reposition is beginning
					self._headerDragging = True
					self._headerDragFrom = (x,y)
				else:
					# already dragging.
					begCol = self.getColByX(self._headerDragFrom[0])
					curCol = self.getColByX(x)

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

			begCol = self.getColByX(self._headerDragFrom[0])
			curCol = self.getColByX(x)

			if begCol != curCol:
				if curCol > begCol:
					curCol += 1
				self.MoveColumn(begCol, curCol)
			self.Header.SetCursor(self.defaultHdrCursor)
		elif self._headerSizing:
			pass
		else:
			# we weren't dragging, and the mouse was just released.
			# Find out the column we are in based on the x-coord, and
			# do a processSort() on that column.
			col = self.getColByX(x)
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

		position = self._headerMousePosition
		menu = dabo.ui.dMenu()

		# Fill the default menu item(s):
		def _autosizeColumn(evt):
			self.autoSizeCol(self.getColByX(self._headerMousePosition[0]), persist=True)
		menu.append(_("&Autosize Column"), bindfunc=_autosizeColumn, 
		            help=_("Autosize the column based on the data in the column."))

		menu = self.fillHeaderContextMenu(menu)

		if menu is not None and len(menu.Children) > 0:
			self.PopupMenu(menu, position)
			menu.release()


	def _onGridHeaderMouseRightUp(self, evt):
		""" Occurs when the right mouse button goes up in the grid header."""
		pass

	
	def _onGridMouseRightClick(self, evt):
		# Make the popup menu appear in the location that was clicked. We init
		# the menu here, then call the user hook method to optionally fill the
		# menu. If we get a menu back from the user hook, we display it.

		# First though, make the cell the user right-clicked on the current cell:
		self.CurrentRow = evt.GetRow()
		self.CurrentColumn = evt.GetCol()

		position = evt.EventData["position"]
		menu = dabo.ui.dMenu()
		menu = self.fillContextMenu(menu)

		if menu is not None and len(menu.Children) > 0:
			self.PopupMenu(menu, position)
			menu.release()
	

	def _onGridHeaderMouseLeftDown(self, evt):
		# We need to eat this event, because the native wx grid will select all
		# rows in the column, which is a spreadsheet-like behavior, not a data-
		# aware grid-like behavior. However, let's keep our eyes out for a better
		# way to handle this, because eating events could cause some hard-to-debug
		# problems later (there could be other, more critical code, that isn't 
		# being allowed to run).
		evt.Continue = False


	def _onGridRowSize(self, evt):
		""" Occurs when the user sizes the height of the row. If the
		property 'SameSizeRows' is True, Dabo overrides the wxPython 
		default and applies that size change to all rows, not just the row 
		the user sized.
		"""
		row = evt.GetRowOrCol()
		size = self.GetRowSize(row)

		# Persist the new size
		app = self.Application
		if app is not None:
			app.setUserSetting("%s.%s.%s" % (
			                   self.Form.Name, self.Name, "RowSize"), size)
		
		if self.SameSizeRows:
			self.SetDefaultRowSize(size, True)
			self.ForceRefresh()

	
	def _onGridSelectCell(self, evt):
		""" Occurs when the grid's cell focus has changed."""
		oldRow = self.CurrentRow
		newRow = evt.EventData["row"]
		if oldRow != newRow:
			if self.bizobj:
				self.bizobj.RowNumber = newRow
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
				and (char.isalnum() or char.isspace()) and not evt.HasModifiers():
				self.addToSearchStr(char)
				# For some reason, without this the key happens twice
				evt.stop()
			else:
				if self.processKeyPress(keyCode):
					# Key was handled
					evt.stop()


	def _onHeaderPaint(self, evt):
		dabo.ui.callAfter(self._paintHeader)
	
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
		
	def __onWxGridCellChange(self, evt):
		self.raiseEvent(dEvents.GridCellEdited, evt)
		evt.Skip()

	def __onWxGridRowSize(self, evt):
		self.raiseEvent(dEvents.GridRowSize, evt)
		evt.Skip()

	def __onWxGridSelectCell(self, evt):
		self.raiseEvent(dEvents.GridSelectCell, evt)
		evt.Skip()

	def __onWxHeaderContextMenu(self, evt):
		self.raiseEvent(dEvents.GridHeaderContextMenu, evt)
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

	
	def _getDefaultGridColAttr(self):
		""" Return the GridCellAttr that will be used for all columns by default."""
		attr = wx.grid.GridCellAttr()
		attr.SetAlignment(wx.ALIGN_TOP, wx.ALIGN_LEFT)
		attr.SetReadOnly(True)
		return attr
	


	##----------------------------------------------------------##
	##              begin: property definitions                 ##
	##----------------------------------------------------------##
	def _getColumns(self):
		try:
			v = self._columns
		except AttributeError:
			v = self._columns = []
		return v


	def _getColumnCount(self):
		return len(self.Columns)

	def _setColumnCount(self, val):
		if self._constructed():
			msg = None
			if val > -1:
				colChange = val - self.ColumnCount 
				self.BeginBatch()
				if colChange == 0:
					# No change
					return
				elif colChange < 0:
					msg = wx.grid.GridTableMessage(self._Table,
							wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED,
							val, abs(colChange))
					self._columns = self.Columns[:val]
				else:
					msg = wx.grid.GridTableMessage(self._Table,
							wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED,
							colChange)
					for cc in range(colChange):
						self.addColumn(inBatch=True)
				if msg:
					self.ProcessTableMessage(msg)
				self.EndBatch()
				self.fillGrid(True)
		else:
			self._properties["ColumnCount"] = val


	def _getColLbls(self):
		ret = []
		for col in range(self.ColumnCount):
			ret.append(self.GetColLabelValue(col))
		return ret


	def _getHeader(self):
		if not self._header:
			self._header = self.GetGridColLabelWindow()
		return self._header


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
		return self.Columns[self.GetGridCursorCol()].Field

	def _setCurrentField(self, val):
		if self._constructed():
			for ii in range(len(self.Columns)):
				if self.Columns[ii].Field == val:
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


	def _getEditable(self):
		return self.IsEditable()

	def _setEditable(self, val):
		if self._constructed():
			self.EnableEditing(val)
		else:
			self._properties["Editable"] = val
	
	
	def _getEncoding(self):
		if self.bizobj:
			ret = self.bizobj.Encoding
		else:
			ret = self.defaultEncoding
		return ret
		

	def _getRowHeight(self):
		return self._rowHeight

	def _setRowHeight(self, val):
		if self._constructed():
			if val != self._rowHeight:
				self._rowHeight = val
				self.SetDefaultRowSize(val, True)
				self.ForceRefresh()
				# Persist the new size
				app = self.Application
				if app is not None:
					app.setUserSetting("%s.%s.%s" % (
					                   self.Form.Name, self.Name, "RowSize"), val)
		else:
				self._properties["RowHeight"] = val


	def _getRowLbls(self):
		return self._rowLabels
	
	def _setRowLbls(self, val):
		self._rowLabels = val
		self.fillGrid()


	def _getShowRowLabels(self):
		return self._showRowLabels

	def _setShowRowLabels(self, val):
		if self._constructed():
			self._showRowLabels = val
			if val:
				self.SetRowLabelSize(self._rowLabelWidth)
			else:
				self.SetRowLabelSize(0)
		else:
			self._properties["ShowRowLabels"] = val


	def _getRowLabelWidth(self):
		return self._rowLabelWidth

	def _setRowLabelWidth(self, val):
		if self._constructed():
			self._rowLabelWidth = val
			if self._showRowLabels:
				self.SetRowLabelSize(self._rowLabelWidth)
		else:
			self._properties["RowLabelWidth"] = val


	def _getSearchDelay(self):
		return self._searchDelay

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
		tbl = self.GetTable()
		if not tbl:
			tbl = dGridDataTable(self)
			self.SetTable(tbl, True)
		return tbl	

	def _setTable(self, tbl):
		if self._constructed():
			self.SetTable(tbl, True)
		else:
			self._properties["Table"] = value


	ColumnCount = property(_getColumnCount, _setColumnCount, None, 
			_("Number of columns in the grid.  (int)") )
	
	ColumnLabels = property(_getColLbls, None, None, 
			_("List of the column labels.  (list)") )
	
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
			
	Editable = property(_getEditable, _setEditable, None,
			_("""This setting enables/disables cell editing globally. When False, no cells
			will be editable by the user. When True, cells in columns set as Editable
			will be editable by the user. Note that grids and columns are both set
			with Editable=False by default, so to enable cell editing you need to turn
			it on in the appropriate column as well as in the grid.  (bool)""") )
			
	Encoding = property(_getEncoding, None, None,
			_("Name of encoding to use for unicode  (str)") )
			
	Header = property(_getHeader, None, None,
			_("Reference to the grid header window.  (header object?)") )
			
	HeaderHeight = property(_getHeaderHeight, _setHeaderHeight, None, 
			_("Height of the column headers.  (int)") )
	
	NoneDisplay = property(_getNoneDisp, None, None, 
			_("Text to display for null (None) values.  (str)") )
	
	RowCount = property(_getRowCount, None, None, 
			_("Number of rows in the grid.  (int)") )

	RowHeight = property(_getRowHeight, _setRowHeight, None,
			_("Row Height for all rows of the grid  (int)"))

	RowLabels = property(_getRowLbls, _setRowLbls, None, 
			_("List of the row labels.  (list)") )
	
	RowLabelWidth = property(_getRowLabelWidth, _setRowLabelWidth, None,
			_("""Width of the label on the left side of the rows. This only changes
			the grid if ShowRowLabels is True.  (int)"""))

	Searchable = property(_getSearchable, _setSearchable, None,
			_("""Specifies whether the columns can be searched. If True, 
			and if the column's Searchable property is True, the column 
			will be searchable. Default: True  (bool)"""))

	SearchDelay = property(_getSearchDelay, _setSearchDelay, None,
			_("""Delay in miliseconds between keystrokes before the 
			incremental search clears  (int)""") )
			
	ShowRowLabels = property(_getShowRowLabels, _setShowRowLabels, None,
			_("Are row labels shown?  (bool)") )

	Sortable = property(_getSortable, _setSortable, None,
			_("""Specifies whether the columns can be sorted. If True, 
			and if the column's Sortable property is True, the column 
			will be sortable. Default: True  (bool)"""))

	_Table = property(_getTable, _setTable, None,
			_("Reference to the internal table class  (dGridDataTable)") )

	##----------------------------------------------------------##
	##               end: property definitions                  ##
	##----------------------------------------------------------##


class _dGrid_test(dGrid):
	def initProperties(self):
		self.dataSet = [{"name" : "Ed Leafe", "age" : 47, "coder" :  True},
		                {"name" : "Mike Leafe", "age" : 18, "coder" :  False},
		                {"name" : "Dan Leafe", "age" : 13, "coder" :  False} ]
		self.Width = 360
		self.Height = 150
		self.Editable = True
		#self.Sortable = False
		#self.Searchable = False


	def afterInit(self):
		_dGrid_test.doDefault()

		col = dColumn(self, Name="Geek", Order=10, Field="coder",
				DataType="bool", Width=60, Caption="Geek?", Sortable=False,
				Searchable=False, Editable=True)
		self.addColumn(col)

		col = dColumn(self, Name="Person", Order=20, Field="name",
				DataType="string", Width=200, Caption="Customer Name",
				Sortable=True, Searchable=True, Editable=False)
		self.addColumn(col)
		
		col = dColumn(self, Name="Age", Order=30, Field="age",
				DataType="integer", Width=40, Caption="Age",
				Sortable=True, Searchable=False, Editable=True)
		self.addColumn(col)



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
