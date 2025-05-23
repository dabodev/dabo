# -*- coding: utf-8 -*-
import copy
import datetime
import locale
import operator
import re
import sys
import time
import warnings
from decimal import Decimal
from decimal import InvalidOperation
from functools import reduce

import wx
import wx.grid
from wx._core import PyAssertionError

from .. import application
from .. import biz
from .. import color_tools
from .. import db
from .. import events
from .. import exceptions
from .. import settings
from .. import ui
from ..base_object import dObject
from ..debugging import loggit
from ..lib import dates
from ..lib.utils import caseInsensitiveSortKey
from ..lib.utils import noneSortKey
from ..lib.utils import ustr
from ..localization import _
from ..localization import n_
from . import dButton
from . import dCheckBox
from . import dControlMixin
from . import dDropdownList
from . import dFont
from . import dForm
from . import dGridSizer
from . import dKeys
from . import dMenu
from . import dPemMixin
from . import dRadioList
from . import dTextBox
from . import dTimer
from . import dUICursors
from . import makeDynamicProperty

dabo_module = settings.get_dabo_package()

# Make this locale-independent
# JK: We can't set this up on module load because locale
# is set not until dApp is completely setup.
decimalPoint = None


class dGridDataTable(wx.grid.GridTableBase):
    def __init__(self, parent):
        super().__init__()
        self._clearCache()
        self.grid = parent
        self._initTable()

    def _clearCache(self):
        self.__cachedVals = {}
        self.__cachedAttrs = {}

    def _initTable(self):
        self.colDefs = []
        self._oldRowCount = 0
        self.grid.setTableAttributes(self)

    def GetAttr(self, row, col, kind=0):
        col = self._convertWxColNumToDaboColNum(col)
        if col is None:
            # Empty grid so far, no biggie:
            return self.grid._defaultGridColAttr.Clone()

        cv = self.__cachedAttrs.get((row, col))
        if cv:
            diff = time.time() - cv[1]
            if diff < 10:  ## if it's been less than this # of seconds.
                return cv[0].Clone()

        dcol = self.grid.Columns[col]
        dcol._updateCellDynamicProps(row)

        if dcol._gridCellAttrs:
            attr = dcol._gridCellAttrs.get(row, dcol._gridColAttr)
        else:
            attr = dcol._gridColAttr

        ## Now, override with a custom renderer for this row/col if applicable.
        ## Note that only the renderer is handled here, as we are segfaulting when
        ## handling the editor here.
        r = dcol.getRendererClassForRow(row)
        if r is not None:
            rnd = r()
            attr.SetRenderer(rnd)
            if r in (dcol.floatRendererClass, dcol.decimalRendererClass):
                rnd.SetPrecision(dcol.Precision)
        do_incref = True
        # Now check for alternate row coloration
        if self.alternateRowColoring:
            do_incref = False
            attr = attr.Clone()
            attr.SetBackgroundColour((self.rowColorEven, self.rowColorOdd)[row % 2])

        # Prevents overwriting when a long cell has None in the one next to it.
        attr.SetOverflow(False)

        if do_incref:
            attr.IncRef()

        return attr

    def GetRowLabelValue(self, row):
        try:
            return self.grid.RowLabels[row]
        except IndexError:
            return ""

    def GetColLabelValue(self, col):
        return ""

    def setColumns(self, colDefs):
        """Create columns based on passed list of column definitions."""
        if colDefs == self.colDefs:
            # Already done, no need to take the time.
            return

        for idx, col in enumerate(colDefs):
            nm = col.DataField
            while not nm:
                nm = ustr(idx)
                idx += 1
                if nm in colDefs:
                    nm = ""
            colName = "Column_%s" % nm
            pos = col._getUserSetting("Order")
            if pos is not None:
                col.Order = pos

            # If the data types are actual types and not strings, convert
            # them to common strings.
            if isinstance(col.DataType, type):
                typeDict = {
                    str: "string",
                    str: "unicode",
                    bool: "bool",
                    int: "integer",
                    float: "float",
                    int: "long",
                    datetime.date: "date",
                    datetime.datetime: "datetime",
                    datetime.time: "time",
                    Decimal: "decimal",
                }
                try:
                    col.DataType = typeDict[col.DataType]
                except KeyError:
                    # Not one of the standard types. Extract it from
                    # the string version of the type
                    try:
                        col.DataType = ustr(col.DataType).split("'")[1].lower()
                    except IndexError:
                        # Something's odd. Print an error message and move on.
                        dabo_module.error(
                            "Unknown data type found in setColumns(): %s" % col.DataType
                        )
                        col.DataType = ustr(col.DataType)

        # Make sure that all cols have an Order set
        for num in range(len(colDefs)):
            col = colDefs[num]
            if col.Order < 0:
                col.Order = num
        colDefs.sort(key=lambda col: col.Order)
        self.colDefs = copy.copy(colDefs)

    def orderSort(self, col1, col2):
        return (col1 > col2) - (col1 < col2)

    def convertType(self, typ):
        """
        Convert common types, names and abbreviations for
        data types into the constants needed by the wx.grid.
        """
        # Default
        ret = wx.grid.GRID_VALUE_STRING
        if type(typ) == str:
            lowtyp = typ.lower()
        else:
            lowtyp = typ
            if typ is Decimal:
                lowtyp = "decimal"
        if lowtyp in (bool, "bool", "boolean", "logical", "l"):
            ret = wx.grid.GRID_VALUE_BOOL
        if lowtyp in (int, int, "int", "integer", "bigint", "i", "long"):
            ret = wx.grid.GRID_VALUE_NUMBER
        elif lowtyp in (str, str, "char", "varchar", "text", "c", "s"):
            ret = wx.grid.GRID_VALUE_STRING
        elif lowtyp in (float, "float", "f", "decimal"):
            ret = wx.grid.GRID_VALUE_FLOAT
        elif lowtyp in (
            datetime.date,
            datetime.datetime,
            datetime.time,
            "date",
            "datetime",
            "time",
            "d",
            "t",
        ):
            ret = wx.grid.GRID_VALUE_DATETIME
        return ret

    def CanGetValueAs(self, row, col, typ):
        col = self._convertWxColNumToDaboColNum(col)
        if self.grid.useCustomGetValue:
            return self.grid.customCanGetValueAs(row, col, typ)
        else:
            dcol = self.grid.Columns[col]
            return typ == self.convertType(dcol.DataType)

    def CanSetValueAs(self, row, col, typ):
        col = self._convertWxColNumToDaboColNum(col)
        if self.grid.useCustomSetValue:
            return self.grid.customCanSetValueAs(row, col, typ)
        else:
            dcol = self.grid.Columns[col]
            return typ == self.convertType(dcol.DataType)

    def fillTable(self, force=False):
        """
        Fill the grid's data table to match the data set. Returns the number
        of rows in the table.
        """
        _oldRowCount = self._oldRowCount

        # Get the data from the grid.
        bizobj = self.grid.getBizobj()

        if bizobj:
            dataSet = bizobj
            _newRowCount = dataSet.RowCount
            self._bizobj = bizobj
        else:
            self._bizobj = None
            dataSet = self.grid.DataSet
            if dataSet is None:
                return 0
            _newRowCount = len(dataSet)
            if _oldRowCount is None:
                ## still haven't tracked down why, but bizobj grids needed _oldRowCount
                ## to be initialized to None, or extra rows would be added. Since we
                ## aren't a bizobj grid, we need to change that None to 0 here so that
                ## the rows can get appended below.
                _oldRowCount = 0

        if _oldRowCount == _newRowCount and not force:
            return _newRowCount

        self.grid._syncRowCount()
        # Column widths come from multiple places. In decreasing precedence:
        #    1) dApp user settings,
        #    2) col.Width (as set by the Width prop or by the fieldspecs)
        #    3) have the grid autosize

        for idx, col in enumerate(self.grid._columns):
            gridCol = idx

            # 1) Try to get the column width from the saved user settings:
            width = col._getUserSetting("Width")

            if width is None:
                # 2) Try to get the column width from the column definition:
                width = col.Width

            if width is None or (width < 0):
                # 3) Have the grid autosize:
                self.grid.autoSizeCol(gridCol)
            else:
                col.Width = width

        # Show the row labels, if any
        for idx, label in enumerate(self.grid.RowLabels):
            self.SetRowLabelValue(idx, label)

        self._oldRowCount = _newRowCount
        return _newRowCount

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

    def GetNumberCols(self, useNative=False):
        if useNative:
            return super(dGridDataTable, self).GetNumberCols()
        else:
            return self.grid.ColumnCount

    def IsEmptyCell(self, row, col):
        if row >= self.grid.RowCount:
            return True
        return False

    def GetValue(
        self,
        row,
        col,
        useCache=True,
        convertNoneToString=True,
        dynamicUpdate=True,
        _fromGridEditor=False,
    ):
        col = self._convertWxColNumToDaboColNum(col)
        if useCache and not _fromGridEditor:
            cv = self.__cachedVals.get((row, col))
            if cv:
                diff = time.time() - cv[1]
                if diff < 10:  ## if it's been less than this # of seconds.
                    return cv[0]

        if col is None:
            # No corresponding Dabo column for this column; must be not visible.
            return ""

        bizobj = self.grid.getBizobj()
        col_obj = self.grid.Columns[col]
        field = col_obj.DataField
        if dynamicUpdate:
            col_obj._updateDynamicProps()
            col_obj._updateCellDynamicProps(row)
        ret = ""
        if bizobj:
            if field and (row < bizobj.RowCount):
                try:
                    ret = bizobj.getFieldVal(field, row)
                except exceptions.FieldNotFoundException:
                    pass
                if not _fromGridEditor:
                    ret = self.getStringValue(ret)
        else:
            try:
                ret = self.grid.DataSet[row][field]
            except (TypeError, IndexError, KeyError):
                pass
        if ret is None and convertNoneToString:
            ret = self.grid.NoneDisplay
        if not _fromGridEditor:
            self.__cachedVals[(row, col)] = (ret, time.time())
        return ret

    def getStringValue(self, val):
        """Get the string value to display in the grid."""
        if isinstance(val, datetime.datetime):
            return dates.getStringFromDateTime(val)
        elif isinstance(val, datetime.date):
            return dates.getStringFromDate(val)
        return val

    def SetValue(self, row, col, value, _fromGridEditor=False):
        col = self._convertWxColNumToDaboColNum(col)
        self.grid._setCellValue(row, col, value)
        if not _fromGridEditor:
            # Update the cache
            self.__cachedVals[(row, col)] = (value, time.time())
        self.grid.afterCellEdit(row, col)

    def _convertWxColNumToDaboColNum(self, wxCol):
        return self.grid._convertWxColNumToDaboColNum(wxCol)


class GridListEditor(wx.grid.GridCellChoiceEditor):
    def __init__(self, *args, **kwargs):
        dabo_module.info("GridListEditor: Init ")
        dabo_module.info(ustr(args))
        dabo_module.info(ustr(kwargs))
        super().__init__(*args, **kwargs)

    def Create(self, parent, id, evtHandler, *args, **kwargs):
        dabo_module.info("GridListEditor: Create")
        dabo_module.info(ustr(args))
        dabo_module.info(ustr(kwargs))
        self.control = dDropdownList(parent=parent, id=id, ValueMode="String")
        self.SetControl(self.control)
        if evtHandler:
            self.control.PushEventHandler(evtHandler)

    def Clone(self):
        return self.__class__()

    def SetParameters(self, paramStr):
        dabo_module.info("GridListEditor: SetParameters: %s" % paramStr)
        self.control.Choices = eval(paramStr)

    def BeginEdit(self, row, col, grid):
        dabo_module.info("GridListEditor: BeginEdit (%d,%d)" % (row, col))
        self.value = grid.GetTable().GetValue(row, col)
        dabo_module.info("GridListEditor: Value=%s" % self.value)
        dabo_module.info("GridListEditor: Choices=%s" % self.control.Choices)
        try:
            self.control.Value = self.value
        except ValueError:
            dabo_module.info("GridListEditor: Value not in Choices")
        self.control.SetFocus()

    def EndEdit(self, row, col, grid):
        dabo_module.info("GridListEditor: EndEdit (%d,%d)" % (row, col))
        changed = False
        v = self.control.Value
        if v != self.value:
            changed = True
        if changed:
            grid.GetTable().SetValue(row, col, value)
        self.value = ""
        self.control.Value = self.value
        return changed

    def Reset(self):
        dabo_module.info("GridListEditor: Reset")
        self.control.Value = self.value

    def IsAcceptedKey(self, key):
        dabo_module.info("GridListEditor: check key: %d" % (key))
        return True


class dColumn(wx._core.Object, dPemMixin):
    """
    These aren't the actual columns that appear in the grid; rather,
    they provide a way to interact with the underlying grid table in a more
    straightforward manner.
    """

    _call_beforeInit, _call_afterInit, _call_initProperties = False, True, True

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._isConstructed = False
        self._dynamic = {}
        # Initialize the attributes for DataField and DataType
        self._dataField = ""
        self._dataType = ""
        self._expand = False
        # Default to 2 decimal places
        self._precision = 2
        # Do text columns wrap their long text?
        self._wordWrap = False
        # Is the column shown?
        self._visible = True
        # Are headers auto aligned?
        self._autoAlign = False
        # Holds the default renderer class for the column
        self._rendererClass = None
        # Custom editors/renderers
        self._customRenderers = {}
        self._customEditors = {}

        # Declare Internal Header Attributes
        self._headerVerticalAlignment = "Center"
        self._headerHorizontalAlignment = "Center"
        self._headerForeColor = None
        self._headerBackColor = None

        self._sortKey = None

        dataFieldSent = "DataField" in kwargs
        dataTypeSent = "DataType" in kwargs
        precisionSent = "Precision" in kwargs

        self._beforeInit()
        kwargs["Parent"] = parent
        self._parent = parent
        # dColumn maintains one attr object that the grid table will use for
        # setting properties such as ForeColor and Font on the entire column.
        att = self._gridColAttr = parent._defaultGridColAttr.Clone()
        att.SetFont(self._getDefaultFont()._nativeFont)

        self._gridCellAttrs = {}

        wx._core.Object.__init__(self)
        dPemMixin.__init__(
            self, properties=properties, attProperties=attProperties, *args, **kwargs
        )
        self._baseClass = dColumn
        if dataFieldSent and not dataTypeSent:
            implicitPrecision = not precisionSent
            self._setDataTypeFromDataField(implicitPrecision)

    def _beforeInit(self, pre=None):
        # Define the cell renderer and editor classes
        self.stringRendererClass = wx.grid.GridCellStringRenderer
        self.wrapStringRendererClass = wx.grid.GridCellAutoWrapStringRenderer
        self.boolRendererClass = wx.grid.GridCellBoolRenderer
        self.intRendererClass = wx.grid.GridCellNumberRenderer
        self.longRendererClass = wx.grid.GridCellNumberRenderer
        self.decimalRendererClass = wx.grid.GridCellFloatRenderer
        self.floatRendererClass = wx.grid.GridCellFloatRenderer
        self.listRendererClass = wx.grid.GridCellStringRenderer
        self.imageRendererClass = ui.ImageRenderer
        self.stringEditorClass = wx.grid.GridCellTextEditor
        self.wrapStringEditorClass = wx.grid.GridCellAutoWrapStringEditor
        self.boolEditorClass = wx.grid.GridCellBoolEditor
        self.intEditorClass = wx.grid.GridCellNumberEditor
        self.longEditorClass = wx.grid.GridCellNumberEditor
        self.decimalEditorClass = wx.grid.GridCellFloatEditor
        self.floatEditorClass = wx.grid.GridCellFloatEditor
        self.listEditorClass = wx.grid.GridCellChoiceEditor
        #        self.listEditorClass = GridListEditor

        self.defaultRenderers = {
            "str": self.stringRendererClass,
            "string": self.stringRendererClass,
            "date": self.stringRendererClass,
            "datetime": self.stringRendererClass,
            "bool": self.boolRendererClass,
            "int": self.intRendererClass,
            "long": self.longRendererClass,
            "decimal": self.decimalRendererClass,
            "float": self.floatRendererClass,
            "list": self.listRendererClass,
            str: self.stringRendererClass,
            datetime.date: self.stringRendererClass,
            datetime.datetime: self.stringRendererClass,
            bool: self.boolRendererClass,
            int: self.intRendererClass,
            int: self.longRendererClass,
            float: self.floatRendererClass,
            Decimal: self.decimalRendererClass,
            list: self.listRendererClass,
        }
        self.defaultEditors = {
            "str": self.stringEditorClass,
            "string": self.stringEditorClass,
            "date": self.stringEditorClass,
            "datetime": self.stringEditorClass,
            "bool": self.boolEditorClass,
            "int": self.intEditorClass,
            "integer": self.intEditorClass,
            "long": self.longEditorClass,
            "decimal": self.decimalEditorClass,
            "float": self.floatEditorClass,
            "list": self.listEditorClass,
            str: self.stringEditorClass,
            str: self.stringEditorClass,
            datetime.date: self.stringEditorClass,
            datetime.datetime: self.stringEditorClass,
            bool: self.boolEditorClass,
            int: self.intEditorClass,
            int: self.longEditorClass,
            float: self.floatEditorClass,
            Decimal: self.decimalEditorClass,
            list: self.listEditorClass,
        }

        # Default to string renderer
        self._rendererClass = self.stringRendererClass
        super()._beforeInit(None)

    def _afterInit(self):
        self._isConstructed = True
        super()._afterInit()
        ui.callAfter(self._restoreFontZoom)

    def GetParent(self):
        # For wx compatibility
        return self._parent

    def getDataTypeForColumn(self):
        try:
            return self.DataType
        except (exceptions.FieldNotFoundException, exceptions.NoRecordsException):
            return None

    def _setRenderer(self):
        self._setDataTypeFromDataField()
        custom = self.CustomRendererClass
        if custom:
            self._rendererClass = custom
        else:
            typ = self.getDataTypeForColumn()
            self._rendererClass = self.defaultRenderers.get(typ, self.stringRendererClass)

    @ui.deadCheck
    def _updateDynamicProps(self):
        for prop, func in list(self._dynamic.items()):
            if prop[:4] != "Cell":
                if isinstance(func, tuple):
                    args = func[1:]
                    func = func[0]
                else:
                    args = ()
                setattr(self, prop, func(*args))

    def _updateCellDynamicProps(self, row):
        kwargs = {"row": row}
        self._cellDynamicRow = row
        for prop, func in list(self._dynamic.items()):
            if prop[:4] == "Cell":
                if isinstance(func, tuple):
                    args = func[1:]
                    func = func[0]
                else:
                    args = ()
                setattr(self, prop, func(*args, **kwargs))
        del self._cellDynamicRow

    def _restoreFontZoom(self):
        if self.Form and self.Form.SaveRestorePosition:
            super()._restoreFontZoom()

    def _getDefaultFont(self):
        ret = dFont(Size=10, Bold=False, Italic=False, Underline=False)
        if sys.platform.startswith("win"):
            # The wx default is quite ugly
            try:
                ret.Face = "Arial"
                ret.Size = 9
            except exceptions.FontNotFoundException:
                # I had this happen to a customer running Win XP. No idea why Arial
                # would be missing. --pkm 2009-10-24
                pass
        return ret

    def _constructed(self):
        return self._isConstructed

    def release(self):
        """
        Usually don't need this, but it helps to keep this in
        line with other Dabo objects.
        """
        try:
            self.Parent.removeColumn(self)
        except ValueError:
            # Will happen when the column has already been removed
            pass

    def _setAbsoluteFontZoom(self, newZoom):
        origFontSize = self._origFontSize = getattr(self, "_origFontSize", self.FontSize)
        origHeaderFontSize = self._origHeaderFontSize = getattr(
            self, "_origHeaderFontSize", self.HeaderFontSize
        )
        fontSize = origFontSize + newZoom
        headerFontSize = origHeaderFontSize + newZoom
        self._currFontZoom = newZoom
        if fontSize > 1:
            self.FontSize = fontSize
        if headerFontSize > 1:
            self.HeaderFontSize = headerFontSize

        if self.Form is not None:
            ui.callAfterInterval(200, self.Form.layout)

    def _setEditor(self, row):
        """
        Set the editor for the entire column based on the editor for this row.

        This is a workaround to a problem that is preventing us from setting the
        editor for a specific cell at the time the grid needs it.
        """
        edClass = self.getEditorClassForRow(row)
        attr = self._gridColAttr.Clone()
        if edClass:
            kwargs = {}
            if edClass in (wx.grid.GridCellChoiceEditor,):
                kwargs["choices"] = self.getListEditorChoicesForRow(row)
            elif edClass in (wx.grid.GridCellFloatEditor,):
                kwargs["precision"] = self.Precision
            editor = edClass(**kwargs)
            attr.SetEditor(editor)
        #            if edClass is self.floatEditorClass:
        #                editor.SetPrecision(self.Precision)
        self._gridColAttr = attr

    def getListEditorChoicesForRow(self, row):
        """Return the list of choices for the list editor for the given row."""
        return self.CustomListEditorChoices.get(row, self.ListEditorChoices)

    def getEditorClassForRow(self, row):
        """Return the cell editor class for the passed row."""
        return self.CustomEditors.get(row, self.EditorClass)

    def _getValueForRow(self, row):
        if self.Parent:
            return self.Parent.getColumnValueByRow(self, row)

    def getRendererClassForRow(self, row):
        """Return the cell renderer class for the passed row."""
        if self._getValueForRow(row) == self.Parent.NoneDisplay:
            # Null values in the data should be rendered as strings,
            # no matter what type the column is.
            return self.stringRendererClass
        return self._customRenderers.get(row, self._rendererClass)

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
            if not colObj.Visible:
                continue
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
            self.Parent.SetColLabelValue(self.ColumnIndex, "")

    def _refreshGrid(self):
        """Refresh the grid region, not the header region."""
        if self.Parent:
            gw = self.Parent.GetGridWindow()
            gw.Refresh()

    def _persist(self, prop):
        """Persist the current prop setting to the user settings table."""
        self._setUserSetting(prop, getattr(self, prop))

    def _setDataTypeFromDataField(self, implicitPrecision=True):
        """
        When a column has its DataField changed, we need to set the
        correct DataType based on the new value.
        """
        if self.Parent:
            currDT = self.DataType
            dt = self.Parent.typeFromDataField(self.DataField, self)
            if dt not in (None, type(None)) and (dt != currDT):
                self.DataType = dt
                if dt is Decimal and implicitPrecision:
                    self.Precision = self.Parent.precisionFromDataField(self.DataField)

    def _getUserSetting(self, prop):
        """Get the property value from the user settings table."""
        app = self.Application
        grid = self.Parent
        form = grid.Form
        colName = "column_%s" % self.DataField

        if app is not None and form is not None and not hasattr(grid, "isDesignerControl"):
            settingName = "%s.%s.%s.%s" % (form.Name, grid.Name, colName, prop)
            return app.getUserSetting(settingName)
        return None

    def _setUserSetting(self, prop, val):
        """Set the property value to the user settings table."""
        app = self.Application
        grid = self.Parent
        form = grid.Form
        colName = "column_%s" % self.DataField

        if app is not None and form is not None and not hasattr(grid, "isDesignerControl"):
            settingName = "%s.%s.%s.%s" % (form.Name, grid.Name, colName, prop)
            app.setUserSetting(settingName, val)

    def _updateEditor(self):
        """The Field, DataType, or CustomEditor has changed: set in the attr"""
        editorClass = self.EditorClass
        if editorClass is None:
            editor = None
        else:
            kwargs = {}
            if editorClass in (wx.grid.GridCellChoiceEditor,):
                kwargs["choices"] = self.ListEditorChoices
            # Fix for editor precision issue.
            elif editorClass in (wx.grid.GridCellFloatEditor,):
                kwargs["precision"] = self.Precision
            editor = editorClass(**kwargs)
        self._gridColAttr.SetEditor(editor)

    def _updateRenderer(self):
        """The Field, DataType, or CustomRenderer has changed: set in the attr"""
        self._setRenderer()
        rendClass = self.CustomRendererClass or self.RendererClass
        if rendClass is None:
            renderer = None
        else:
            renderer = rendClass()
        self._gridColAttr.SetRenderer(renderer)

    def _onFontPropsChanged(self, evt):
        # Sent by the dFont object when any props changed. Wx needs to be notified:
        self._gridColAttr.SetFont(self.Font._nativeFont)
        self._refreshGrid()

    def _onHeaderFontPropsChanged(self, evt):
        # Sent by the dFont object when any props changed. Wx needs to be notified:
        self._refreshHeader()

    def _setCellProp(self, wxPropName, *args, **kwargs):
        """Called from all of the Cell property setters."""
        ## dynamic prop uses cellDynamicRow; reg prop uses self.CurrentRow
        try:
            row = getattr(self, "_cellDynamicRow", self.Parent.CurrentRow)
        except RuntimeError:
            # @ui.deadCheck didn't seem to work...
            return
        cellAttr = obj = self._gridCellAttrs.get(row, self._gridColAttr.Clone())
        if "." in wxPropName:
            # For instance, Font.SetWeight
            wxPropName, subObject = wxPropName.split(".")
            obj = getattr(cellAttr, wxPropName)
            getattr(obj, subObject)(*args, **kwargs)
            setattr(cellAttr, wxPropName, obj)
        else:
            getattr(cellAttr, wxPropName)(*args, **kwargs)
        self._gridCellAttrs[row] = cellAttr

    def _setAutoHorizontalAlignment(self):
        dt = self.DataType
        if isinstance(dt, str):
            if dt in ("decimal", "float", "long", "integer"):
                self._AutoAlign = True
                self.HorizontalAlignment = "Right"

    ## Property definitions
    @property
    def _AutoAlign(self):
        return self._autoAlign

    @_AutoAlign.setter
    def _AutoAlign(self, val):
        self._autoAlign = val

    @property
    def BackColor(self):
        """Color for the background of each cell in the column."""
        return self._gridColAttr.GetBackgroundColour()

    @BackColor.setter
    def BackColor(self, val):
        if self._constructed():
            if isinstance(val, str):
                val = color_tools.colorTupleFromName(val)
            self._gridColAttr.SetBackgroundColour(val)
            self._refreshGrid()
        else:
            self._properties["BackColor"] = val

    @property
    def Caption(self):
        """Specifies the caption displayed in this column's header."""
        try:
            v = self._caption
        except AttributeError:
            v = self._caption = "Column"
        return v

    @Caption.setter
    def Caption(self, val):
        if self._constructed():
            self._caption = val
            self._refreshHeader()
        else:
            self._properties["Caption"] = val

    @property
    def CellBackColor(self):
        """Color for the background of the current cell in the column."""
        row = self.Parent.CurrentRow
        cellAttr = self._gridCellAttrs.get(row, False)
        if cellAttr:
            return cellAttr.GetBackgroundColour()
        return self.BackColor

    @CellBackColor.setter
    def CellBackColor(self, val):
        if self._constructed():
            if isinstance(val, str):
                val = color_tools.colorTupleFromName(val)
            self._setCellProp("SetBackgroundColour", val)
        else:
            self._properties["CellBackColor"] = val

    @property
    def CellFontBold(self):
        """Specifies whether the current cell's font is bold-faced."""
        row = self.Parent.CurrentRow
        cellAttr = self._gridCellAttrs.get(row, False)
        if cellAttr:
            return cellAttr.GetFont().GetWeight() == wx.FONTWEIGHT_BOLD
        return self.FontBold

    @CellFontBold.setter
    def CellFontBold(self, val):
        if self._constructed():
            if val:
                val = wx.FONTWEIGHT_BOLD
            else:
                val = wx.FONTWEIGHT_NORMAL
            self._setCellProp("Font.SetWeight", val)
        else:
            self._properties["CellFontBold"] = val

    @property
    def CellForeColor(self):
        """Color for the foreground (text) of the current cell in the column."""
        row = self.Parent.CurrentRow
        cellAttr = self._gridCellAttrs.get(row, False)
        if cellAttr:
            return cellAttr.GetTextColour()
        return self.ForeColor

    @CellForeColor.setter
    def CellForeColor(self, val):
        if self._constructed():
            if isinstance(val, str):
                val = color_tools.colorTupleFromName(val)
            self._setCellProp("SetTextColour", val)
        else:
            self._properties["CellForeColor"] = val

    @property
    def ColumnIndex(self):
        """Return our column index in the grid, or -1."""
        try:
            return self.Parent.Columns.index(self)
        except (ValueError, AttributeError):
            return -1

    @property
    def CustomEditorClass(self):
        """
        Custom Editor class for this column. Default: None.

        Set this to override the default editor class, which Dabo will
        select based on the data type of the field.
        """
        try:
            v = self._customEditorClass
        except AttributeError:
            v = self._customEditorClass = None
        return v

    @CustomEditorClass.setter
    def CustomEditorClass(self, val):
        if self._constructed():
            self._customEditorClass = val
            self._updateEditor()
        else:
            self._properties["CustomEditorClass"] = val

    @property
    def CustomEditors(self):
        """
        Dictionary of custom editors for this column. Default: {}.

        Set this to override the default editor class on a row-by-row basis. If there is no custom
        editor class for a given row in CustomEditors, the CustomEditor property setting will apply.
        """
        try:
            v = self._customEditors
        except AttributeError:
            v = self._customEditors = {}
        return v

    @CustomEditors.setter
    def CustomEditors(self, val):
        self._customEditors = val

    @property
    def CustomListEditorChoices(self):
        """
        Dictionary of custom list choices for this column. Default: {}.

        Set this to override the default list choices on a row-by-row basis. If there is no custom
        entry for a given row in CustomListEditorChoices, the ListEditorChoices property setting
        will apply.
        """
        try:
            v = self._customListEditorChoices
        except AttributeError:
            v = self._customListEditorChoices = {}
        return v

    @CustomListEditorChoices.setter
    def CustomListEditorChoices(self, val):
        self._customListEditorChoices = val

    @property
    def CustomRendererClass(self):
        """
        Custom Renderer class for this column. Default: None.

        Set this to override the default renderer class, which Dabo will select based
        on the data type of the field.
        """
        try:
            v = self._customRendererClass
        except AttributeError:
            v = self._customRendererClass = None
        return v

    @CustomRendererClass.setter
    def CustomRendererClass(self, val):
        if self._constructed():
            self._customRendererClass = val
            self._updateRenderer()
        else:
            self._properties["CustomRendererClass"] = val

    @property
    def CustomRenderers(self):
        """
        Dictionary of custom renderers for this column. Default: {}.

        Set this to override the default renderer class on a row-by-row basis.  If there is no
        custom renderer for a given row in CustomRenderers, the CustomRendererClass property setting
        will apply.
        """
        try:
            v = self._customRenderers
        except AttributeError:
            v = self._customRenderers = {}
        return v

    @CustomRenderers.setter
    def CustomRenderers(self, val):
        self._customRenderers = val

    @property
    def DataField(self):
        """Field key in the data set to which this column is bound.     (str)"""
        try:
            v = self._dataField
        except AttributeError:
            v = self._dataField = ""
        return v

    @DataField.setter
    def DataField(self, val):
        if self._constructed():
            if self._dataField:
                # Use a callAfter, since the parent may not be finished instantiating yet.
                ui.callAfter(self._setDataTypeFromDataField)
            self._dataField = val
            if not self.Name or self.Name == "?":
                self._name = _("col_%s") % val
            self._updateRenderer()
            self._updateEditor()
        else:
            self._properties["DataField"] = val

    @property
    def DataType(self):
        """Description of the data type for this column     (str)"""
        try:
            v = self._dataType
        except AttributeError:
            v = self._dataType = "str"
        return v

    @DataType.setter
    def DataType(self, val):
        if self._constructed():
            if isinstance(val, str):
                if val.lower().strip() in ("str", "string", "char", "varchar", ""):
                    val = "str"
            if self._dataType == val:
                return
            self._dataType = val
            if "Automatic" in self.HorizontalAlignment:
                self._setAutoHorizontalAlignment()
            self._updateRenderer()
            self._updateEditor()
        else:
            self._properties["DataType"] = val

    @property
    def Editable(self):
        """
        If True, and if the grid is set as Editable, the cell values in this column are editable by
        the user. If False, the cells in this column cannot be edited no matter what the grid
        setting is. When editable, incremental searching will not be enabled, regardless of the
        Searchable property setting.  (bool)
        """
        return not self._gridColAttr.IsReadOnly()

    @Editable.setter
    def Editable(self, val):
        if self._constructed():
            self._gridColAttr.SetReadOnly(not val)
            if self.Parent:
                self.Parent.refresh()
        else:
            self._properties["Editable"] = val

    @property
    def EditorClass(self):
        """
        Returns the editor class used for cells in the column. This will be self.CustomEditorClass
        if set, or the default editor for the datatype of the field.  (varies)
        """
        v = self.CustomEditorClass
        if v is None:
            v = self.defaultEditors.get(self.DataType)
        return v

    @property
    def Expand(self):
        return self._expand

    @Expand.setter
    def Expand(self, val):
        """Does this column expand/shrink as the grid width changes?  Default=False  (bool)"""
        if self._constructed():
            self._expand = val
        else:
            self._properties["Expand"] = val

    @property
    def Font(self):
        if hasattr(self, "_font"):
            v = self._font
        else:
            v = self.Font = dFont(_nativeFont=self._gridColAttr.GetFont())
        return v

    @Font.setter
    def Font(self, val):
        """The font properties of the column's cells. (dFont)"""
        assert isinstance(val, dFont)
        if self._constructed():
            self._font = val
            self._gridColAttr.SetFont(val._nativeFont)
            val.bindEvent(events.FontPropertiesChanged, self._onFontPropsChanged)
            self._refreshGrid()
        else:
            self._properties["Font"] = val

    @property
    def FontBold(self):
        """Specifies if the cell font (for all cells in the column) is bold-faced. (bool)"""
        return self.Font.Bold

    @FontBold.setter
    def FontBold(self, val):
        if self._constructed():
            self.Font.Bold = val
        else:
            self._properties["FontBold"] = val

    @property
    def FontDescription(self):
        """Human-readable description of the column's cell font settings. (str)"""
        return self.Font.Description

    @property
    def FontFace(self):
        """Specifies the font face for the column cells. (str)"""
        return self.Font.Face

    @FontFace.setter
    def FontFace(self, val):
        if self._constructed():
            self.Font.Face = val
        else:
            self._properties["FontFace"] = val

    @property
    def FontInfo(self):
        """Specifies the platform-native font info string for the column cells. Read-only. (str)"""
        return self.Font._nativeFont.GetNativeFontInfoDesc()

    @property
    def FontItalic(self):
        """Specifies whether the column's cell font is italicized. (bool)"""
        return self.Font.Italic

    @FontItalic.setter
    def FontItalic(self, val):
        if self._constructed():
            self.Font.Italic = val
        else:
            self._properties["FontItalic"] = val

    @property
    def FontSize(self):
        """Specifies the point size of the column's cell font. (int)"""
        return self.Font.Size

    @FontSize.setter
    def FontSize(self, val):
        if self._constructed():
            self.Font.Size = val
        else:
            self._properties["FontSize"] = val

    @property
    def FontUnderline(self):
        """Specifies whether cell text is underlined. (bool)"""
        return self.Font.Underline

    @FontUnderline.setter
    def FontUnderline(self, val):
        if self._constructed():
            self.Font.Underline = val
        else:
            self._properties["FontUnderline"] = val

    @property
    def ForeColor(self):
        """Color for the foreground (text) of each cell in the column."""
        try:
            return self._gridColAttr.GetTextColour()
        except wx.PyAssertionError:
            # Getting the color failed on Mac and win: "no default attr"
            default = color_tools.colorTupleFromName("black")
            self._gridColAttr.SetTextColour(default)
            return default

    @ForeColor.setter
    def ForeColor(self, val):
        if self._constructed():
            if isinstance(val, str):
                val = color_tools.colorTupleFromName(val)
            self._gridColAttr.SetTextColour(val)
            self._refreshGrid()
        else:
            self._properties["ForeColor"] = val

    @property
    def HeaderBackColor(self):
        """Optional color for the background of the column header  (str)"""
        try:
            v = self._headerBackColor
        except AttributeError:
            v = self._headerBackColor = None
        return v

    @HeaderBackColor.setter
    def HeaderBackColor(self, val):
        if self._constructed():
            if isinstance(val, str):
                val = color_tools.colorTupleFromName(val)
            self._headerBackColor = val
            self._refreshHeader()
        else:
            self._properties["HeaderBackColor"] = val

    @property
    def HeaderFont(self):
        """The font properties of the column's header. (dFont)"""
        if hasattr(self, "_headerFont"):
            v = self._headerFont
        else:
            v = self.HeaderFont = self._getDefaultFont()
            v.Bold = True
        return v

    @HeaderFont.setter
    def HeaderFont(self, val):
        assert isinstance(val, dFont)
        if self._constructed():
            self._headerFont = val
            val.bindEvent(events.FontPropertiesChanged, self._onHeaderFontPropsChanged)
        else:
            self._properties["HeaderFont"] = val

    @property
    def HeaderFontBold(self):
        """Specifies if the header font is bold-faced. (bool)"""
        return self.HeaderFont.Bold

    @HeaderFontBold.setter
    def HeaderFontBold(self, val):
        if self._constructed():
            self.HeaderFont.Bold = val
        else:
            self._properties["HeaderFontBold"] = val

    @property
    def HeaderFontDescription(self):
        """Human-readable description of the current header font settings. (str)"""
        return self.HeaderFont.Description

    @property
    def HeaderFontFace(self):
        """Specifies the font face for the column header. (str)"""
        return self.HeaderFont.Face

    @HeaderFontFace.setter
    def HeaderFontFace(self, val):
        if self._constructed():
            self.HeaderFont.Face = val
        else:
            self._properties["HeaderFontFace"] = val

    @property
    def HeaderFontInfo(self):
        """Specifies the platform-native font info string for the column header. Read-only. (str)"""
        return self.HeaderFont._nativeFont.GetNativeFontInfoDesc()

    @property
    def HeaderFontItalic(self):
        """Specifies whether the header font is italicized. (bool)"""
        return self.HeaderFont.Italic

    @HeaderFontItalic.setter
    def HeaderFontItalic(self, val):
        if self._constructed():
            self.HeaderFont.Italic = val
        else:
            self._properties["HeaderFontItalic"] = val

    @property
    def HeaderFontSize(self):
        """Specifies the point size of the header font. (int)"""
        return self.HeaderFont.Size

    @HeaderFontSize.setter
    def HeaderFontSize(self, val):
        if self._constructed():
            self.HeaderFont.Size = val
        else:
            self._properties["HeaderFontSize"] = val

    @property
    def HeaderFontUnderline(self):
        """Specifies whether column header text is underlined. (bool)"""
        return self.HeaderFont.Underline

    @HeaderFontUnderline.setter
    def HeaderFontUnderline(self, val):
        if self._constructed():
            self.HeaderFont.Underline = val
        else:
            self._properties["HeaderFontUnderline"] = val

    @property
    def HeaderForeColor(self):
        """Optional color for the foreground (text) of the column header  (str)"""
        try:
            v = self._headerForeColor
        except AttributeError:
            v = self._headerForeColor = None
        return v

    @HeaderForeColor.setter
    def HeaderForeColor(self, val):
        if self._constructed():
            if isinstance(val, str):
                val = color_tools.colorTupleFromName(val)
            self._headerForeColor = val
            self._refreshHeader()
        else:
            self._properties["HeaderForeColor"] = val

    @property
    def HeaderHorizontalAlignment(self):
        """Specifies the horizontal alignment of the header caption. ('Left', 'Center', 'Right')"""
        try:
            val = self._headerHorizontalAlignment
        except AttributeError:
            val = self._headerHorizontalAlignment = None
        return val

    @HeaderHorizontalAlignment.setter
    def HeaderHorizontalAlignment(self, val):
        if self._constructed():
            v = self._expandPropStringValue(val, ("Left", "Right", "Center", None))
            self._headerHorizontalAlignment = v
            self._refreshHeader()
        else:
            self._properties["HeaderHorizontalAlignment"] = val

    @property
    def HeaderVerticalAlignment(self):
        """Specifies the vertical alignment of the header caption. ('Top', 'Center', 'Bottom')"""
        try:
            val = self._headerVerticalAlignment
        except AttributeError:
            val = self._headerVerticalAlignment = None
        return val

    @HeaderVerticalAlignment.setter
    def HeaderVerticalAlignment(self, val):
        if self._constructed():
            v = self._expandPropStringValue(val, ("Top", "Bottom", "Center", None))
            self._headerVerticalAlignment = v
            self._refreshHeader()
        else:
            self._properties["HeaderVerticalAlignment"] = val

    @property
    def HorizontalAlignment(self):
        """
        Horizontal alignment for all cells in this column. (str)
        Acceptable values are:
            'Automatic': The cell's contents will align right for numeric data,
                         left for text. (default)
            'Left'
            'Center'
            'Right'
        """
        try:
            auto = self._autoHorizontalAlignment
        except AttributeError:
            auto = self._autoHorizontalAlignment = True
        mapping = {
            wx.ALIGN_LEFT: "Left",
            wx.ALIGN_RIGHT: "Right",
            wx.ALIGN_CENTRE: "Center",
        }
        wxAlignment = self._gridColAttr.GetAlignment()[0]
        try:
            val = mapping[wxAlignment]
        except KeyError:
            val = "Left"
        if auto:
            val = "%s (Automatic)" % val
        return val

    @HorizontalAlignment.setter
    def HorizontalAlignment(self, val):
        if self._constructed():
            val = self._expandPropStringValue(val, ("Automatic", "Left", "Right", "Center"))
            if val == "Automatic" and not self._AutoAlign:
                self._autoHorizontalAlignment = True
                self._setAutoHorizontalAlignment()
                return
            if val != "Automatic" and not self._AutoAlign:
                self._autoHorizontalAlignment = False
            mapping = {
                "Left": wx.ALIGN_LEFT,
                "Right": wx.ALIGN_RIGHT,
                "Center": wx.ALIGN_CENTRE,
            }
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

    @property
    def ListEditorChoices(self):
        """
        Specifies the list of choices that will appear in the list. Only applies if the DataType is
        set as "list".  (list)
        """
        try:
            v = self._listEditorChoices
        except AttributeError:
            v = []
        return v

    @ListEditorChoices.setter
    def ListEditorChoices(self, val):
        if self._constructed():
            self._listEditorChoices = val
        else:
            self._properties["ListEditorChoices"] = val

    @property
    def Movable(self):
        """
        Specifies whether this column is movable by the user.

        Note also the dGrid.MovableColumns property - if that is set to False, columns will not be
        movable even if their Movable property is set to True.
        """
        return getattr(self, "_movable", True)

    @Movable.setter
    def Movable(self, val):
        self._movable = bool(val)

    @property
    def Order(self):
        """
        Order of this column. Columns in the grid are arranged according to their
        relative Order.  (int)
        """
        try:
            v = self._order
        except AttributeError:
            v = self._order = -1
        return v

    @Order.setter
    def Order(self, val):
        if self._constructed():
            self._order = val
        else:
            self._properties["Order"] = val

    @property
    def Precision(self):
        """Number of decimal places to display for float and decimal values  (int)"""
        return self._precision

    @Precision.setter
    def Precision(self, val):
        if self._constructed():
            self._precision = val
            if self.Parent:
                ui.callAfterInterval(50, self.Parent.refresh)
        else:
            self._properties["Precision"] = val

    @property
    def RendererClass(self):
        """
        Returns the renderer class used for cells in the column. This will be
        self.CustomRendererClass if set, or the default renderer class for the datatype of the
        field.  (varies)
        """
        return self._rendererClass

    @property
    def Resizable(self):
        """
        Specifies whether this column is resizable by the user.

        Note also the dGrid.ResizableColumns property - if that is set to False, columns will not be
        resizable even if their Resizable property is set to True.
        """
        return getattr(self, "_resizable", True)

    @Resizable.setter
    def Resizable(self, val):
        self._resizable = bool(val)

    @property
    def Searchable(self):
        """
        Specifies whether this column's incremental search is enabled. Default = True. The grid's
        Searchable property will override this setting.  (bool)
        """
        try:
            v = self._searchable
        except AttributeError:
            v = self._searchable = True
        return v

    @Searchable.setter
    def Searchable(self, val):
        if self._constructed():
            self._searchable = bool(val)
        else:
            self._properties["Searchable"] = val

    @property
    def Sortable(self):
        """
        Specifies whether this column can be sorted. Default: True. The grid's Sortable property
        will override this setting.  (bool)
        """
        try:
            v = self._sortable
        except AttributeError:
            v = self._sortable = True
        return v

    @Sortable.setter
    def Sortable(self, val):
        if self._constructed():
            self._sortable = bool(val)
        else:
            self._properties["Sortable"] = val

    @property
    def SortKey(self):
        """
        Defines how this column will be sorted should a sort be issued.

        Must be a callable that complies with the standard pythonic sort key function. See
        python.org's documentation for list.sort more information. (callable)
        """
        return self._sortKey

    @SortKey.setter
    def SortKey(self, obj):
        if callable(obj):
            self._sortKey = obj
        else:
            raise ValueError("SortKey must be callable.")

    @property
    def Value(self):
        """Returns the current value of the column from the underlying dataset or bizobj."""
        grid = self.Parent
        if grid is None:
            return None
        biz = grid.getBizobj()
        if self.DataField:
            if biz and (grid.CurrentRow < biz.RowCount):
                return biz.getFieldVal(self.DataField)
            if grid.DataSet:
                return grid.DataSet[grid.CurrentRow][self.DataField]
        return None

    @property
    def VerticalAlignment(self):
        """
        Vertical alignment for all cells in this column. Acceptable values are 'Top', 'Center', and
        'Bottom'.  (str)
        """
        mapping = {
            wx.ALIGN_TOP: "Top",
            wx.ALIGN_BOTTOM: "Bottom",
            wx.ALIGN_CENTRE: "Center",
        }
        wxAlignment = self._gridColAttr.GetAlignment()[1]
        try:
            val = mapping[wxAlignment]
        except KeyError:
            val = "Top"
        return val

    @VerticalAlignment.setter
    def VerticalAlignment(self, val):
        if self._constructed():
            val = self._expandPropStringValue(val, ("Top", "Bottom", "Center"))
            mapping = {
                "Top": wx.ALIGN_TOP,
                "Bottom": wx.ALIGN_BOTTOM,
                "Center": wx.ALIGN_CENTRE,
            }
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

    @property
    def Visible(self):
        """Controls whether the column is shown or not    (bool)"""
        return self._visible

    @Visible.setter
    def Visible(self, val):
        if self._constructed():
            self._visible = val
            self.Parent.showColumn(self, val)
        else:
            self._properties["Visible"] = val

    @property
    def Width(self):
        """Width of this column  (int)"""
        try:
            v = self._width
        except AttributeError:
            v = self._width = 150
        if self.Parent:
            idx = self.Parent._convertDaboColNumToWxColNum(self.ColumnIndex)
            if idx is not None:
                # Make sure the grid is in sync:
                try:
                    self.Parent.SetColSize(idx, v)
                except wx.PyAssertionError:
                    # The grid may still be in the process of being created, so pass.
                    pass
        return v

    @Width.setter
    def Width(self, val):
        if self._constructed():
            try:
                if val == self._width:
                    return
            except AttributeError:
                pass
            self._width = val
            grd = self.Parent
            if grd:
                grd._syncColumnCount()
                idx = grd._convertDaboColNumToWxColNum(self.ColumnIndex)
                if idx is not None:
                    # Change the size in the wx grid:
                    grd.SetColSize(idx, val)
        else:
            self._properties["Width"] = val

    @property
    def WordWrap(self):
        """When True, text longer than the column width will wrap to the next line  (bool)"""
        return self._wordWrap

    @WordWrap.setter
    def WordWrap(self, val):
        if self._constructed():
            if val != self._wordWrap:
                self._wordWrap = val
                if val:
                    for typ in (str, "str", "string"):
                        self.defaultRenderers[typ] = self.wrapStringRendererClass
                        self.defaultEditors[typ] = self.wrapStringEditorClass
                else:
                    for typ in (str, "str", "string"):
                        self.defaultRenderers[typ] = self.stringRendererClass
                        self.defaultEditors[typ] = self.stringEditorClass
                self._updateEditor()
                self._updateRenderer()
                self._refreshGrid()
        else:
            self._properties["WordWrap"] = val

    # Dynamic Property Declarations
    DynamicBackColor = makeDynamicProperty(BackColor)
    DynamicCaption = makeDynamicProperty(Caption)
    DynamicCellBackColor = makeDynamicProperty(CellBackColor)
    DynamicCellFontBold = makeDynamicProperty(CellFontBold)
    DynamicCellForeColor = makeDynamicProperty(CellForeColor)
    DynamicCustomEditorClass = makeDynamicProperty(CustomEditorClass)
    DynamicCustomEditors = makeDynamicProperty(CustomEditors)
    DynamicCustomListEditorChoices = makeDynamicProperty(CustomListEditorChoices)
    DynamicCustomRendererClass = makeDynamicProperty(CustomRendererClass)
    DynamicCustomRenderers = makeDynamicProperty(CustomRenderers)
    DynamicDataField = makeDynamicProperty(DataField)
    DynamicDataType = makeDynamicProperty(DataType)
    DynamicEditable = makeDynamicProperty(Editable)
    DynamicFont = makeDynamicProperty(Font)
    DynamicFontBold = makeDynamicProperty(FontBold)
    DynamicFontFace = makeDynamicProperty(FontFace)
    DynamicFontItalic = makeDynamicProperty(FontItalic)
    DynamicFontSize = makeDynamicProperty(FontSize)
    DynamicFontUnderline = makeDynamicProperty(FontUnderline)
    DynamicForeColor = makeDynamicProperty(ForeColor)
    DynamicHeaderBackColor = makeDynamicProperty(HeaderBackColor)
    DynamicHeaderFont = makeDynamicProperty(HeaderFont)
    DynamicHeaderFontBold = makeDynamicProperty(HeaderFontBold)
    DynamicHeaderFontFace = makeDynamicProperty(HeaderFontFace)
    DynamicHeaderFontItalic = makeDynamicProperty(HeaderFontItalic)
    DynamicHeaderFontSize = makeDynamicProperty(HeaderFontSize)
    DynamicHeaderFontUnderline = makeDynamicProperty(HeaderFontUnderline)
    DynamicHeaderForeColor = makeDynamicProperty(HeaderForeColor)
    DynamicHeaderHorizontalAlignment = makeDynamicProperty(HeaderHorizontalAlignment)
    DynamicHeaderVerticalAlignment = makeDynamicProperty(HeaderVerticalAlignment)
    DynamicHorizontalAlignment = makeDynamicProperty(HorizontalAlignment)
    DynamicListEditorChoices = makeDynamicProperty(ListEditorChoices)
    DynamicOrder = makeDynamicProperty(Order)
    DynamicSearchable = makeDynamicProperty(Searchable)
    DynamicSortable = makeDynamicProperty(Sortable)
    DynamicVerticalAlignment = makeDynamicProperty(VerticalAlignment)
    DynamicVisible = makeDynamicProperty(Visible)
    DynamicWidth = makeDynamicProperty(Width)


class dGrid(dControlMixin, wx.grid.Grid):
    """
    Creates a grid, with rows and columns to represent records and fields.

    Grids are powerful controls for allowing reading and writing of data. A
    grid can have any number of dColumns, which themselves have lots of properties
    to manipulate. The grid is virtual, meaning that large amounts of data can
    be accessed efficiently: only the data that needs to be shown on the current
    screen is copied and displayed.
    """

    USE_DATASOURCE_BEING_SET_HACK = False

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        # Update global decimalPoint attribute.
        global decimalPoint
        if decimalPoint is None:
            decimalPoint = locale.localeconv()["decimal_point"]
        # Get scrollbar size from system metrics.
        self._scrollBarSize = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)
        self._baseClass = dGrid
        preClass = wx.grid.Grid

        # Internal flag indicates update invoked by grid itself.
        self._inUpdate = False
        # Internal flag indicates header repaint invoked by the header itself.
        self._inHeaderPaint = False
        # Internal flag to determine if the prior sort order needs to be restored.
        self._sortRestored = False
        # Internal flag to determine if the resorting is the result of the DataSet property.
        self._settingDataSetFromSort = False
        # Internal flag to determine if refresh should be called after sorting.
        self._refreshAfterSort = True
        # Local count of rows in the data table
        self._tableRows = 0
        # List of visible columns
        self._daboVisibleColumns = []

        # When user selects new row, does the form have responsibility for making the change?
        self._mediateRowNumberThroughForm = True

        # Used to provide 'data' when the DataSet is empty.
        self.emptyRowsToAdd = 0

        # dColumn maintains its own cell attribute object, but this is the default:
        self._defaultGridColAttr = self._getDefaultGridColAttr()

        # Some applications (I'm thinking the UI Designer here) need to be able
        # to set Editing = True, but still disallow editing. This attribute does that.
        self._vetoAllEditing = False

        # Can the user move the columns around?
        self._movableColumns = True
        # Can the user re-size the columns or rows?
        self._resizableColumns = True
        self._resizableRows = True

        # Flag to indicate we are auto-sizing all columns
        self._inAutoSizeLoop = False
        # Flag to indicate we are in a range selection event
        self._inRangeSelect = False
        # Flag to indicate we are in a selection update event
        self._inUpdateSelection = False
        # Flag to avoid record pointer movement during DataSource setting. Only
        # applies if dGrid.USE_DATASOURCE_BEING_SET_HACK is True (default False)
        self._dataSourceBeingSet = False

        # Do we show row or column labels?
        self._showHeaders = True
        self._showRowLabels = False

        # Declare Internal Row Attributes
        self._rowLabels = []
        self._sameSizeRows = True

        # Declare Internal Column Attributes
        self._columnClass = dColumn
        self._columns = []

        # Declare Internal Search And Sort Attributes
        self._searchable = True
        self._searchDelay = None
        self._sortable = True

        # Declare Internal Header Attributes
        self._headerVerticalAlignment = "Center"
        self._headerHorizontalAlignment = "Center"
        self._headerForeColor = None
        self._headerBackColor = (232, 232, 232)
        self._verticalHeaders = False
        self._autoAdjustHeaderHeight = False
        self._headerMaxTextHeight = 0
        self._columnMetrics = [(0, 0)]
        # What color/size should the little sort indicator arrow be?
        self._sortIndicatorColor = "yellow"
        self._sortIndicatorSize = 8

        # Set NoneDisplay attributes
        if self.Application:
            self.__noneDisplayDefault = self.Application.NoneDisplay
        else:
            self.__noneDisplayDefault = _("< None >")
        self._noneDisplay = self.__noneDisplayDefault

        # These hold the values that affect row/col hiliting
        self._selectionForeColor = "black"
        self._selectionBackColor = "yellow"
        self._selectionMode = "Cell"
        self._modeSet = False
        self._multipleSelection = True
        # Track the last row and col selected
        self._lastRow = self._lastCol = None
        self._alternateRowColoring = False
        self._rowColorEven = "white"
        self._rowColorOdd = (212, 255, 212)  # very light green

        dControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

        # Reduces grid flickering on Windows platform.
        self._enableDoubleBuffering()
        # Need to sync the size reported by wx to the size reported by Dabo:
        self.RowHeight = self.RowHeight
        self.ShowRowLabels = self.ShowRowLabels

        # Set reasonable minimum size, as the default of (-1,-1) results in something
        # in wx calculating the effective minsize based on how much space we need to
        # show all the rows:
        self.SetMinSize((100, 100))

    def _afterInit(self):
        # When doing an incremental search, do we stop
        # at the nearest matching value?
        self.searchNearest = True
        # Do we do case-sensitive incremental searches?
        self.searchCaseSensitive = False
        # How many characters of strings do we display?
        self.stringDisplayLen = 64

        self.currSearchStr = ""
        self.incSearchTimer = dTimer(self)
        self.incSearchTimer.bindEvent(events.Hit, self.onIncSearchTimer)

        # By default, row labels are not shown. They can be displayed
        # if desired by setting ShowRowLabels = True, and their size
        # can be adjusted by setting RowLabelWidth = <width>
        self.SetRowLabelSize(self.RowLabelWidth)
        self.EnableEditing(self.Editable and not self._vetoAllEditing)

        # These need to be set to True, and custom methods provided,
        # if a grid with variable types in a single column is used.
        self.useCustomGetValue = False
        self.useCustomSetValue = False

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

        super()._afterInit()

        # Set the header props/events
        self.initHeader()
        # Make sure that the columns are sized properly
        ui.callAfter(self._updateColumnWidths)

    @ui.deadCheck
    def _afterInitAll(self):
        super()._afterInitAll()
        for col in self.Columns:
            col._setRenderer()

    def _initEvents(self):
        ## pkm: Don't do the grid_cell mouse events, because we handle it manually and it
        ##        would result in doubling up the events.
        # self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.__onWxGridCellMouseLeftDoubleClick)
        # self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.__onWxGridCellMouseLeftClick)
        # self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.__onWxGridCellMouseRightClick)
        self.Bind(wx.grid.EVT_GRID_CMD_ROW_SIZE, self.__onWxGridRowSize)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.__onWxGridSelectCell)
        self.Bind(wx.grid.EVT_GRID_CMD_COL_SIZE, self.__onWxGridColSize)
        self.Bind(wx.grid.EVT_GRID_EDITOR_CREATED, self.__onWxGridEditorCreated)
        self.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN, self.__onWxGridEditorShown)
        self.Bind(wx.grid.EVT_GRID_EDITOR_HIDDEN, self.__onWxGridEditorHidden)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.__onWxGridCellChange)
        self.Bind(wx.grid.EVT_GRID_RANGE_SELECT, self.__onWxGridRangeSelect)
        self.Bind(wx.EVT_SCROLLWIN, self.__onWxScrollWin)

        # Testing bool cell renderer/editor single-click-toggle:
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.__onGridCellLeftClick_toggleCB)

        gridWindow = self.GetGridWindow()

        gridWindow.Bind(wx.EVT_MOTION, self.__onWxMouseMotion)
        gridWindow.Bind(wx.EVT_LEFT_DCLICK, self.__onWxMouseLeftDoubleClick)
        gridWindow.Bind(wx.EVT_LEFT_DOWN, self.__onWxMouseLeftDown)
        gridWindow.Bind(wx.EVT_LEFT_UP, self.__onWxMouseLeftUp)
        gridWindow.Bind(wx.EVT_RIGHT_DOWN, self.__onWxMouseRightDown)
        gridWindow.Bind(wx.EVT_RIGHT_UP, self.__onWxMouseRightUp)
        gridWindow.Bind(wx.EVT_CONTEXT_MENU, self.__onWxContextMenu)

        self.bindEvent(events.KeyDown, self._onKeyDown)
        self.bindEvent(events.KeyChar, self._onKeyChar)
        self.bindEvent(events.GridRowSize, self._onGridRowSize)
        self.bindEvent(events.GridCellSelected, self._onGridCellSelected)
        self.bindEvent(events.GridColSize, self._onGridColSize)
        self.bindEvent(events.GridCellEdited, self._onGridCellEdited)
        self.bindEvent(events.GridMouseLeftClick, self._onGridMouseLeftClick)

        ## wx.EVT_CONTEXT_MENU doesn't appear to be working for dGrid yet:
        #        self.bindEvent(events.GridContextMenu, self._onContextMenu)
        self.bindEvent(events.GridMouseRightClick, self._onGridMouseRightClick)
        self.bindEvent(events.Resize, self._onGridResize)

        self.bindEvent(events.Create, self._onCreate)
        self.bindEvent(events.Destroy, self._onDestroy)

        super()._initEvents()

    def initHeader(self):
        """Initialize behavior for the grid header region."""
        header = self._getWxHeader()
        self.defaultHdrCursor = header.GetCursor()
        self._headerNeedsRedraw = False
        self._lastHeaderMousePosition = None
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

        self.bindEvent(events.GridHeaderMouseLeftDown, self._onGridHeaderMouseLeftDown)
        self.bindEvent(events.GridHeaderMouseMove, self._onGridHeaderMouseMove)
        self.bindEvent(events.GridHeaderMouseLeftUp, self._onGridHeaderMouseLeftUp)
        self.bindEvent(events.GridHeaderMouseRightUp, self._onGridHeaderMouseRightUp)
        self.bindEvent(events.GridHeaderMouseRightClick, self._onGridHeaderMouseRightClick)

    def update(self):
        """
        Call this when your datasource or dataset has changed to get the grid showing
        the proper number of rows with current data.
        """
        # We never call the superclass update, because we don't need/want that behavior.
        last = getattr(self, "_lastCellSelectedTime", 0)
        cur = time.time()
        if cur - last < 0.5:
            return
        self._syncRowCount()
        self._syncCurrentRow()
        self.refresh()  ## to clear the cache and repaint the cells

    def _syncAll(self):
        self._syncRowCount()
        self._syncColumnCount()
        self._syncCurrentRow()

    def refresh(self):
        """Repaint the grid."""
        if getattr(self, "__inRefresh", False):
            return
        self.__inRefresh = True
        self._Table._clearCache()  ## Make sure the proper values are filled into the cells

        # Force invisible column dynamic properties to update (possible to make Visible again):
        invisible_cols = [c._updateDynamicProps() for c in self.Columns if not c.Visible]

        super().refresh()
        self.__inRefresh = False

    def _refreshHeader(self):
        self._getWxHeader().Refresh()

    def GetCellValue(self, row, col, useCache=True):
        try:
            ret = self._Table.GetValue(row, col, useCache=useCache)
        except AttributeError:
            ret = super().GetCellValue(row, col)
        return ret

    def GetValue(self, row, col, dynamicUpdate=True):
        try:
            ret = self._Table.GetValue(row, col, dynamicUpdate=dynamicUpdate)
        except (AttributeError, TypeError):
            ret = super().GetValue(row, col)
        return ret

    def SetValue(self, row, col, val):
        try:
            self._Table.SetValue(row, col, val)
        except Exception as e:
            super().SetCellValue(row, col, val)
            # Update the main data source
            self._setCellValue(row, col, val)

    def _setCellValue(self, row, col, val):
        try:
            column = self.Columns[col]
            fld = column.DataField
            biz = self.getBizobj()
            if isinstance(val, float) and (
                issubclass(column.DataType, Decimal) or column.DataType == "decimal"
            ):
                val = Decimal(ustr(val))
            if biz:
                biz.RowNumber = row
                biz.setFieldVal(fld, val)
            else:
                self.DataSet[row][fld] = val
        except Exception as e:
            dabo_module.error("Cannot update data set: %s" % e)

    # Wrapper methods to Dabo-ize these calls.
    def getValue(self, row=None, col=None):
        """
        Returns the value of the specified row and column.

        If no row/col is specified, the current row/col will be used.
        """
        if row is None:
            row = self.CurrentRow
        if col is None:
            col = self.CurrentColumn
        ret = self.GetValue(row, col, dynamicUpdate=False)
        if isinstance(ret, bytes):
            ret = ret.decode(self.Encoding)
        return ret

    def setValue(self, row, col, val):
        return self.SetValue(row, col, val)

    # These two methods need to be customized if a grid has columns
    # with more than one type of data in them.
    def customCanGetValueAs(self, row, col, typ):
        pass

    def customCanSetValueAs(self, row, col, typ):
        pass

    # Wrap the native wx methods
    def setEditorForCell(self, row, col, edt):
        ## dColumn maintains a dict of overriding editor mappings, but keep this
        ## function for convenience.
        dcol = self.Columns[col]
        dcol.CustomEditors[row] = edt
        # self.SetCellEditor(row, col, edt)

    def setRendererForCell(self, row, col, rnd):
        ## dColumn maintains a dict of overriding renderer mappings, but keep this
        ## function for convenience.
        dcol = self.Columns[col]
        dcol.CustomRenderers[row] = rnd
        # self.SetCellRenderer(row, col, rnd)

    def typeFromDataField(self, df, col=None):
        """
        When the DataField is set for a column, it needs to set the corresponding
        value of its DataType property. Will return the Python data type, or None if
        there is no bizobj, or no DataStructure info available in the bizobj.
        """
        biz = self.getBizobj()
        if biz is None:
            if col is not None:
                return col.getDataTypeForColumn()
            else:
                return None
        try:
            pyType = biz.getDataTypeForField(df)
        except ValueError as e:
            dabo_module.error(e)
            return None
        return pyType

    def precisionFromDataField(self, df):
        """
        Return the decimal precision for the passed data field, or the default
        precision if this isn't a decimal field or it isn't specified in the
        bizobj.
        """
        default = 2
        biz = self.getBizobj()
        if biz is not None:
            ret = biz.getPrecisionForField(df)
            if ret is not None:
                return ret
        return default

    def getTableClass(cls):
        """
        We don't expose the underlying table class to the ui namespace, as it's a
        wx-specific implementation detail, but for cases where you need to subclass
        the table, this classmethod will return the class reference.
        """
        return dGridDataTable

    getTableClass = classmethod(getTableClass)

    def setTableAttributes(self, tbl=None):
        """Set the attributes for table display"""
        if tbl is None:
            try:
                tbl = self._Table
            except TypeError:
                tbl = None
            if tbl is None:
                # Still not fully constructed
                ui.callAfter(self.setTableAttributes)
                return
        tbl.alternateRowColoring = self.AlternateRowColoring
        tbl.rowColorOdd = self.getWxColour(self.RowColorOdd)
        tbl.rowColorEven = self.getWxColour(self.RowColorEven)

    def afterCellEdit(self, row, col):
        """Called after a cell has been edited by the user."""
        pass

    def fillGrid(self, force=False):
        """Refresh the grid to match the data in the data set."""
        # Get the default row size from dApp's user settings
        rowSize = self._getUserSetting("RowSize")
        if rowSize:
            self.SetDefaultRowSize(rowSize)
        tbl = self._Table

        if self.emptyRowsToAdd and self.Columns:
            # Used for display purposes when no data is present.
            self._addEmptyRows()
        tbl.setColumns(self.Columns)
        self._tableRows = tbl.fillTable(force)
        if not self._sortRestored:
            ui.callAfter(self._restoreSort)
            self._sortRestored = True

        # This will make sure that the current selection mode is activated.
        # We can't do it until after the first time the grid is filled.
        if not self._modeSet:
            self._modeSet = True
            self.SelectionMode = self.SelectionMode

        # I've found that both refresh calls are needed sometimes, especially
        # on Linux when manually moving a column header with the mouse.
        ui.callAfterInterval(200, self.refresh)
        self.refresh()

    def _updateDaboVisibleColumns(self):
        try:
            self._daboVisibleColumns = [e[0] for e in enumerate(self._columns) if e[1].Visible]
        except wx._core.PyAssertionError as e:
            # Can happen when an editor is active and columns resize
            vis = []
            for pos, col in enumerate(self._columns):
                if col.Visible:
                    vis.append(pos)
            self._daboVisibleColumns = vis

    def _convertWxColNumToDaboColNum(self, wxCol):
        """
        For the Visible property to work, we need to convert the column number
        wx sends to the actual column index in grid.Columns.

        Returns None if there is no corresponding dabo column.
        """
        try:
            return self._daboVisibleColumns[wxCol]
        except IndexError:
            return None

    def _convertDaboColNumToWxColNum(self, daboCol):
        """
        For the Visible property to work, we need to convert the column number
        dabo uses in grid.Columns to the wx column.

        Returns None if there is no corresponding wx column.
        """
        try:
            return self._daboVisibleColumns.index(daboCol)
        except ValueError:
            return None

    def _restoreSort(self):
        if not self.Sortable:
            return
        self.sortedColumn = self._getUserSetting("sortedColumn")
        self.sortOrder = self._getUserSetting("sortOrder")

        if self.sortedColumn is not None:
            sortCol = None
            for idx, col in enumerate(self.Columns):
                if col.DataField == self.sortedColumn:
                    sortCol = idx
                    break
            if sortCol is not None and col.Sortable:
                if self.RowCount > 0:
                    self.processSort(sortCol, toggleSort=False)

    def _addEmptyRows(self):
        """
        Adds blank rows of data to the grid. Used mostly by
        the Designer to display a grid that actually looks like a grid.
        """
        # First, get the type and field name for each column, and
        # add an empty value to a dict.
        colDict = {}
        for col in self.Columns:
            val = " " * 10
            dt = col.DataType
            if dt == "bool":
                val = False
            elif dt in ("int", "long"):
                val = 0
            elif dt in ("float", "decimal"):
                val = 0.00
            colDict[col.DataField] = val
        # Now add as many rows as specified
        ds = []
        for cnt in range(self.emptyRowsToAdd):
            ds.append(colDict)

        self.emptyRowsToAdd = 0
        self.DataSet = ds

    def buildFromDataSet(
        self,
        ds,
        keyCaption=None,
        includeFields=None,
        colOrder=None,
        colWidths=None,
        colTypes=None,
        autoSizeCols=True,
    ):
        """
        Add columns with properties set based on the passed dataset.

        A dataset is defined as one of:

            + a sequence of dicts, containing fieldname/fieldvalue pairs.
            + a string, which maps to a bizobj on the form.

        The columns will be taken from the first record of the dataset, with each
        column header caption being set to the field name, unless the optional
        keyCaption parameter is passed. This parameter is a 1:1 dict containing
        the data set keys as its keys, and the desired caption as the
        corresponding value.

        If the includeFields parameter is a sequence, the only columns added will
        be the fieldnames included in the includeFields sequence. If the
        includeFields parameter is None, all fields will be added to the grid.

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

        if isinstance(ds, str) or isinstance(ds, biz.dBizobj):
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
                try:
                    structure = bizobj.getDataStructureFromDescription()
                except TypeError:
                    # Well, that call failed... seems that sqlite doesn't define a cursor
                    # description? I need to test this out. For now, fall back to the old
                    # code that gets the data structure by executing "select * from table
                    # where 1=0". The downside to this is that no derived fields will be
                    # included in the structure.
                    structure = bizobj.getDataStructure()
                firstRec = {}
                for field in structure:
                    firstRec[field[0]] = None
                    if field[0] not in colTypes:
                        colTypes[field[0]] = field[1]
        else:
            # not a bizobj datasource
            firstRec = ds[0]

        colKeys = [
            key for key in list(firstRec.keys()) if (includeFields is None or key in includeFields)
        ]

        # Add the columns
        for colKey in colKeys:
            # Use the keyCaption values, if possible
            try:
                cap = keyCaption[colKey]
            except (KeyError, TypeError):
                cap = colKey
            col = self.addColumn(inBatch=True)
            col.Caption = cap
            col.DataField = colKey

            ## pkm: Get the datatype from what is specified in fieldspecs, not from
            ##        the actual type of the record.
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
            if colKey in colOrder:
                col.Order = colOrder[colKey]

            # See if any width was specified
            if colKey in colWidths:
                col.Width = colWidths[colKey]
            else:
                # Use a default width
                col.Width = -1

        # Populate the grid
        self.fillGrid(True)
        if autoSizeCols:
            self.autoSizeCol("all", True)
        return True

    def _onCreate(self, evt):
        self.restoreDataSet()

    def _onDestroy(self, evt):
        self.saveDataSet()

        for col in self.Columns:
            if col._gridColAttr is not None:
                col._gridColAttr.DecRef()
                col._gridColAttr = None  # that ref is now unsafe to use.

    def _onGridResize(self, evt):
        # Prevent unnecessary event processing.
        try:
            updCol = self._lastSize != evt._uiEvent.Size
        except AttributeError:
            updCol = True
        if updCol:
            self._lastSize = evt._uiEvent.Size
            ui.callAfter(self._updateColumnWidths)

    def _totalContentWidth(self, addScrollBar=False):
        ret = sum([col.Width for col in self.Columns])
        if self.ShowRowLabels:
            ret += self.RowLabelWidth
        if addScrollBar and self.isScrollBarVisible("v"):
            ret += self._scrollBarSize
        return ret

    def _totalContentHeight(self, addScrollBar=False):
        if self.SameSizeRows:
            ret = self.RowHeight * self.RowCount
        else:
            ret = sum([self.GetRowSize(r) for r in range(self.RowCount)])
        if self.ShowHeaders:
            ret += self.HeaderHeight
        if addScrollBar and self.isScrollBarVisible("h"):
            ret += self._scrollBarSize
        return ret

    def isScrollBarVisible(self, which):
        whichSide = {"h": wx.HORIZONTAL, "v": wx.VERTICAL}[which[0].lower()]
        sr = self.GetScrollRange(whichSide)
        if self.Application.Platform in ("Win", "GTK"):
            # For some reason, GetScrollRange() returns either 1 or 101 when the scrollbar
            # is not visible under Windows or GTK. Under OS X, it returns 0 as expected.
            return sr not in (1, 101)
        return bool(sr)

    @ui.deadCheck
    def _updateColumnWidths(self):
        """
        See if there are any dynamically-sized columns, and resize them
        accordingly.
        """
        try:
            if self._inColWidthUpdate:
                return
        except AttributeError:
            pass
        self._inColWidthUpdate = False
        if [col for col in self.Columns if col.Expand]:
            ui.callAfterInterval(10, self._delayedUpdateColumnWidths)

    def _delayedUpdateColumnWidths(self, redo=False):
        def _setFlag():
            self._inColWidthUpdate = True
            self.BeginBatch()

        def _clearFlag():
            self._inColWidthUpdate = False
            self.EndBatch()

        if self._inColWidthUpdate:
            return
        _setFlag()
        dynCols = [col for col in self.Columns if col.Expand]
        dynColCnt = len(dynCols)
        colWd = self._totalContentWidth(addScrollBar=True)
        rowHt = self._totalContentHeight()
        grdWd = self.Width
        # Subtract extra pixels to avoid triggering the scroll bar. Again, this
        # will probably be OS-dependent
        diff = grdWd - colWd - 10
        if redo and not diff:
            diff = -10
        if not diff:
            ui.callAfterInterval(5, _clearFlag)
            return
        if not redo and (diff == self._scrollBarSize):
            # This can cause infinite loops as we adjust constantly
            diff -= 1
        adj = diff / dynColCnt
        mod = diff % dynColCnt
        for col in dynCols:
            if mod:
                newWidth = col.Width + (adj + 1)
                mod -= 1
            else:
                newWidth = col.Width + adj
            # Don't allow the Expand columns to shrink below 24px wide.
            col.Width = max(24, newWidth)
        # Check to see if we need a further adjustment
        adjWd = self._totalContentWidth()
        if self.isScrollBarVisible("h") and (adjWd < grdWd):
            _clearFlag()
            self._delayedUpdateColumnWidths(redo=True)
        else:
            ui.callAfter(_clearFlag)

    def autoSizeCol(self, colNum, persist=False):
        """
        Set the column to the minimum width necessary to display its data.

        Set colNum='all' to auto-size all columns. Set persist=True to persist the
        new width to the user settings table.
        """
        if isinstance(colNum, str) and colNum.lower() == "all":
            self.BeginBatch()
            self._inAutoSizeLoop = True
            for ii in range(len(self.Columns)):
                self.autoSizeCol(ii, persist=persist)
            self._updateColumnWidths()
            self.EndBatch()
            self._inAutoSizeLoop = False
            return
        maxWidth = 250  ## limit the width of the column to something reasonable
        if not self._inAutoSizeLoop:
            # lock the screen
            self.lockDisplay()

        ## This function will get used in both if/elif below:
        def _setColSize(idx):
            sortIconSize = self.SortIndicatorSize
            sortIconBuffer = sortIconSize / 2
            ## breathing room around header caption:
            capBuffer = 5
            ## add additional room to account for possible sort indicator:
            capBuffer += (2 * sortIconSize) + (2 * sortIconBuffer)
            colObj = self.Columns[idx]
            if not colObj.Visible:
                ## wx knows nothing about Dabo's invisible columns
                return
            idx = self._convertDaboColNumToWxColNum(idx)
            autoWidth = self.GetColSize(idx)

            # Account for the width of the header caption:
            cw = ui.fontMetricFromFont(colObj.Caption, colObj.HeaderFont._nativeFont)[0] + int(
                capBuffer
            )
            w = max(autoWidth, cw)
            w = min(w, maxWidth)
            colObj.Width = w
            if persist:
                colObj._persist("Width")

        try:
            self.AutoSizeColumn(self._convertDaboColNumToWxColNum(colNum), setAsMin=False)
        except (TypeError, wx.PyAssertionError):
            pass
        if colNum > -1:
            _setColSize(colNum)

        if not self._inAutoSizeLoop:
            self.refresh()
            self.unlockDisplay()
            self._updateColumnWidths()

    def _paintHeader(self):
        """
        This method handles all of the display for the header, including writing
        the Captions along with any sort indicators.
        """
        if self._inHeaderPaint:
            return
        self._inHeaderPaint = True
        w = self._getWxHeader()
        w.SetBackgroundColour((255, 255, 255))
        updateBox = w.GetClientRect()
        try:
            # When called from OnPaint event, there should be PaintDC context.
            dc = wx.PaintDC(w)
        except wx.PyAssertionError:
            dc = wx.ClientDC(w)
        textAngle = {True: 90, False: 0}[self.VerticalHeaders]
        self._columnMetrics = []

        for idx, col in enumerate(self._columns):
            headerRect = col._getHeaderRect()
            intersect = wx.IntersectRect(updateBox, headerRect)
            if intersect is None:
                # column isn't visible
                continue
            headerRect[0] -= 1
            headerRect[2] += 1

            sortIndicator = False
            colObj = self.getColByX(intersect[0])
            if not colObj:
                # Grid is probably being created or destroyed, so just skip it
                continue
            dc.SetClippingRegion(*headerRect)

            headerRect = col._getHeaderRect()
            trect = list(headerRect)
            trect = wx.Rect(*trect)
            holdBrush = dc.GetBrush()
            holdPen = dc.GetPen()
            fcolor = colObj.HeaderForeColor
            if fcolor is None:
                fcolor = self.HeaderForeColor
                if fcolor is None:
                    fcolor = (0, 0, 0)
            fcolor = self.getWxColour(fcolor)
            bcolor = colObj.HeaderBackColor
            if bcolor is None:
                bcolor = self.HeaderBackColor
            bcolor = self.getWxColour(bcolor)
            dc.SetTextForeground(fcolor)
            wxNativeFont = colObj.HeaderFont._nativeFont
            # draw the col. header background:
            if bcolor is not None:
                dc.SetBrush(wx.Brush(bcolor, wx.BRUSHSTYLE_SOLID))
                dc.SetPen(wx.Pen(fcolor, width=0))
                dc.DrawRectangle(*headerRect)

            # draw the col. border:
            dc.SetBrush(wx.Brush(bcolor, wx.BRUSHSTYLE_TRANSPARENT))
            dc.SetPen(self.GetDefaultGridLinePen())
            dc.DrawRectangle(*headerRect)
            dc.SetPen(holdPen)
            dc.SetBrush(holdBrush)

            if colObj.DataField == self.sortedColumn:
                sortIndicator = True
                sortIconSize = self.SortIndicatorSize
                sortIconBuffer = int(sortIconSize / 2)
                # draw a triangle, pointed up or down, at the top left
                # of the column. TODO: Perhaps replace with prettier icons
                left = headerRect[0] + sortIconBuffer
                top = headerRect[1] + sortIconBuffer
                brushColor = self.getWxColour(self.SortIndicatorColor)
                dc.SetBrush(wx.Brush(brushColor, wx.BRUSHSTYLE_SOLID))
                if self.sortOrder == "DESC":
                    # Down arrow
                    dc.DrawPolygon(
                        [
                            (left, top),
                            (left + sortIconSize, top),
                            (left + sortIconBuffer, top + sortIconSize),
                        ]
                    )
                elif self.sortOrder == "ASC":
                    # Up arrow
                    dc.DrawPolygon(
                        [
                            (left + sortIconBuffer, top),
                            (left + sortIconSize, top + sortIconSize),
                            (left, top + sortIconSize),
                        ]
                    )
                else:
                    # Column is not sorted, so don't draw.
                    sortIndicator = False

            dc.SetFont(wxNativeFont)
            ah = colObj.HeaderHorizontalAlignment
            av = colObj.HeaderVerticalAlignment
            if ah is None:
                ah = self.HeaderHorizontalAlignment
            if av is None:
                av = self.HeaderVerticalAlignment
            if ah is None:
                ah = "Center"
            if av is None:
                av = "Bottom"
            wxah = {
                "Center": wx.ALIGN_CENTRE_HORIZONTAL,
                "Left": wx.ALIGN_LEFT,
                "Right": wx.ALIGN_RIGHT,
            }[ah]
            wxav = {
                "Center": wx.ALIGN_CENTRE_VERTICAL,
                "Top": wx.ALIGN_TOP,
                "Bottom": wx.ALIGN_BOTTOM,
            }[av]

            # Give some more space around the rect - some platforms use a 3d look
            # and anyway it looks better if left/right aligned text isn't right on
            # the line.
            horBuffer = 3
            vertBuffer = 2
            sortBuffer = horBuffer
            if sortIndicator:
                # If there's a sort indicator, we'll nudge the caption over
                sortBuffer += sortIconSize + sortIconBuffer
            trect = list(headerRect)
            trect[0] = trect[0] + sortBuffer
            trect[1] = trect[1] + vertBuffer
            if ah == "Center":
                trect[2] = trect[2] - (2 * sortBuffer)
            else:
                trect[2] = trect[2] - (horBuffer + sortBuffer)
            trect[3] = trect[3] - (2 * vertBuffer)
            trect = wx.Rect(*trect)

            twd, tht = ui.fontMetricFromDC(dc, colObj.Caption)
            if self.VerticalHeaders:
                # Note that when rotating 90 degrees, the width affect height,
                # and vice-versa
                twd, tht = tht, twd
            self._columnMetrics.append((twd, tht))

            # Figure out the x,y coordinates to start the text drawing.
            left, top, wd, ht = trect
            x = left
            if ah == "Center":
                x += (wd / 2) - (twd / 2)
            elif ah == "Right":
                x += wd - twd
            # Note that we need to adjust for text height when angle is 0.
            yadj = 0
            if textAngle == 0:
                yadj = tht
            y = top + ht - yadj
            if av == "Top":
                y = top + tht + 2 - yadj
            elif av == "Center":
                y = top + (ht / 2) + (tht / 2) - yadj

            # Note: leaving this here. It was the old way of drawing Captions for columns, but it
            # didn't work in the latest wxPython.
            # txt = self.drawText(
            #     "%s" % colObj.Caption,
            #     x,
            #     y,
            #     foreColor=fcolor,
            #     backColor=bcolor,
            #     angle=textAngle,
            #     dc=dc,
            #     useDefaults=True,
            # )
            dc.DrawText(colObj.Caption, round(x), round(y))
            dc.DestroyClippingRegion()
        if self.AutoAdjustHeaderHeight:
            self.fitHeaderHeight()
        self._inHeaderPaint = False

    def fitHeaderHeight(self):
        """
        Sizes the HeaderHeight to comfortably fit the captions. Primarily used for
        vertical captions or multi-line captions.
        """
        self._paintHeader()
        if self._columnMetrics:
            self._headerMaxTextHeight = max([cht for cwd, cht in self._columnMetrics])
        else:
            self._headerMaxTextHeight = 0
        diff = (self._headerMaxTextHeight + 20) - self.HeaderHeight
        if diff:
            self.HeaderHeight += diff
            ui.callAfter(self.refresh)

    def showColumn(self, col, visible):
        """
        If the column is not shown and visible=True, show it. Likewise
        but opposite if visible=False.
        """
        col = self._resolveColumn(col, logOnly=True)
        if col is None:
            # Invalid 'col' passed
            return
        col._visible = visible
        self._syncColumnCount()
        if getattr(self.Parent, "__inRefresh", False):
            self.refresh()

    def moveColumn(self, colNum, toNum):
        """Move the column to a new position."""
        oldCol = self.Columns[colNum]
        self.Columns.remove(oldCol)
        if toNum > colNum:
            self.Columns.insert(toNum - 1, oldCol)
        else:
            self.Columns.insert(toNum, oldCol)
        for col in self.Columns:
            col.Order = self.Columns.index(col) * 10
            col._persist("Order")
        self.fillGrid(True)

    def getColumnValueByRow(self, col, row):
        """Returns the value in the given column and row."""
        if isinstance(col, dColumn):
            colnum = self.Columns.index(col)
        else:
            colnum = col
        return self.GetValue(row, colnum)

    def sizeToColumns(self, scrollBarFudge=True):
        """
        Set the width of the grid equal to the sum of the widths    of the columns.

        If scrollBarFudge is True, additional space will be added to account for
        the width of the vertical scrollbar.
        """
        fudge = 5
        if scrollBarFudge:
            fudge = 18
        self.Width = reduce(operator.add, [col.Width for col in self.Columns]) + fudge

    def sizeToRows(self, maxHeight=500, scrollBarFudge=True):
        """
        Set the height of the grid equal to the sum of the heights of the rows.

        This is intended to be used only when the number of rows is expected to be
        low. Set maxHeight to whatever you want the maximum height to be.
        """
        fudge = 5
        if scrollBarFudge:
            fudge = 18
        self.Height = min(self.RowHeight * self.RowCount, maxHeight) + fudge

    def onIncSearchTimer(self, evt):
        """
        Occurs when the incremental search timer reaches its interval.
        It is time to run the search, if there is any search in the buffer.
        """
        if self.currSearchStr not in ("", "\n", "\r", "\r\n"):
            self.runIncSearch()
        else:
            self.incSearchTimer.stop()

    ##----------------------------------------------------------##
    ##                 begin: user hook methods                    ##
    ##----------------------------------------------------------##

    def fillContextMenu(self, menu):
        """
        User hook called just before showing the context menu.

        User code can append menu items, or replace/remove the menu entirely.
        Return a dMenu or None from this hook. Default: no context menu.
        """
        return menu

    def fillHeaderContextMenu(self, menu):
        """
        User hook called just before showing the context menu for the header.

        User code can append menu items, or replace/remove the menu entirely.
        Return a dMenu or None from this hook. The default menu includes an
        option to autosize the column.
        """
        return menu

    ##----------------------------------------------------------##
    ##                  end: user hook methods                    ##
    ##----------------------------------------------------------##

    def sort(self):
        """Hook method used in subclasses for custom sorting."""
        pass

    def processSort(self, gridCol=None, toggleSort=True):
        """
        Sort the grid column.

        Toggle between ascending and descending. If the grid column index isn't
        passed, the currently active grid column will be sorted.
        """
        if gridCol is None:
            gridCol = self.CurrentColumn

        colObj = self._resolveColumn(gridCol)
        canSort = self.Sortable and colObj.Sortable
        columnToSort = colObj.DataField
        sortCol = self.Columns.index(colObj)
        dataType = self.Columns[sortCol].DataType

        if not canSort:
            # Some columns, especially those with mixed values,
            # should not be sorted.
            return

        sortOrder = "ASC"
        if columnToSort == self.sortedColumn:
            sortOrder = self.sortOrder
            if toggleSort:
                if sortOrder == "ASC":
                    sortOrder = "DESC"
                elif sortOrder == "DESC":
                    columnToSort = None
                    sortOrder = "ASC"
                else:
                    sortOrder = "ASC"
        self.sortOrder = sortOrder
        self.sortedColumn = columnToSort

        eventData = {"column": colObj, "sortOrder": sortOrder}
        self.raiseEvent(events.GridBeforeSort, eventObject=self, eventData=eventData)

        biz = self.getBizobj()
        if columnToSort is not None:
            if self.customSort:
                # Grids tied to bizobj cursors may want to use their own sorting.
                self.sort()
            elif biz:
                # Use the default sort() in the bizobj:
                try:
                    biz.sort(columnToSort, sortOrder, self.caseSensitiveSorting)
                except exceptions.NoRecordsException:
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
                # Ensure that we actually have data to sort
                if not sortList:
                    return
                # At this point we have a list consisting of lists. Each of these member
                # lists contain the sort value in the zeroth element, and the row as
                # the first element.
                # First, see if we are comparing strings
                # if dataType is None:
                f = sortList[0][0]
                if f is None:
                    # We are just poking around, trying to glean the datatype, which is prone
                    # to error. The record we just checked is None, so try the last record and
                    # then give up.
                    f = sortList[-1][0]

                sortingStrings = isinstance(f, str)

                if colObj.SortKey:
                    sortKey = colObj.SortKey
                elif sortingStrings and not caseSensitive:  # Begin guessing at sort keys.
                    sortKey = caseInsensitiveSortKey
                # elif dataType in ("date", "datetime", 'boolean'):
                elif isinstance(f, datetime.date) or isinstance(f, bool) or isinstance(f, bool):
                    # can't compare NoneType to these types:
                    sortKey = noneSortKey
                else:
                    sortKey = None

                try:
                    sortList.sort(key=sortKey, reverse=(sortOrder == "DESC"))
                except TypeError as exc:
                    s = (
                        "Unable to sort this column. Conflicting, or unknown, data types within "
                        "the column make it impossible to sort implicitly. Please supply a sort "
                        "key method to the column, via the SortKey property, to delegate sort "
                        "behavior to."
                    )
                    if colObj.SortKey is not None:
                        # the preceding exception information will be useful for debugging
                        # their SortKey method
                        raise TypeError(s)
                    else:
                        # There is no user provided SortKey
                        raise TypeError(s) from exc
                # Extract the rows into a new list, then set the dataSet to the new list
                newRows = []
                newLabels = []
                for elem in sortList:
                    newRows.append(elem[1])
                    if self.RowLabels:
                        newLabels.append(elem[2])
                self.RowLabels = newLabels
                # Set this to avoid infinite loops
                self._settingDataSetFromSort = True
                self.DataSet = newRows
                self._settingDataSetFromSort = False

        if biz:
            ui.setAfter(self, "CurrentRow", biz.RowNumber)

        if self._refreshAfterSort:
            self.refresh()

        self._setUserSetting("sortedColumn", columnToSort)
        self._setUserSetting("sortOrder", sortOrder)
        self.raiseEvent(events.GridAfterSort, eventObject=self, eventData=eventData)
        ui.callAfterInterval(200, self.Form.update)  ## rownum in status bar

    def restoreDataSet(self):
        if self.SaveRestoreDataSet:
            ds = self.Application.getUserSetting("%s.DataSet" % self.getAbsoluteName())
            if ds is not None:
                self.DataSet = ds

    def saveDataSet(self):
        if self.SaveRestoreDataSet:
            self.Application.setUserSetting("%s.DataSet" % self.getAbsoluteName(), self.DataSet)

    def runIncSearch(self):
        """Run the incremental search."""
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
        srchVal = origSrchStr = self.currSearchStr
        self.currSearchStr = ""
        near = self.searchNearest
        caseSensitive = self.searchCaseSensitive
        # Copy the specified field vals and their row numbers to a list, and
        # add those lists to the sort list
        sortList = []
        for i in range(0, self.RowCount):
            if biz:
                val = biz.getFieldVal(fld, i, _forceNoCallback=True)
            else:
                val = self.DataSet[i][fld]
            sortList.append([val, i])

        # Determine if we are seeking string values
        compString = False
        for row in sortList:
            if row[0] is not None:
                compString = isinstance(row[0], str)
                break

        if not compString:
            # coerce srchVal to be the same type as the field type
            listval = sortList[0][0]
            if isinstance(listval, int):
                try:
                    srchVal = int(srchVal)
                except ValueError:
                    srchVal = int(0)
            elif isinstance(listval, int):
                try:
                    srchVal = int(srchVal)
                except ValueError:
                    srchVal = int(0)
            elif isinstance(listval, float):
                try:
                    srchVal = float(srchVal)
                except ValueError:
                    srchVal = float(0)
            elif isinstance(listval, (datetime.datetime, datetime.date, datetime.time)):
                # We need to convert the sort vals into strings
                sortList = [(ustr(vv), i) for vv, i in sortList]
                compString = True

        # Now iterate through the list to find the matching value. I know that
        # there are more efficient search algorithms, but for this purpose, we'll
        # just use brute force
        if compString:
            if caseSensitive:
                mtchs = [
                    vv for vv in sortList if isinstance(vv[0], str) and vv[0].startswith(srchVal)
                ]
            else:
                srchVal = srchVal.lower()
                mtchs = [
                    vv
                    for vv in sortList
                    if isinstance(vv[0], str) and vv[0].lower().startswith(srchVal)
                ]
        else:
            mtchs = [vv for vv in sortList if vv[0] == srchVal]
        if mtchs:
            # The row num is the second element. We want the first row in
            # the list, since it will still be sorted.
            newRow = mtchs[0][1]
        else:
            for fldval, row in sortList:
                if not compString or caseSensitive:
                    match = fldval == srchVal
                else:
                    # Case-insensitive string search.
                    match = isinstance(fldval, str) and fldval.lower() == srchVal
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
                    if compString and not caseSensitive and isinstance(fldval, str):
                        toofar = fldval.lower() > srchVal
                    else:
                        toofar = fldval > srchVal
                    if toofar:
                        break
        self.CurrentRow = newRow

        if self.Form is not None:
            # Add a '.' to the status bar to signify that the search is
            # done, and clear the search string for next time.
            currAutoUpdate = self.Form.AutoUpdateStatusText
            self.Form.AutoUpdateStatusText = False
            if currAutoUpdate:
                ui.setAfterInterval(1000, self.Form, "AutoUpdateStatusText", True)
            self.Form.updateStatusText("Search: '%s'." % origSrchStr)
        self.currSearchStr = ""

    def addToSearchStr(self, key):
        """
        Add a character to the current incremental search.

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
                searchDelay = 500

        self.incSearchTimer.stop()
        self.currSearchStr = "".join((self.currSearchStr, key))

        if self.Form is not None:
            self.Form.updateStatusText("Search: '%s'" % self.currSearchStr)
        self.incSearchTimer.start(searchDelay)

    def findReplace(self, action, findString, replaceString, downwardSearch, wholeWord, matchCase):
        """Called from the 'Find' dialog."""
        ret = False
        rowcol = currRow, currCol = (self.CurrentRow, self.CurrentColumn)
        if downwardSearch:
            op = operator.gt
        else:
            op = operator.lt
        if wholeWord:
            if matchCase:
                srch = r"\b%s\b" % findString
                findGen = (
                    (r, c)
                    for r in range(self.RowCount)
                    for c in range(self.ColumnCount)
                    if op((r, c), rowcol) and re.search(srch, ustr(self.GetValue(r, c)))
                )
            else:
                srch = r"\b%s\b" % findString.lower()
                findGen = (
                    (r, c)
                    for r in range(self.RowCount)
                    for c in range(self.ColumnCount)
                    if op((r, c), rowcol) and re.search(srch, ustr(self.GetValue(r, c)).lower())
                )
        else:
            if matchCase:
                findGen = (
                    (r, c)
                    for r in range(self.RowCount)
                    for c in range(self.ColumnCount)
                    if op((r, c), rowcol) and findString in ustr(self.GetValue(r, c))
                )
            else:
                findGen = (
                    (r, c)
                    for r in range(self.RowCount)
                    for c in range(self.ColumnCount)
                    if op((r, c), rowcol)
                    and findString.lower() in ustr(self.GetValue(r, c)).lower()
                )
        if action == "Find":
            try:
                while True:
                    newR, newC = next(findGen)
                    targetVal = self.GetValue(newR, newC)
                    targetString = ustr(targetVal)
                    if isinstance(targetVal, (str, datetime.datetime, datetime.date)):
                        # Values can be inexact matches
                        break
                    else:
                        # Needs to be an exact match
                        if findString == targetString:
                            break
                ret = True
                self._lastRow, self._lastCol = newR, newC
                self.CurrentRow, self.CurrentColumn = newR, newC
            except StopIteration:
                ret = False
        elif action == "Replace":
            val = self.GetValue(currRow, currCol)
            if isinstance(val, str):
                self.SetValue(currRow, currCol, val.replace(findString, replaceString))
                ret = True
            elif isinstance(val, bool):
                if replaceString.lower() in (
                    "true",
                    "t",
                    "false",
                    "f",
                    "1",
                    "0",
                    "yes",
                    "y",
                    "no",
                    "n",
                ):
                    newval = replaceString.lower() in ("true", "t", "1", "yes", "y")
                    self.SetValue(currRow, currCol, newval)
                    ret = True
                else:
                    dabo_module.error(_("Invalid boolean replacement value: %s") % replaceString)
                    ret = False
            else:
                # Try the numeric types
                typFunc = type(val)
                if typFunc(findString) == val:
                    # We can replace if replaceString can be the correct type
                    errors = (ValueError, InvalidOperation)
                    try:
                        newval = typFunc(replaceString)
                        self.SetValue(currRow, currCol, newval)
                        ret = True
                    except errors:
                        dabo_module.error(_("Invalid replacement value: %s") % replaceString)
                        ret = False
            if ret:
                self.ForceRefresh()
        return ret

    def getColNumByX(self, x):
        """Given the x-coordinate, return the column index in self.Columns."""
        col = self.XToCol(x + (self.GetViewStart()[0] * self.GetScrollPixelsPerUnit()[0]))
        if col == wx.NOT_FOUND:
            col = -1
        else:
            col = self._convertWxColNumToDaboColNum(col)
        return col

    def getRowNumByY(self, y):
        """Given the y-coordinate, return the row number."""
        row = self.YToRow(y + (self.GetViewStart()[1] * self.GetScrollPixelsPerUnit()[1]))
        if row == wx.NOT_FOUND:
            row = -1
        return row

    def getColByX(self, x):
        """Given the x-coordinate, return the column object."""
        colNum = self.getColNumByX(x)
        if (colNum < 0) or (colNum > self.ColumnCount - 1):
            return None
        else:
            return self.Columns[colNum]

    def getColByDataField(self, df):
        """Given a DataField value, return the corresponding column."""
        try:
            ret = [col for col in self.Columns if col.DataField == df][0]
        except IndexError:
            ret = None
        return ret

    def maxColOrder(self):
        """Returns the highest value of Order for all columns."""
        ret = -1
        if len(self.Columns) > 0:
            ret = max([cc.Order for cc in self.Columns])
        return ret

    def addColumns(self, *columns):
        """
        Adds a set of columns to the grid.

        Each column in the set should be a dColumn instance.
        """
        columns = self._resolveColumns(columns)
        for column in columns:
            self.addColumn(column, inBatch=True)
        self._syncColumnCount()
        self.fillGrid(True)

    def addColumn(self, col=None, inBatch=False, *args, **kwargs):
        """Adds a column to the grid.

        If no col (class or instance) is passed, a blank dColumn is added, which
        can be customized later. Any extra keyword arguments are passed to the
        constructor of the new dColumn.
        """
        if col is None:
            col = self.ColumnClass(self, *args, **kwargs)
        else:
            if not isinstance(col, dColumn):
                if issubclass(col, dColumn):
                    col = col(self, *args, **kwargs)
                else:
                    raise ValueError(_("col must be a dColumn subclass or instance"))
            else:
                col.setProperties(**kwargs)
            col.Parent = self

        if col.Order == -1:
            maxOrd = self.maxColOrder()
            if maxOrd < 0:
                newOrd = 0
            else:
                newOrd = maxOrd + 10
            col.Order = newOrd
        self.Columns.append(col)
        if not inBatch:
            self._syncColumnCount()
            self.fillGrid(force=True)
        try:
            ## Set the Width property last, otherwise it won't stick:
            if not col.Width:
                col.Width = 75
            else:
                ## If Width was specified in the dColumn subclass or in the constructor,
                ## it's been set as the property but because it wasn't part of the grid
                ## yet it hasn't yet taken effect: force it.
                col.Width = col.Width
        except (
            wx.wxAssertionError,
            wx._core.wxAssertionError,
        ):
            # If the underlying wx grid doesn't yet know about the column, such
            # as when adding columns with inBatch=True, this can throw an error
            if not inBatch:
                # For now, just log it
                dabo_module.info(_("Cannot set width of column %s") % col.Order)
        return col

    def _resolveColumns(self, columns):
        if len(columns) == 1 and isinstance(columns[0], (list, tuple, set)):
            columns = columns[0]
        return [self._resolveColumn(col) for col in columns]

    def _resolveColumn(self, colOrIdx, returnColumn=True, logOnly=False):
        """
        Accepts either a column object or a column index, and returns a column
        object. If you need the column's index instead, pass False to the
        'returnColumn' parameter.

        Used for cases where a method can accept either type of reference, but
        needs to work with the actual column.

        If anything other than a column reference or an integer is passed, a
        ValueError will be raised. If you prefer to simply log the error without
        raising an exception, pass True to the logOnly parameter (default=False).
        """
        if isinstance(colOrIdx, int):
            return self.Columns[colOrIdx] if returnColumn else colOrIdx
        elif isinstance(colOrIdx, dColumn):
            return colOrIdx if returnColumn else self.Columns.index(colOrIdx)
        else:
            typcoi = type(colOrIdx)
            msg = (
                _("Values must be a dColumn or an int; received '%(colOrIdx)s' (%(typcoi)s)")
                % locals()
            )
            if logOnly:
                dabo_module.error(msg)
                return None
            else:
                raise ValueError(msg)

    def removeColumns(self, *columns):
        """
        Removes a set of columns from the grid.

        The passed columns can be indexes or dColumn instances, or both.
        """
        columns = self._resolveColumns(columns)
        for col in columns:
            self.removeColumn(col, inBatch=True)
        self._syncColumnCount()
        self.fillGrid(True)

    def removeColumn(self, col=None, inBatch=False):
        """
        Removes a column from the grid.

        If no column is passed, the last column is removed. The col argument can
        be either a column index or a dColumn instance.
        """
        if col is None:
            colNum = self.ColumnCount - 1
        else:
            colNum = self._resolveColumn(col, returnColumn=False, logOnly=True)
        del self.Columns[colNum]
        if not inBatch:
            self._syncColumnCount()
            self.fillGrid(True)

    def cell(self, row, col):
        class GridCell(object):
            def __init__(self, parent, row, col):
                self.parent = parent
                self.row = row
                self.col = col

            @property
            def Value(self):
                return self.parent.GetValue(self.row, self.col)

            @Value.setter
            def Value(self, val):
                self.parent.SetValue(self.row, self.col, val)

        return GridCell(self, row, col)

    def copy(self):
        valSep = settings.copyValueSeparator
        strSep = settings.copyStringSeparator
        lnSep = settings.copyLineSeparator

        def valEscape(val):
            if isinstance(val, str):
                # Need to escape tabs and newlines
                escval = val.replace("\t", "\\t").replace("\n", "\\n")
                if strSep:
                    # Also escape the string separator
                    escval = escval.replace(strSep, "\\%s" % strSep)
                return "%s%s%s" % (strSep, escval, strSep)
            else:
                ret = str(val)
                if isinstance(val, (Decimal, float)):
                    # We need to convert decimal point accordingly to the locale.
                    ret = ret.replace(".", decimalPoint)
                return ret

        def valuesForRange(rowrange, colrange):
            allvals = []
            for row in rowrange:
                rowvals = []
                for col in colrange:
                    val = self.getValue(row, col)
                    rowvals.append(valEscape(val))
                allvals.append(valSep.join(rowvals))
            return lnSep.join(allvals)

        sel = self.Selection
        if not sel:
            return None
        selmode = self.SelectionMode
        copied = []
        txtToCopy = ""
        if selmode == "Cell":
            copySections = []
            for rangeTuple in sel:
                zrow, zcol = list(zip(*rangeTuple))
                rowrange = list(range(zrow[0], zrow[1] + 1))
                colrange = list(range(zcol[0], zcol[1] + 1))
                copySections.append(valuesForRange(rowrange, colrange))
            txtToCopy = lnSep.join(copySections)
        else:
            if selmode == "Row":
                rowrange = sel
                colrange = list(range(0, self.ColumnCount))
            else:
                rowrange = list(range(0, self.RowCount))
                colrange = sel
            txtToCopy = valuesForRange(rowrange, colrange)
        self.Application.copyToClipboard(txtToCopy)

    def getBizobj(self):
        """
        Get the bizobj that is controlling this grid.

        Either there was an explicitly-set bizobj reference in
        self.DataSource, in which case that is returned, or self.DataSource
        is a string, in which case the form hierarchy is walked finding the
        first bizobj with the correct DataSource.

        Return None if no bizobj can be located.
        """
        ds = self.DataSource
        if isinstance(ds, biz.dBizobj):
            return ds
        if isinstance(ds, str) and self.Form is not None:
            form = self.Form
            while form is not None:
                if hasattr(form, "getBizobj"):
                    bizobj = form.getBizobj(ds)
                    if isinstance(bizobj, biz.dBizobj):
                        return bizobj
                form = form.Form
        return None

    def setRowHeight(self, row, ht):
        """Explicitly set the height of a specific row in the grid. If
        SameSizeRows is True, all rows will be affected.
        """
        if self.SameSizeRows:
            self.RowHeight = ht
        else:
            if row >= self.RowCount:
                rcm = self.RowCount - 1
                dabo_module.error(
                    _(
                        "Specified row is out of range for setRowHeight(). "
                        "Attempted: %(row)s; max row: %(rcm)s"
                    )
                    % locals()
                )
                return
            self.SetRowSize(row, ht)

    def _getWxHeader(self):
        """Return the wx grid header window."""
        return self.GetGridColLabelWindow()

    def _syncCurrentRow(self):
        """
        Sync the CurrentRow of the grid to the RowNumber of the bizobj.

        Has no effect if the grid's DataSource isn't a link to a bizobj.
        """
        try:
            self.CurrentRow = self.getBizobj().RowNumber
        except AttributeError:
            pass
        # On Win, when row is deleted, active row remains unselected.
        if self.SelectionMode == "Row":
            row = self.CurrentRow
            if row not in self.Selection:
                self.SelectRow(row)

    def _syncColumnCount(self):
        """Sync wx's rendition of column count with our self.ColumnCount"""
        msg = None
        wxColumnCount = self.GetNumberCols()
        daboColumnCount = len([col for col in self.Columns if col.Visible])
        diff = daboColumnCount - wxColumnCount

        self.BeginBatch()
        if diff < 0:
            msg = wx.grid.GridTableMessage(
                self._Table, wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED, 0, abs(diff)
            )
        elif diff > 0:
            msg = wx.grid.GridTableMessage(
                self._Table, wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED, diff
            )
        if msg:
            self.ProcessTableMessage(msg)
        self.EndBatch()

        # Update the visible columns attribute
        self._updateDaboVisibleColumns()

        # We need to adjust the Width of visible columns here, in case any
        # columns have Visible = False.
        for daboCol, colObj in enumerate(self._columns):
            wxCol = self._convertDaboColNumToWxColNum(daboCol)
            if wxCol is not None:
                self.SetColSize(wxCol, colObj.Width)

    def _syncRowCount(self):
        """Sync wx's rendition of row count with our self.RowCount"""
        msg = None
        wxRowCount = self.GetNumberRows()
        daboRowCount = self.RowCount
        diff = daboRowCount - wxRowCount
        if diff < 0:
            msg = wx.grid.GridTableMessage(
                self._Table, wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, 0, abs(diff)
            )
        elif diff > 0:
            msg = wx.grid.GridTableMessage(
                self._Table, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED, diff
            )
        if msg:
            self.ProcessTableMessage(msg)

    def _getDefaultGridColAttr(self):
        """Return the GridCellAttr that will be used for all columns by default."""
        attr = wx.grid.GridCellAttr()
        attr.SetAlignment(wx.ALIGN_TOP, wx.ALIGN_LEFT)
        attr.SetReadOnly(True)
        return attr

    def _getUserSetting(self, prop):
        """Get the value of prop from the user settings table."""
        app = self.Application
        form = self.Form
        ret = None
        if app is not None and form is not None and not hasattr(self, "isDesignerControl"):
            settingName = "%s.%s.%s" % (form.Name, self.Name, prop)
            ret = app.getUserSetting(settingName)
        return ret

    def _setUserSetting(self, prop, val):
        """Persist the value of prop to the user settings table."""
        app = self.Application
        form = self.Form
        if app is not None and form is not None and not hasattr(self, "isDesignerControl"):
            settingName = "%s.%s.%s" % (form.Name, self.Name, prop)
            app.setUserSetting(settingName, val)

    def _enableDoubleBuffering(self):
        for win in (self.GetGridWindow(), self.GetGridColLabelWindow()):
            if not win.IsDoubleBuffered():
                win.SetDoubleBuffered(True)

    def _disableDoubleBuffering(self):
        for win in (self.GetGridWindow(), self.GetGridColLabelWindow()):
            if win.IsDoubleBuffered():
                win.SetDoubleBuffered(False)

    ##----------------------------------------------------------##
    ##          begin: event callbacks for internal use            ##
    ##----------------------------------------------------------##
    def _onGridCellEdited(self, evt):
        ## force cache to update after an edit:
        row, col = evt.EventData["row"], evt.EventData["col"]
        self.GetCellValue(row, col, useCache=False)

    def _onGridColSize(self, evt):
        "Occurs when the user resizes the width of the column."
        colNum = evt.EventData["col"]
        col = self.Columns[colNum]
        colName = "Column_%s" % col.DataField
        # Sync our column object up with what the grid is reporting, and because
        # the user made this change, save to the userSettings:
        col.Width = self.GetColSize(self._convertDaboColNumToWxColNum(colNum))
        col._persist("Width")
        self._disableDoubleBuffering()
        self._enableDoubleBuffering()
        ui.callAfterInterval(20, self._updateColumnWidths)

    def _onGridHeaderMouseMove(self, evt):
        curMousePosition = evt.EventData["mousePosition"]
        headerIsDragging = self._headerDragging
        headerIsSizing = self._headerSizing
        dragging = evt.EventData["mouseDown"] and (
            curMousePosition != self._lastHeaderMousePosition
        )
        header = self._getWxHeader()

        if dragging:
            self._lastHeaderMousePosition = evt.EventData["mousePosition"]
            x, y = self._lastHeaderMousePosition

            if not headerIsSizing and (
                self.getColNumByX(x) == self.getColNumByX(x - 5) == self.getColNumByX(x + 5)
            ):
                if not headerIsDragging:
                    curCol = self.getColByX(x)
                    if self.MovableColumns and curCol and curCol.Movable:
                        # A header reposition is beginning
                        self._headerDragging = True
                        self._headerDragFrom = (x, y)
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
        """
        Occurs when the left mouse button is released in the grid header.

        Basically, this comes down to two possibilities: the end of a drag
        operation, or a single-click operation. If we were dragging, then
        it is possible a column needs to change position. If we were clicking,
        then it is a sort operation.
        """
        x, y = evt.EventData["mousePosition"]
        if self._headerDragging:
            # A drag action is ending
            self._headerDragTo = (x, y)

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
            col = self.getColNumByX(x)
            self.processSort(col)
        self._headerDragging = False
        self._headerSizing = False
        ## pkm: commented out the evt.Continue=False because it doesn't appear
        ##        to be needed, and it prevents the native UI from responding.
        # evt.Continue = False

    def _onGridHeaderMouseRightClick(self, evt):
        ui.callAfter(self._showHeaderContextMenu)

    def _showHeaderContextMenu(self):
        # Make the popup menu appear in the location that was clicked. We init
        # the menu here, then call the user hook method to optionally fill the
        # menu. If we get a menu back from the user hook, we display it.
        menu = dMenu()

        # Fill the default menu item(s):
        def _autosizeColumn(evt):
            self.autoSizeCol(self.getColNumByX(self.getMousePosition()[0]), persist=True)

        def _autosizeAllColumns(evt):
            self.autoSizeCol("All")

        if self.ResizableColumns:
            menu.append(
                _("&Autosize Column"),
                OnHit=_autosizeColumn,
                help=_("Autosize the column based on the data in the column."),
            )
            menu.append(
                _("&Autosize All Columns"),
                OnHit=_autosizeAllColumns,
                help=_("Autosize all columns in the grid."),
            )

        menu = self.fillHeaderContextMenu(menu)

        if menu is not None and len(menu.Children) > 0:
            self.showContextMenu(menu)

    def _onGridHeaderMouseRightUp(self, evt):
        """Occurs when the right mouse button goes up in the grid header."""
        pass

    _onGridHeaderContextMenu = _onGridHeaderMouseRightUp

    def _onGridMouseRightClick(self, evt):
        # Make the popup menu appear in the location that was clicked. We init
        # the menu here, then call the user hook method to optionally fill the
        # menu. If we get a menu back from the user hook, we display it.

        # First though, make the cell the user right-clicked on the current cell:
        if self.MultipleSelection:
            # Don't erase the multiple selection if the user clicks on a valid
            # row or column:
            if "row" in self.SelectionMode.lower() and evt.row not in self.Selection:
                self.CurrentRow = evt.row
            elif "col" in self.SelectionMode.lower() and evt.col not in self.Selection:
                self.CurrentCol = evt.col
            elif "cel" in self.SelectionMode.lower():
                self.CurrentRow = evt.row
                self.CurrentCol = evt.col
        else:
            self.CurrentRow = evt.row
            self.CurrentColumn = evt.col

        menu = dMenu()
        menu = self.fillContextMenu(menu)

        if menu is not None and len(menu.Children) > 0:
            self.showContextMenu(menu)

    _onContextMenu = _onGridMouseRightClick

    def _onGridHeaderMouseLeftDown(self, evt):
        # Clicking a column header will select that column, like a spreadsheet, even when
        # SelectionMode is set to something else. Row mode seems to work correctly, but Cell mode
        # doesn't, so this code will save the selection, and then restore it after.
        self._lastHeaderMousePosition = evt.EventData["mousePosition"]
        self._headerDragging = False
        self._headerSizing = False

        if self.SelectionMode == "Cell":
            # Save the selection
            tl = self.GetSelectionBlockTopLeft()
            br = self.GetSelectionBlockBottomRight()
            # Need to convert these grid references to tuples
            tl_tuple = tuple([(elem.Row, elem.Col) for elem in tl])
            br_tuple = tuple([(elem.Row, elem.Col) for elem in br])
            ui.callAfter(self._restore_cell_selection, tl_tuple, br_tuple)

    def _restore_cell_selection(self, tl, br):
        self.ClearSelection()
        self.SelectionMode = "Cell"
        for pos in range(len(tl)):
            self.SelectBlock(tl[pos][0], tl[pos][1], br[pos][0], br[pos][1], addToSelected=True)

    def _onGridMouseLeftClick(self, evt):
        self.ShowCellEditControl()

    def _onGridRowSize(self, evt):
        """
        Occurs when the user sizes the height of the row. If the
        property 'SameSizeRows' is True, Dabo overrides the wxPython
        default and applies that size change to all rows, not just the row
        the user sized.
        """
        row = evt.EventData["row"]
        if row is None or row < 0 or row > self.RowCount:
            # pkm: This has happened but I don't know why. Treat as spurious.
            return

        if self.SameSizeRows:
            try:
                self.RowHeight = self.GetRowSize(row)
            except wx._core.PyAssertionError:
                # pkm: I don't understand how it could have gotten this far, but
                #      I got an error report that the c++ assertion row>=0 && row<m_numrows failed.
                pass

    def _onGridCellSelected(self, evt):
        """Occurs when the grid's cell focus has changed."""
        threshold = 0.2
        last = getattr(self, "_lastCellSelectedTime", 0)
        cur = self._lastCellSelectedTime = time.time()
        # self._gridCellSelectedNewRowCol = (evt.EventData["row"], evt.EventData["col"])
        if cur - last > threshold:
            # Update immediately:
            self._gridCellSelectedOldRow = self.CurrentRow
            self._updateCellSelection((evt.EventData["row"], evt.EventData["col"]))
            return
        # Let the grid scroll as fast as possible while rapid-fire keyboard navigation is
        # occurring, but <threshold> seconds later, sync up the bizobj and update the selection:
        if getattr(self, "_gridCellSelectedOldRow", None) is None:
            self._gridCellSelectedOldRow = self.CurrentRow
        ui.callAfterInterval(threshold * 1000, self._updateCellSelection)

    def _updateCellSelection(self, newRowCol=None):
        if self._inUpdateSelection:
            return

        oldRow = self._gridCellSelectedOldRow
        self._gridCellSelectedOldRow = None
        if newRowCol is None:
            newRowCol = (self.CurrentRow, self.CurrentColumn)
        newRow = newRowCol[0]
        newCol = self._convertWxColNumToDaboColNum(newRowCol[1])
        try:
            col = self.Columns[newCol]
        except (IndexError, TypeError):
            col = None

        if col and col.Editable and self.Editable:
            return  ## segfault avoidance

        ## pkm 2005-09-28: This works around a nasty segfault:
        self.HideCellEditControl()
        ## but periodically test it. My current version: 2.6.1.1pre

        if col:
            ## pkm 2005-09-28: Part of the editor segfault workaround. This sets the
            ##                   editor for the entire column, at a point in time before
            ##                   the grid is actually asking for the editor, and in a
            ##                   fashion that ensures the editor instance doesn't go
            ##                   out of scope prematurely.
            col._setEditor(newRow)

        if col and (
            self.Editable
            and col.Editable
            and not self._vetoAllEditing
            and self.ActivateEditorOnSelect
        ):
            ui.callAfter(self.EnableCellEditControl)
        if oldRow != newRow:
            bizobj = self.getBizobj()
            if bizobj and not self._dataSourceBeingSet:
                # Don't run any of this code if this is the initial setting of the DataSource
                if bizobj.RowCount > newRow and bizobj.RowNumber != newRow:
                    if self._mediateRowNumberThroughForm and isinstance(self.Form, dForm):
                        # run it through the form:
                        if not self.Form.moveToRowNumber(newRow, bizobj):
                            ui.callAfter(self.refresh)
                    else:
                        # run it through the bizobj directly:
                        try:
                            bizobj.RowNumber = newRow
                            self.Form.update()
                        except exceptions.BusinessRuleViolation as e:
                            ui.stop(e)
                            ui.callAfter(self.refresh)
                else:
                    # We are probably trying to select row 0 when there are no records
                    # in the bizobj.
                    ##pkm: the following call causes an assertion on Mac, and appears to be
                    ##       unneccesary.
                    # self.SetGridCursor(0,0)
                    pass
        self._dataSourceBeingSet = False
        ui.callAfterInterval(50, self._updateSelection)

    def _updateSelection(self):
        if self._inUpdateSelection or self.SelectionMode == "Cell":
            return
        self._inUpdateSelection = True
        self.Freeze()
        self.ClearSelection()
        fnc = {"Row": self.SelectRow, "Col": self.SelectCol}[self.SelectionMode]
        for num in self.Selection:
            fnc(num, True)
        self.Thaw()
        self._inUpdateSelection = False

    def _checkSelectionType(self):
        """
        When the SelectionMode or MultipleSelection properties change,
        we want to make sure that the selection reflects those settings.
        """
        mode = self.SelectionMode
        if mode == "Row":
            self.SelectRow(self.CurrentRow)
        elif mode == "Col":
            self.SelectCol(self.CurrentColumn)
        else:
            self.SelectBlock(
                self.CurrentRow, self.CurrentColumn, self.CurrentRow, self.CurrentColumn
            )
        self.refresh()

    def _onKeyDown(self, evt):
        keycode = evt.EventData["keyCode"]

        if keycode == 27:
            # esc pressed. Grid will eat it by default. But if we are in a dialog with
            # a cancel button, let's runCancel() since that's what the user likely wants:
            if hasattr(self.Form, "runCancel"):
                self.Form.runCancel()
        if keycode == 9 and self.TabNavigates:
            evt.stop()
            self.Navigate(not evt.EventData["shiftDown"])

    def _onKeyChar(self, evt):
        """Occurs when the user presses a key inside the grid."""
        columns = self.Columns
        current_col = self.CurrentColumn
        if not columns or (
            self.Editable and columns[current_col].Editable and not self._vetoAllEditing
        ):
            # Can't search and edit at the same time
            return

        keyCode = evt.EventData["unicodeKey"]
        try:
            char = chr(keyCode)
        except ValueError:
            # keycode not in ascii range
            return

        if (
            keyCode
            in (
                dKeys.key_Left,
                dKeys.key_Right,
                dKeys.key_Up,
                dKeys.key_Down,
                dKeys.key_Pageup,
                dKeys.key_Pagedown,
                dKeys.key_Home,
                dKeys.key_End,
            )
            or evt.EventData["hasModifiers"]
        ):
            # Enter, Tab, and Arrow Keys shouldn't be searched on.
            return

        if self.Searchable and columns[current_col].Searchable:
            self.addToSearchStr(char)
            # For some reason, without this the key happens twice
            evt.stop()

    ##----------------------------------------------------------##
    ##          end: event callbacks for internal use            ##
    ##----------------------------------------------------------##

    def _calcRanges(self, seq, rowOrCol):
        startPoints = []
        nextVal = -1
        maxIdx = len(seq) - 1
        for idx, pt in enumerate(seq):
            if idx == 0:
                startPoints.append(pt)
                nextVal = pt + 1
            else:
                if pt == nextVal:
                    nextVal += 1
                else:
                    startPoints.append(pt)
                    nextVal = pt + 1

        endPoints = []
        for pt in startPoints:
            idx = seq.index(pt)
            if idx == maxIdx:
                endPoints.append(pt)
            else:
                found = False
                while idx < maxIdx:
                    if seq[idx + 1] == pt + 1:
                        idx += 1
                        pt += 1
                    else:
                        endPoints.append(pt)
                        found = True
                        break
                if not found:
                    endPoints.append(pt)

        typ = rowOrCol.lower()[:3]
        if typ == "row":
            cols = self.ColumnCount
            rangeStart = [(r, 0) for r in startPoints]
            rangeEnd = [(r, cols) for r in endPoints]
        elif typ == "col":
            rows = self.RowCount
            rangeStart = [(0, c) for c in startPoints]
            rangeEnd = [(rows, c) for c in endPoints]
        return list(zip(rangeStart, rangeEnd))

    ##----------------------------------------------------------##
    ##        begin: wx callbacks to re-route to events            ##
    ##----------------------------------------------------------##

    ## dGrid has to reimplement all of this to augment what dPemMixin does,
    ## to offer separate events in the grid versus the header region.
    def __onWxContextMenu(self, evt):
        self.raiseEvent(events.GridContextMenu, evt)
        evt.Skip()

    def __onWxGridColSize(self, evt):
        daboCol = self._convertWxColNumToDaboColNum(evt.GetRowOrCol())
        colObj = self.Columns[daboCol]
        if self.ResizableColumns and colObj.Resizable:
            self.raiseEvent(events.GridColSize, col=daboCol)
        else:
            # need to reference the Width property for some reason:
            colObj.Width
            evt.Veto()
            self._refreshHeader()

    def __onWxGridSelectCell(self, evt):
        if getattr(self, "_inSelect", False) or getattr(self, "_inUpdateSelection", False):
            # Avoid recursion
            return
        if self.ColumnCount == 0:
            # Grid is not fully constructed yet
            return
        col = self.Columns[evt.GetCol()]
        if col.Editable and col.RendererClass == col.boolRendererClass:
            # user is clicking on a checkbox
            wx.CallAfter(self.EnableCellEditControl)
        self._inSelect = True
        if evt.Selecting():
            self._updateWxSelection(evt)
        self.raiseEvent(events.GridCellSelected, evt)
        self._lastRow, self._lastCol = evt.GetRow(), evt.GetCol()
        if not sys.platform.startswith("win"):
            evt.Skip()
        self._inSelect = False

    def __onWxGridRangeSelect(self, evt):
        if self._inRangeSelect:
            # avoid recursive events
            return
        self._inRangeSelect = True
        if evt.Selecting():
            self._updateWxSelection(evt)
        self.raiseEvent(events.GridRangeSelected, evt)
        evt.Skip()
        self._inRangeSelect = False

    def __onWxScrollWin(self, evt):
        evtClass = ui.getScrollWinEventClass(evt)
        self.raiseEvent(evtClass, evt)
        evt.Skip()

    def _updateWxSelection(self, evt):
        if self.MultipleSelection:
            # Nothing to do
            return
        origRow, origCol = self.CurrentRow, self.CurrentColumn
        mode = self.GetSelectionMode()
        try:
            top, bott = evt.GetTopRow(), evt.GetBottomRow()
        except AttributeError:
            top = bott = evt.GetRow()
        try:
            left, right = evt.GetLeftCol(), evt.GetRightCol()
        except AttributeError:
            left = right = evt.GetCol()
        if mode == wx.grid.Grid.GridSelectRows:
            if (top != bott) or (top != origCol):
                # Attempting to select a range
                if top == origRow:
                    row = bott
                else:
                    row = top
                if self._lastCol is not None:
                    self.SetGridCursor(row, self._lastCol)
                    self.SelectRow(row)
        elif mode == wx.grid.Grid.GridSelectColumns:
            if (left != right) or (left != origCol):
                # Attempting to select a range
                if left == origCol:
                    col = right
                else:
                    col = left
                self.SetGridCursor(self._lastRow, col)
                self.SelectCol(col)
        else:
            # Cells
            chg = False
            row, col = origRow, origCol
            if top != bott:
                chg = True
                if top == origRow:
                    row = bott
                else:
                    row = top
            elif top != origRow:
                # New row
                chg = True
                row = top
            if left != right:
                chg = True
                if left == origCol:
                    col = right
                else:
                    col = left
            elif left != origCol:
                # New col
                chg = True
                col = left
            if chg:
                self.SetGridCursor(row, col)
                self.SelectBlock(row, col, row, col)

    def __onWxGridEditorShown(self, evt):
        self.raiseEvent(events.GridCellEditBegin, evt)

        # Need to reapply the edit controls dynamic properties. (Be careful to not inflate the
        # editors refcount)
        editor = self.GetCellEditor(evt.GetRow(), evt.GetCol())
        ctrl = editor.GetControl()
        editor.DecRef()
        if hasattr(
            ctrl, "initProperties"
        ):  # Don't want to cause an error while operating on a stock editor.
            ctrl.initProperties()

        evt.Skip()

    def __onWxGridEditorHidden(self, evt):
        self.raiseEvent(events.GridCellEditEnd, evt)
        evt.Skip()

    def _toggleCheckBox(self):
        ed = getattr(self, "_activeEditorControl", None)
        if ed:
            ed.SetValue(not ed.GetValue())
            self._checkBoxToggled(ed)

    def _checkBoxToggled(self, obj):
        # Force the flushing of the value immediately, instead of waiting for the
        # editor to lose focus (where the flush will happen a second time).
        self._Table.SetValue(self.CurrentRow, self.CurrentColumn, obj.GetValue())
        self.raiseEvent(events.GridCellEditorHit)

    def __onGridCellLeftClick_toggleCB(self, evt):
        col = self.Columns[evt.GetCol()]
        if col.RendererClass == col.boolRendererClass:
            ui.callAfterInterval(100, self._toggleCheckBox)
        evt.Skip()

    def __onWxGridEditorCreated(self, evt):
        """Bind the kill focus event to the newly instantiated cell editor"""
        editor = evt.GetControl()
        if editor is None:
            return

        editor.Bind(wx.EVT_KILL_FOCUS, self.__onWxGridCellEditorKillFocus)

        col = self.Columns[evt.GetCol()]
        if col.RendererClass == col.boolRendererClass:

            def onKeyDown(evt):
                if evt.KeyCode == wx.WXK_UP:
                    if self.GetGridCursorRow() > 0:
                        self.DisableCellEditControl()
                        self.MoveCursorUp(False)
                elif evt.KeyCode == wx.WXK_DOWN:
                    if self.GetGridCursorRow() < (self.GetNumberRows() - 1):
                        self.DisableCellEditControl()
                        self.MoveCursorDown(False)
                elif evt.KeyCode == wx.WXK_LEFT:
                    if self.GetGridCursorCol() > 0:
                        self.DisableCellEditControl()
                        self.MoveCursorLeft(False)
                elif evt.KeyCode == wx.WXK_RIGHT:
                    if self.GetGridCursorCol() < (self.GetNumberCols() - 1):
                        self.DisableCellEditControl()
                        self.MoveCursorRight(False)
                else:
                    evt.Skip()

            def onHit(evt):
                self._checkBoxToggled(editor)

            ed = self._activeEditorControl = evt.GetControl()
            style = ed.GetWindowStyle()
            style |= wx.WANTS_CHARS
            ed.SetWindowStyle(style)
            ed.Bind(wx.EVT_KEY_DOWN, onKeyDown)
            ed.Bind(wx.EVT_CHECKBOX, onHit)
        evt.Skip()

    def __onWxGridCellEditorKillFocus(self, evt):
        # Cell editor's grandparent, the grid GridWindow's parent, is the grid.
        self.SaveEditControlValue()
        self.HideCellEditControl()
        evt.Skip()

    def __onWxGridCellChange(self, evt):
        self.raiseEvent(events.GridCellEdited, evt)
        evt.Skip()

    def __onWxGridRowSize(self, evt):
        self.raiseEvent(events.GridRowSize, evt)
        evt.Skip()

    def __onWxHeaderContextMenu(self, evt):
        col, row = self._getColRowForPosition(evt.GetPosition())
        self.raiseEvent(events.GridHeaderContextMenu, evt, col=col)
        evt.Skip()

    def __onWxHeaderIdle(self, evt):
        self.raiseEvent(events.GridHeaderIdle, evt)
        evt.Skip()

    def __onWxHeaderMouseEnter(self, evt):
        col, row = self._getColRowForPosition(evt.GetPosition())
        self.raiseEvent(events.GridHeaderMouseEnter, evt, col=col)
        evt.Skip()

    def __onWxHeaderMouseLeave(self, evt):
        col, row = self._getColRowForPosition(evt.GetPosition())
        self._headerMouseLeftDown, self._headerMouseRightDown = False, False
        self.raiseEvent(events.GridHeaderMouseLeave, evt, col=col)
        evt.Skip()

    def __onWxHeaderMouseLeftDoubleClick(self, evt):
        col, row = self._getColRowForPosition(evt.GetPosition())
        self.raiseEvent(events.GridHeaderMouseLeftDoubleClick, evt, col=col)
        evt.Skip()

    def __onWxHeaderMouseLeftDown(self, evt):
        col, row = self._getColRowForPosition(evt.GetPosition())
        self.raiseEvent(events.GridHeaderMouseLeftDown, evt, col=col)
        self._headerMouseLeftDown = True
        # evt.Skip() #- don't skip or all the rows will be selected.

    def __onWxHeaderMouseLeftUp(self, evt):
        ui.callAfter(self._enableDoubleBuffering)
        col, row = self._getColRowForPosition(evt.GetPosition())
        self.raiseEvent(events.GridHeaderMouseLeftUp, evt, col=col)
        if self._headerMouseLeftDown:
            # mouse went down and up in the header: send a click:
            self.raiseEvent(events.GridHeaderMouseLeftClick, evt, col=col)
            self._headerMouseLeftDown = False
        evt.Skip()

    def __onWxHeaderMouseMotion(self, evt):
        if ui.isMouseLeftDown():
            self._disableDoubleBuffering()
        col, row = self._getColRowForPosition(evt.GetPosition())
        self.raiseEvent(events.GridHeaderMouseMove, evt, col=col)
        evt.Skip()

    def __onWxHeaderMouseRightDown(self, evt):
        col, row = self._getColRowForPosition(evt.GetPosition())
        self.raiseEvent(events.GridHeaderMouseRightDown, evt, col=col)
        self._headerMouseRightDown = True
        evt.Skip()

    def __onWxHeaderMouseRightUp(self, evt):
        col, row = self._getColRowForPosition(evt.GetPosition())
        self.raiseEvent(events.GridHeaderMouseRightUp, evt, col=col)
        if self._headerMouseRightDown:
            # mouse went down and up in the header: send a click:
            self.raiseEvent(events.GridHeaderMouseRightClick, evt)
            self._headerMouseRightDown = False
        evt.Skip()

    def __onWxHeaderPaint(self, evt):
        self._paintHeader()
        evt.Skip()

    def _getColRowForPosition(self, pos):
        """Used in the mouse event handlers to stuff the col, row into EventData."""
        col = self.getColNumByX(pos[0])
        row = self.getRowNumByY(pos[1])
        if (col and row) and (col < 0 or row < 0):
            # click was outside grid cell area
            col, row = None, None
        return col, row

    def __onWxMouseLeftDoubleClick(self, evt):
        col, row = self._getColRowForPosition(evt.GetPosition())
        self.raiseEvent(events.GridMouseLeftDoubleClick, evt, col=col, row=row)
        evt.Skip()

    def __onWxMouseLeftDown(self, evt):
        col, row = self._getColRowForPosition(evt.GetPosition())
        self.raiseEvent(events.GridMouseLeftDown, evt, col=col, row=row)
        self._mouseLeftDown = (col, row)
        evt.Skip()

    def __onWxMouseLeftUp(self, evt):
        ui.callAfter(self._enableDoubleBuffering)
        col, row = self._getColRowForPosition(evt.GetPosition())
        self.raiseEvent(events.GridMouseLeftUp, evt, col=col, row=row)
        if getattr(self, "_mouseLeftDown", (None, None)) == (col, row):
            # mouse went down and up in this cell: send a click:
            self.raiseEvent(events.GridMouseLeftClick, evt, col=col, row=row)
            self._mouseLeftDown = (None, None)
        evt.Skip()

    def __onWxMouseMotion(self, evt):
        if ui.isMouseLeftDown():
            self._disableDoubleBuffering()
        col, row = self._getColRowForPosition(evt.GetPosition())
        self.raiseEvent(events.GridMouseMove, evt, col=col, row=row)
        evt.Skip()

    def __onWxMouseRightDown(self, evt):
        col, row = self._getColRowForPosition(evt.GetPosition())
        self.raiseEvent(events.GridMouseRightDown, evt, col=col, row=row)
        self._mouseRightDown = (col, row)
        evt.Skip()

    def __onWxMouseRightUp(self, evt):
        col, row = self._getColRowForPosition(evt.GetPosition())
        self.raiseEvent(events.GridMouseRightUp, evt, col=col, row=row)
        if getattr(self, "_mouseRightDown", (None, None)) == (col, row):
            # mouse went down and up in this cell: send a click:
            self.raiseEvent(events.GridMouseRightClick, evt, col=col, row=row)
            self._mouseRightDown = (None, None)
        evt.Skip()

    ##----------------------------------------------------------##
    ##         end: wx callbacks to re-route to events            ##
    ##----------------------------------------------------------##

    ##----------------------------------------------------------##
    ##                begin: property definitions                    ##
    ##----------------------------------------------------------##
    @property
    def ActivateEditorOnSelect(self):
        """Specifies whether the cell editor, if any, is activated upon cell selection."""
        try:
            v = self._activateEditorOnSelect
        except AttributeError:
            v = self._activateEditorOnSelect = True
        return v

    @ActivateEditorOnSelect.setter
    def ActivateEditorOnSelect(self, val):
        self._activateEditorOnSelect = bool(val)

    @property
    def AlternateRowColoring(self):
        """
        When True, alternate rows of the grid are colored according to
        the RowColorOdd and RowColorEven properties  (bool)
        """
        return self._alternateRowColoring

    @AlternateRowColoring.setter
    def AlternateRowColoring(self, val):
        if self._constructed():
            self._alternateRowColoring = val
            self.setTableAttributes(self._Table)
            self.Refresh()
        else:
            self._properties["AlternateRowColoring"] = val

    @property
    def AutoAdjustHeaderHeight(self):
        """
        When True, changing the VerticalHeaders property will adjust the HeaderHeight
        to accommodate the rotated labels. Default=False.  (bool)
        """
        return self._autoAdjustHeaderHeight

    @AutoAdjustHeaderHeight.setter
    def AutoAdjustHeaderHeight(self, val):
        if self._constructed():
            self._autoAdjustHeaderHeight = val
            self.refresh()
            if val:
                self.fitHeaderHeight()
        else:
            self._properties["AutoAdjustHeaderHeight"] = val

    @property
    def CellHighlightWidth(self):
        """Specifies the width of the cell highlight box."""
        return self.GetCellHighlightPenWidth()

    @CellHighlightWidth.setter
    def CellHighlightWidth(self, val):
        if self._constructed():
            self.SetCellHighlightPenWidth(val)
            self.SetCellHighlightROPenWidth(val)
        else:
            self._properties["CellHighlightWidth"] = val

    @property
    def Columns(self):
        """List of dColumns.  (list)"""
        return self._columns

    @property
    def ColumnClass(self):
        """
        Class to instantiate when a change to ColumnCount requires additional columns to be created.
        Default=dColumn.  (dColumn subclass)
        """
        return self._columnClass

    @ColumnClass.setter
    def ColumnClass(self, val):
        self._columnClass = val

    @property
    def ColumnCount(self):
        """Number of columns in the grid.  (int)"""
        return len(self.Columns)

    @ColumnCount.setter
    def ColumnCount(self, val):
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

    @property
    def CurrCellVal(self):
        """Value of the currently selected grid cell  (varies)"""
        return self.GetValue(self.GetGridCursorRow(), self.GetGridCursorCol())

    @CurrCellVal.setter
    def CurrCellVal(self, val):
        self.SetValue(self.GetGridCursorRow(), self.GetGridCursorCol(), val)
        self.refresh()

    @property
    def CurrentColumn(self):
        """Currently selected column index. (int)"""
        return self.GetGridCursorCol()

    @CurrentColumn.setter
    def CurrentColumn(self, val):
        if self._constructed():
            if val > -1:
                val = min(val, self.ColumnCount)
                rn = self.CurrentRow
                self.SetGridCursor(rn, val)
                self.MakeCellVisible(rn, val)
        else:
            self._properties["CurrentColumn"] = val

    @property
    def CurrentField(self):
        """Field for the currently selected column    (str)"""
        return self.Columns[self.GetGridCursorCol()].DataField

    @CurrentField.setter
    def CurrentField(self, val):
        if self._constructed():
            for ii in range(len(self.Columns)):
                if self.Columns[ii].DataField == val:
                    self.CurrentColumn = ii
                    break
        else:
            self._properties["CurrentField"] = val

    @property
    def CurrentRow(self):
        """Currently selected row  (int)"""
        return self.GetGridCursorRow()

    @CurrentRow.setter
    def CurrentRow(self, val):
        if self._constructed():
            curr = self.GetGridCursorRow()
            if val >= self.RowCount:
                val = self.RowCount - 1
            if val < 0:
                val = 0
            cn = self.CurrentColumn
            if curr != val:
                # The row is being changed
                val = max(0, val)
                cn = max(0, cn)
                self.SetGridCursor(val, cn)
                self.MakeCellVisible(val, cn)
        else:
            self._properties["CurrentRow"] = val

    @property
    def DataSet(self):
        """
        The set of data displayed in the grid.  (set of dicts)

        When DataSource isn't defined, setting DataSet to a set of dicts, such as what you get from
        calling dBizobj.getDataSet(), will define the source of the data that the grid displays.

        If DataSource is defined, DataSet is read-only and returns the dataSet from the bizobj.
        """
        if self.DataSource is not None:
            ret = None
            bo = self.getBizobj()
            try:
                ret = bo.getDataSet()
            except AttributeError:
                # See if the DataSource is a reference
                try:
                    ret = eval(self.DataSource)
                except Exception:
                    # If it fails for any reason, bail.
                    pass
            self._dataSet = ret
        else:
            try:
                ret = self._dataSet
            except AttributeError:
                ret = self._dataSet = None
        return ret

    @DataSet.setter
    def DataSet(self, val):
        if self._constructed():
            if (self.DataSource is not None) and not hasattr(self, "isDesignerControl"):
                raise ValueError("Cannot set DataSet: DataSource defined.")
            # We must make sure the grid's table is initialized first:
            self._Table
            if not isinstance(val, db.dDataSet):
                val = db.dDataSet(val)
            self._dataSet = val
            self.fillGrid()
            self._syncAll()
            if not self._settingDataSetFromSort:
                # Force the grid to maintain its current sort order
                self._restoreSort()
                ui.callAfter(self.refresh)
        else:
            self._properties["DataSet"] = val

    @property
    def DataSource(self):
        """
        The source of the data to display in the grid.  (str)

        This corresponds to a bizobj with a matching DataSource on the form, and setting this makes
        it impossible to set DataSet.
        """
        try:
            v = self._dataSource
        except AttributeError:
            v = self._dataSource = None
        return v

    @DataSource.setter
    def DataSource(self, val):
        if self._constructed():
            # We must make sure the grid's table is initialized first:
            self._Table
            self._dataSet = None
            self._dataSource = val
            self.fillGrid(True)
            biz = self.getBizobj()
            if self.USE_DATASOURCE_BEING_SET_HACK:
                self._dataSourceBeingSet = True
            if biz:
                ui.setAfter(self, "CurrentRow", biz.RowNumber)
        else:
            self._properties["DataSource"] = val

    @property
    def Editable(self):
        """
        This setting enables/disables cell editing globally.  (bool)

        When False, no cells will be editable by the user. When True, cells in columns set as
        Editable will be editable by the user. Note that grids and columns are both set with
        Editable=False by default, so to enable cell editing you need to turn it on in the
        appropriate column as well as in the grid.
        """
        return self.IsEditable()

    @Editable.setter
    def Editable(self, val):
        if self._constructed():
            self.EnableEditing(val)
        else:
            self._properties["Editable"] = val

    @property
    def Encoding(self):
        """
        Optional color for the background of the column headers.  (str or None)

        This is only the default: setting the corresponding dColumn property will override.
        """
        try:
            ret = self.getBizobj().Encoding
        except AttributeError:
            ret = settings.getEncoding()
        return ret

    @property
    def HeaderBackColor(self):
        """
        Optional color for the background of the column headers.  (str or None)

        This is only the default: setting the corresponding dColumn property will override.
        """
        return self._headerBackColor

    @HeaderBackColor.setter
    def HeaderBackColor(self, val):
        if self._constructed():
            if isinstance(val, str):
                val = color_tools.colorTupleFromName(val)
            self._headerBackColor = val
            self.refresh()
        else:
            self._properties["HeaderBackColor"] = val

    @property
    def HeaderForeColor(self):
        """
        Optional color for the foreground (text) of the column headers.  (str or None)

        This is only the default: setting the corresponding dColumn property will override.
        """
        return self._headerForeColor

    @HeaderForeColor.setter
    def HeaderForeColor(self, val):
        if self._constructed():
            if isinstance(val, str):
                val = color_tools.colorTupleFromName(val)
            self._headerForeColor = val
            self.refresh()
        else:
            self._properties["HeaderForeColor"] = val

    @property
    def HeaderHeight(self):
        """Height of the column headers.  (int)"""
        return self.GetColLabelSize()

    @HeaderHeight.setter
    def HeaderHeight(self, val):
        if self._constructed():
            if val <= 0:
                self._lastPositiveHeaderHeight = self.GetColLabelSize()
            self.SetColLabelSize(val)
        else:
            self._properties["HeaderHeight"] = val

    @property
    def HeaderHorizontalAlignment(self):
        """
        The horizontal alignment of the header captions. ('Left', 'Center', 'Right')

        This is only the default: setting the corresponding dColumn property will override.
        """
        return self._headerHorizontalAlignment

    @HeaderHorizontalAlignment.setter
    def HeaderHorizontalAlignment(self, val):
        if self._constructed():
            v = self._expandPropStringValue(val, ("Left", "Right", "Center"))
            self._headerHorizontalAlignment = v
            self.refresh()
        else:
            self._properties["HeaderHorizontalAlignment"] = val

    @property
    def HeaderVerticalAlignment(self):
        """
        The vertical alignment of the header captions. ('Top', 'Center', 'Bottom')

        This is only the default: setting the corresponding dColumn property will override.
        """
        return self._headerVerticalAlignment

    @HeaderVerticalAlignment.setter
    def HeaderVerticalAlignment(self, val):
        if self._constructed():
            v = self._expandPropStringValue(val, ("Top", "Bottom", "Center"))
            self._headerVerticalAlignment = v
            self.refresh()
        else:
            self._properties["HeaderVerticalAlignment"] = val

    @property
    def HorizontalScrolling(self):
        """Is scrolling enabled in the horizontal direction?  (bool)"""
        return self.GetScrollPixelsPerUnit()[0] > 0

    @HorizontalScrolling.setter
    def HorizontalScrolling(self, val):
        if self._constructed():
            if val:
                self.SetScrollRate(20, self.GetScrollPixelsPerUnit()[1])
            else:
                self.SetScrollRate(0, self.GetScrollPixelsPerUnit()[1])
            self.refresh()
        else:
            self._properties["HorizontalScrolling"] = val

    @property
    def MovableColumns(self):
        """When False, the user cannot re-order the columns by dragging the headers  (bool)"""
        return self._movableColumns

    @MovableColumns.setter
    def MovableColumns(self, val):
        self._movableColumns = val

    @property
    def MultipleSelection(self):
        """When True (default), more than one cell/row/col can be selected at once  (bool)"""
        return self._multipleSelection

    @MultipleSelection.setter
    def MultipleSelection(self, val):
        if self._constructed():
            if val != self._multipleSelection:
                self._multipleSelection = val
                self._checkSelectionType()
        else:
            self._properties["MultipleSelection"] = val

    @property
    def NoneDisplay(self):
        """Text to display for null (None) values.  (str)"""
        return self._noneDisplay

    @NoneDisplay.setter
    def NoneDisplay(self, val):
        if val is None:
            self._noneDisplay = self.__noneDisplayDefault
        else:
            assert isinstance(val, str)
            self._noneDisplay = val

    @property
    def ResizableColumns(self):
        """When False, the user cannot resize the columns  (bool)"""
        return self._resizableColumns

    @ResizableColumns.setter
    def ResizableColumns(self, val):
        self._resizableColumns = val

    @property
    def ResizableRows(self):
        """When False, the user cannot resize the rows  (bool)"""
        return self._resizableRows

    @ResizableRows.setter
    def ResizableRows(self, val):
        if self._constructed():
            self._resizableRows = val
            if val:
                self.EnableDragRowSize()
            else:
                self.DisableDragRowSize()
        else:
            self._properties["ResizableRows"] = val

    @property
    def RowColorEven(self):
        """
        When alternate row coloring is active, controls the color of the even rows  (str or tuple
        )"""
        return self._rowColorEven

    @RowColorEven.setter
    def RowColorEven(self, val):
        if self._constructed():
            self._rowColorEven = val
            self.setTableAttributes(self._Table)
        else:
            self._properties["RowColorEven"] = val

    @property
    def RowColorOdd(self):
        """
        When alternate row coloring is active, controls the color of the odd rows  (str or tuple)
        """
        return self._rowColorOdd

    @RowColorOdd.setter
    def RowColorOdd(self, val):
        if self._constructed():
            self._rowColorOdd = val
            self.setTableAttributes(self._Table)
        else:
            self._properties["RowColorOdd"] = val

    @property
    def RowCount(self):
        """Number of rows in the grid.  (int)"""
        try:
            self._tableRows = self.getBizobj().RowCount
        except AttributeError:
            pass
        return self._tableRows

    @property
    def RowHeight(self):
        """Row Height for all rows of the grid  (int)"""
        try:
            v = self._rowHeight
        except AttributeError:
            v = self._rowHeight = self.GetDefaultRowSize()
        return v

    @RowHeight.setter
    def RowHeight(self, val):
        if self._constructed():
            try:
                rh = self._rowHeight
            except AttributeError:
                rh = self._rowHeight = self.GetDefaultRowSize()
            if val != rh:
                self._rowHeight = val
                self.SetDefaultRowSize(val, True)
                self.ForceRefresh()
                # Persist the new size:
                self._setUserSetting("RowSize", val)
        else:
            self._properties["RowHeight"] = val

    @property
    def RowLabels(self):
        """List of the row labels.  (list)"""
        return self._rowLabels

    @RowLabels.setter
    def RowLabels(self, val):
        self._rowLabels = val
        self.fillGrid()

    @property
    def RowLabelWidth(self):
        """
        Width of the label on the left side of the rows. This only changes the grid if ShowRowLabels
        is True.  (int)
        """
        try:
            v = self._rowLabelWidth
        except AttributeError:
            v = self._rowLabelWidth = self.GetDefaultRowLabelSize()
        return v

    @RowLabelWidth.setter
    def RowLabelWidth(self, val):
        if self._constructed():
            self._rowLabelWidth = val
            if self.ShowRowLabels:
                self.SetRowLabelSize(val)
        else:
            self._properties["RowLabelWidth"] = val

    @property
    def SameSizeRows(self):
        """Is every row the same height?  (bool)"""
        return self._sameSizeRows

    @SameSizeRows.setter
    def SameSizeRows(self, val):
        self._sameSizeRows = bool(val)

    @property
    def SaveRestoreDataSet(self):
        """
        Specifies whether the DataSet is persisted to preferences (bool).

        This allows you to build a grid to capture user input of some form, and instead of saving
        the row and field values to a database, to save the entire dataset to a single key in the
        prefs table.

        Use this sparingly for grids that won't grow too large.

        Default: False.
        """
        return getattr(self, "_saveRestoreDataSet", False)

    @SaveRestoreDataSet.setter
    def SaveRestoreDataSet(self, val):
        self._saveRestoreDataSet = bool(val)

    @property
    def Searchable(self):
        """
        Specifies whether the columns can be searched.  (bool)

        If True, columns that have their Searchable properties set to True will be searchable.

        Default: True
        """
        return self._searchable

    @Searchable.setter
    def Searchable(self, val):
        self._searchable = bool(val)

    @property
    def SearchDelay(self):
        """
        Specifies the delay before incrementeal searching begins.  (int or None)

        As the user types, the search string is modified. If the time between keystrokes exceeds
        SearchDelay (milliseconds), the search will run and the search string will be cleared.

        If SearchDelay is set to None (the default), Application.SearchDelay will be used.
        """
        return self._searchDelay

    @SearchDelay.setter
    def SearchDelay(self, val):
        self._searchDelay = val

    @property
    def Selection(self):
        """
        Returns either a list of row/column numbers if SelectionMode is set to either 'Row' or
        'Column'. If SelectionMode is 'Cell', returns a list of 2-tuples, where each 2-tuple
        represents a selected range of cells: the top-left and bottom-right coordinates for a given
        range. If only a single cell is selected, there will be only one 2-tuple in the list, with
        both values being the same. If a continuous block of cells is selected, there will be only
        one 2-tuple in the list, but the values will differ. If more than one discontinuous range is
        selected, there will be as many 2-tuples as there are range blocks.  (list)
        """
        ret = []
        sm = self._selectionMode
        tl = self.GetSelectionBlockTopLeft()
        br = self.GetSelectionBlockBottomRight()
        cols = self.GetSelectedCols()
        rows = self.GetSelectedRows()
        cells = self.GetSelectedCells()

        if sm == "Row":
            ret = rows
            # See if anything is returned by the block functions
            if tl and br:
                for tlz, brz in zip(tl, br):
                    r1 = tlz[0]
                    r2 = brz[0]
                    ret += list(range(r1, r2 + 1))
            if not ret:
                # Only a single cell selected
                ret = [self.GetGridCursorRow()]

        elif sm == "Col":
            ret = cols
            # See if anything is returned by the block functions
            if tl and br:
                for tlz, brz in zip(tl, br):
                    c1 = tlz[1]
                    c2 = brz[1]
                    ret += list(range(c1, c2 + 1))
            if not ret:
                # Only a single cell selected
                ret = [self.GetGridCursorCol()]

        else:
            # Cell selection mode
            if tl and br:
                ret = list(zip(tl, br))
            # Add any selected rows
            if rows:
                ret += self._calcRanges(rows, "Rows")
            # Add any selected columns
            if cols:
                ret += self._calcRanges(cols, "Cols")
            # Add any selected cells
            if cells:
                ret += [(val, val) for val in cells]

            if not ret:
                cell = (self.GetGridCursorRow(), self.GetGridCursorCol())
                ret = [(cell, cell)]
        ret.sort()
        return ret

    @property
    def SelectionBackColor(self):
        """BackColor of selected cells  (str or RGB tuple)"""
        return self._selectionBackColor

    @SelectionBackColor.setter
    def SelectionBackColor(self, val):
        if self._constructed():
            self._selectionBackColor = val
            if isinstance(val, str):
                val = color_tools.colorTupleFromName(val)
            self.SetSelectionBackground(val)
        else:
            self._properties["SelectionBackColor"] = val

    @property
    def SelectionForeColor(self):
        """ForeColor of selected cells  (str or RGB tuple)"""
        return self._selectionForeColor

    @SelectionForeColor.setter
    def SelectionForeColor(self, val):
        if self._constructed():
            self._selectionForeColor = val
            if isinstance(val, str):
                val = color_tools.colorTupleFromName(val)
            self.SetSelectionForeground(val)
        else:
            self._properties["SelectionForeColor"] = val

    @property
    def SelectionMode(self):
        """Determines how the grid displays selections.  (str)

        Options are:
            Cells/Plain/None - no row/col highlighting  (default)
            Row - the row of the selected cell is highlighted
            Column - the column of the selected cell is highlighted

        The highlight color is determined by the SelectionBackColor and SelectionForeColor
        properties.
        """
        return self._selectionMode

    @SelectionMode.setter
    def SelectionMode(self, val):
        if self._constructed():
            orig = self._selectionMode
            val2 = val.lower().strip()[:2]
            if val2 == "ro":
                try:
                    self.SetSelectionMode(wx.grid.Grid.GridSelectRows)
                    self._selectionMode = "Row"
                except (AttributeError, wx.PyAssertionError):
                    ui.setAfter(self, "SelectionMode", val)
            elif val2 == "co":
                try:
                    self.SetSelectionMode(wx.grid.Grid.GridSelectColumns)
                    self._selectionMode = "Col"
                except (AttributeError, wx.PyAssertionError):
                    ui.setAfter(self, "SelectionMode", val)
            else:
                try:
                    self.SetSelectionMode(wx.grid.Grid.GridSelectCells)
                    self._selectionMode = "Cell"
                except (AttributeError, wx.PyAssertionError):
                    ui.setAfter(self, "SelectionMode", val)
            if self._selectionMode != orig:
                self._checkSelectionType()
        else:
            self._properties["SelectionMode"] = val

    @property
    def ShowCellBorders(self):
        """Are borders around cells shown?  (bool)"""
        return self.GridLinesEnabled()

    @ShowCellBorders.setter
    def ShowCellBorders(self, val):
        if self._constructed():
            self.EnableGridLines(val)
        else:
            self._properties["ShowCellBorders"] = val

    @property
    def ShowColumnLabels(self):
        """
        Are column labels shown?  (bool)

        DEPRECATED: Use ShowHeaders instead.
        """
        warnings.warn(
            _("ShowColumnLabels is deprecated. Use ShowHeaders instead"),
            DeprecationWarning,
        )
        return self._showHeaders

    @ShowColumnLabels.setter
    def ShowColumnLabels(self, val):
        if self._constructed():
            warnings.warn(
                _("ShowColumnLabels is deprecated. Use ShowHeaders instead"),
                DeprecationWarning,
            )
            self._showHeaders = val
            if val:
                self.SetColLabelSize(self.HeaderHeight)
            else:
                self.SetColLabelSize(0)
        else:
            self._properties["ShowColumnLabels"] = val

    @property
    def ShowHeaders(self):
        """Are grid column headers shown?  (bool)"""
        return self._showHeaders

    @ShowHeaders.setter
    def ShowHeaders(self, val):
        if self._constructed():
            self._showHeaders = val
            if val:
                hh = getattr(self, "_lastPositiveHeaderHeight", None)
                if not hh:
                    # Use current if already positive:
                    hh = self.GetColLabelSize()
                if not hh:
                    # Set a reasonable default (should never happen)
                    hh = 32
                self.SetColLabelSize(hh)
            else:
                curr = self.GetColLabelSize()
                if curr > 0:
                    self._lastPositiveHeaderHeight = curr
                self.SetColLabelSize(0)
        else:
            self._properties["ShowHeaders"] = val

    @property
    def ShowRowLabels(self):
        """Are row labels shown?  (bool)"""
        return self._showRowLabels

    @ShowRowLabels.setter
    def ShowRowLabels(self, val):
        if self._constructed():
            self._showRowLabels = val
            if val:
                self.SetRowLabelSize(self.RowLabelWidth)
            else:
                self.SetRowLabelSize(0)
        else:
            self._properties["ShowRowLabels"] = val

    @property
    def Sortable(self):
        """
        Specifies whether the columns can be sorted. If True, and if the column's Sortable property
        is True, the column will be sortable. Default: True  (bool)
        """
        return self._sortable

    @Sortable.setter
    def Sortable(self, val):
        self._sortable = bool(val)

    @property
    def SortIndicatorColor(self):
        """
        Color of the icon is that identifies a column as being sorted.  Default="yellow".  (str or
        color tuple)
        """
        return self._sortIndicatorColor

    @SortIndicatorColor.setter
    def SortIndicatorColor(self, val):
        if self._constructed():
            self._sortIndicatorColor = val
        else:
            self._properties["SortIndicatorColor"] = val

    @property
    def SortIndicatorSize(self):
        """
        Determines how large the icon is that identifies a column as being sorted. Default=8. (int)
        """
        return self._sortIndicatorSize

    @SortIndicatorSize.setter
    def SortIndicatorSize(self, val):
        if self._constructed():
            self._sortIndicatorSize = val
        else:
            self._properties["SortIndicatorSize"] = val

    @property
    def _Table(self):
        """Reference to the internal table class  (dGridDataTable)"""
        ## pkm: we can't call this until after the grid is fully constructed. Need to fix.
        try:
            tbl = self.GetTable()
        except TypeError:
            tbl = None
        if not tbl:
            try:
                tbl = dGridDataTable(self)
                self.SetTable(tbl, True)
            except TypeError:
                tbl = None
        return tbl

    @_Table.setter
    def _Table(self, tbl):
        if self._constructed():
            self.SetTable(tbl, True)
        else:
            self._properties["Table"] = value

    @property
    def TabNavigates(self):
        """
        Specifies whether Tab navigates to the next control (True, the default), or if Tab moves to
        the next column in the grid (False).
        """
        return getattr(self, "_tabNavigates", True)

    @TabNavigates.setter
    def TabNavigates(self, val):
        self._tabNavigates = bool(val)

    @property
    def VerticalHeaders(self):
        """
        When True, the column headers' Captions are written vertically.  Default=False.  (bool)
        """
        return self._verticalHeaders

    @VerticalHeaders.setter
    def VerticalHeaders(self, val):
        if self._constructed():
            if val != self._verticalHeaders:
                self._verticalHeaders = val
                self.refresh()
                if self.AutoAdjustHeaderHeight:
                    ui.callAfter(self.fitHeaderHeight)
        else:
            self._properties["VerticalHeaders"] = val

    @property
    def VerticalScrolling(self):
        """Is scrolling enabled in the vertical direction?  (bool)"""
        return self.GetScrollPixelsPerUnit()[1] > 0

    @VerticalScrolling.setter
    def VerticalScrolling(self, val):
        if self._constructed():
            if val:
                self.SetScrollRate(self.GetScrollPixelsPerUnit()[0], 20)
            else:
                self.SetScrollRate(self.GetScrollPixelsPerUnit()[0], 0)
            self.refresh()
        else:
            self._properties["VerticalScrolling"] = val

    Children = Columns

    # Dynamic Property Declarations
    DynamicActivateEditorOnSelect = makeDynamicProperty(ActivateEditorOnSelect)
    DynamicAlternateRowColoring = makeDynamicProperty(AlternateRowColoring)
    DynamicCellHighlightWidth = makeDynamicProperty(CellHighlightWidth)
    DynamicColumnClass = makeDynamicProperty(ColumnClass)
    DynamicColumnCount = makeDynamicProperty(ColumnCount)
    DynamicCurrentColumn = makeDynamicProperty(CurrentColumn)
    DynamicCurrentField = makeDynamicProperty(CurrentField)
    DynamicCurrentRow = makeDynamicProperty(CurrentRow)
    DynamicDataSet = makeDynamicProperty(DataSet)
    DynamicDataSource = makeDynamicProperty(DataSource)
    DynamicEditable = makeDynamicProperty(Editable)
    DynamicHeaderBackColor = makeDynamicProperty(HeaderBackColor)
    DynamicHeaderForeColor = makeDynamicProperty(HeaderForeColor)
    DynamicHeaderHeight = makeDynamicProperty(HeaderHeight)
    DynamicHeaderHorizontalAlignment = makeDynamicProperty(HeaderHorizontalAlignment)
    DynamicHeaderVerticalAlignment = makeDynamicProperty(HeaderVerticalAlignment)
    DynamicHorizontalScrolling = makeDynamicProperty(HorizontalScrolling)
    DynamicRowColorEven = makeDynamicProperty(RowColorEven)
    DynamicRowColorOdd = makeDynamicProperty(RowColorOdd)
    DynamicRowHeight = makeDynamicProperty(RowHeight)
    DynamicRowLabelWidth = makeDynamicProperty(RowLabelWidth)
    DynamicRowLabels = makeDynamicProperty(RowLabels)
    DynamicSameSizeRows = makeDynamicProperty(SameSizeRows)
    DynamicSearchDelay = makeDynamicProperty(SearchDelay)
    DynamicSearchable = makeDynamicProperty(Searchable)
    DynamicSelectionBackColor = makeDynamicProperty(SelectionBackColor)
    DynamicSelectionForeColor = makeDynamicProperty(SelectionForeColor)
    DynamicSelectionMode = makeDynamicProperty(SelectionMode)
    DynamicShowCellBorders = makeDynamicProperty(ShowCellBorders)
    DynamicShowColumnLabels = makeDynamicProperty(ShowColumnLabels)
    DynamicShowHeaders = makeDynamicProperty(ShowHeaders)
    DynamicShowRowLabels = makeDynamicProperty(ShowRowLabels)
    DynamicSortable = makeDynamicProperty(Sortable)
    DynamicTabNavigates = makeDynamicProperty(TabNavigates)
    DynamicVerticalHeaders = makeDynamicProperty(VerticalHeaders)
    DynamicVerticalScrolling = makeDynamicProperty(VerticalScrolling)

    ##----------------------------------------------------------##
    ##                 end: property definitions                    ##
    ##----------------------------------------------------------##


ui.dGridDataTable = dGridDataTable
ui.GridListEditor = GridListEditor
ui.dColumn = dColumn
ui.dGrid = dGrid


class _dGrid_test(dGrid):
    def initProperties(self):
        thisYear = datetime.datetime.now().year
        ds = [
            {"name": "Ed Leafe", "age": thisYear - 1957, "coder": True, "color": "cornsilk"},
            {"name": "Paul McNett", "age": thisYear - 1969, "coder": True, "color": "wheat"},
            {"name": "Ted Roche", "age": thisYear - 1958, "coder": True, "color": "goldenrod"},
            {"name": "Derek Jeter", "age": thisYear - 1974, "coder": False, "color": "white"},
            {"name": "Halle Berry", "age": thisYear - 1966, "coder": False, "color": "orange"},
            {
                "name": "Steve Wozniak",
                "age": thisYear - 1950,
                "coder": True,
                "color": "yellow",
            },
            {
                "name": "LeBron James",
                "age": thisYear - 1984,
                "coder": False,
                "color": "gold",
            },
            {
                "name": "Barack Obama",
                "age": thisYear - 1961,
                "coder": False,
                "color": "red",
            },
        ]
        self.DataSet = ds

        self.TabNavigates = False
        self.Width = 360
        self.Height = 150
        self.Editable = False
        self.AlternateRowColoring = True
        self.Sortable = True
        self.Searchable = True

    def afterInit(self):
        super().afterInit()

        self.addColumn(
            Name="Geek",
            DataField="coder",
            Caption="Geek?",
            Order=10,
            DataType="bool",
            Width=60,
            Sortable=True,
            Searchable=False,
            Editable=True,
            HeaderFontBold=False,
            HorizontalAlignment="Center",
            VerticalAlignment="Center",
            Resizable=False,
        )

        col = dColumn(
            self,
            Name="Person",
            Order=20,
            DataField="name",
            DataType="string",
            Width=200,
            Caption="Celebrity Name",
            Sortable=True,
            Searchable=True,
            Editable=True,
            Expand=False,
        )
        self.addColumn(col)

        col.HeaderFontItalic = True
        col.HeaderBackColor = "peachpuff"
        col.HeaderVerticalAlignment = "Top"
        col.HeaderHorizontalAlignment = "Left"

        # Let's make a custom editor for the name
        class ColoredText(dTextBox):
            def initProperties(self):
                self.ForeColor = "blue"
                self.FontItalic = True
                self.FontSize = 24

            def onKeyChar(self, evt):
                self.ForeColor = color_tools.randomColor()
                self.FontItalic = not self.FontItalic

        # Since we're using a big font, set a minimum height for the editor
        col.CustomEditorClass = ui.makeGridEditor(ColoredText, minHeight=40)

        self.addColumn(
            Name="Age",
            Order=30,
            DataField="age",
            DataType="int",
            Width=40,
            Caption="Age",
            Sortable=True,
            Searchable=True,
            Editable=True,
        )

        col = dColumn(
            self,
            Name="Color",
            Order=40,
            DataField="color",
            DataType="string",
            Width=40,
            Caption="Favorite Color",
            Sortable=True,
            Searchable=True,
            Editable=True,
            Expand=False,
        )
        self.addColumn(col)

        col.ListEditorChoices = color_tools.colors
        col.CustomEditorClass = col.listEditorClass

        col.HeaderVerticalAlignment = "Bottom"
        col.HeaderHorizontalAlignment = "Right"
        col.HeaderForeColor = "brown"

    def onScrollLineUp(self, evt):
        print("LINE UP orientation =", evt.orientation, " scrollpos =", evt.scrollpos)

    def onScrollLineDown(self, evt):
        print("LINE DOWN orientation =", evt.orientation, " scrollpos =", evt.scrollpos)

    def onScrollPageUp(self, evt):
        print("PAGE UP orientation =", evt.orientation, " scrollpos =", evt.scrollpos)

    def onScrollPageDown(self, evt):
        print("PAGE DOWN orientation =", evt.orientation, " scrollpos =", evt.scrollpos)

    def onScrollThumbDrag(self, evt):
        print("DRAG orientation =", evt.orientation, " scrollpos =", evt.scrollpos)

    def onScrollThumbRelease(self, evt):
        print(
            "THUMB RELEASE orientation =",
            evt.orientation,
            " scrollpos =",
            evt.scrollpos,
        )


if __name__ == "__main__":
    from ..application import dApp

    class TestForm(dForm):
        def afterInit(self):
            self.BackColor = "khaki"
            g = self.grid = _dGrid_test(self, RegID="sampleGrid")
            self.Sizer.append(g, 1, "x", border=0, borderSides="all")
            self.Sizer.appendSpacer(10)
            gsz = dGridSizer(HGap=50)

            chk = dCheckBox(
                self,
                Caption="Allow Editing?",
                RegID="gridEdit",
                DataSource=self.grid,
                DataField="Editable",
            )
            chk.update()
            gsz.append(chk, row=0, col=0)

            chk = dCheckBox(
                self,
                Caption="Show Headers",
                RegID="showHeaders",
                DataSource=self.grid,
                DataField="ShowHeaders",
            )
            gsz.append(chk, row=1, col=0)
            chk.update()

            chk = dCheckBox(
                self,
                Caption="Allow Multiple Selection",
                RegID="multiSelect",
                DataSource=self.grid,
                DataField="MultipleSelection",
            )
            chk.update()
            gsz.append(chk, row=2, col=0)

            chk = dCheckBox(
                self,
                Caption="Sortable?",
                RegID="sortable",
                DataSource=self.grid,
                DataField="Sortable",
            )
            chk.update()
            gsz.append(chk, row=3, col=0)

            chk = dCheckBox(
                self,
                Caption="Vertical Headers",
                RegID="verticalHeaders",
                DataSource=self.grid,
                DataField="VerticalHeaders",
            )
            chk.update()
            gsz.append(chk, row=4, col=0)

            chk = dCheckBox(
                self,
                Caption="Auto-adjust Header Height",
                RegID="autoAdjust",
                DataSource=self.grid,
                DataField="AutoAdjustHeaderHeight",
            )
            chk.update()
            gsz.append(chk, row=5, col=0)

            radSelect = dRadioList(
                self,
                Choices=["Row", "Col", "Cell"],
                ValueMode="string",
                Caption="Sel Mode",
                BackColor=self.BackColor,
                DataSource=self.grid,
                DataField="SelectionMode",
                RegID="radSelect",
            )
            radSelect.refresh()
            gsz.append(radSelect, row=0, col=1, rowSpan=3)

            def setVisible(evt):
                col = g.getColByDataField("name")
                but = evt.EventObject
                col.Visible = not col.Visible
                if col.Visible:
                    but.Caption = "Make Celebrity Invisible"
                else:
                    but.Caption = "Make Celebrity Visible"

            butVisible = dButton(self, Caption="Toggle Celebrity Visibility", OnHit=setVisible)
            gsz.append(butVisible, row=6, col=0)

            self.Sizer.append(gsz, halign="Center", border=10)
            gsz.setColExpand(True, 1)
            self.layout()

            self.fitToSizer(20, 20)

    app = dApp(MainFormClass=TestForm)
    app.setup()
    app.MainForm.radSelect.setFocus()
    app.start()
