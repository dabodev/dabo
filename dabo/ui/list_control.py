# -*- coding: utf-8 -*-
import wx
import wx.lib.mixins.listctrl as ListMixin

from .. import color_tools, events, settings, ui
from ..lib.utils import ustr
from ..localization import _
from . import dControlItemMixin, makeDynamicProperty

dabo_module = settings.get_dabo_package()


class _ListColumnAccessor(object):
    """
    These aren't the actual columns that appear in the list control; rather,
    they provide a way to interact with the underlying list items in a more
    straightforward manner.
    """

    def __init__(self, listcontrol, *args, **kwargs):
        self.listcontrol = listcontrol
        super().__init__(*args, **kwargs)

    def __dabo_getitem__(self, val):
        ret = self.listcontrol.GetColumn(val)
        ret._dabo_listcontrol = self.listcontrol
        ret._dabo_column_number = val

        # NOTE: We need to define the property this way (not using decorators),
        # as the property is not part of this class, but of the wx.ListItem
        def _getCaption(self):
            """Caption for the column.  (str)"""
            return self._dabo_listcontrol.getCaptionForColumn(self._dabo_column_number)

        def _setCaption(self, val):
            self._dabo_listcontrol.setCaptionForColumn(self._dabo_column_number, val)

        Caption = property(_getCaption, _setCaption)
        setattr(ret.__class__, "Caption", Caption)

        return ret

    def __getitem__(self, val):
        return self.__dabo_getitem__(val)

    def __getslice__(self, start, end):
        return [self.__dabo_getitem__(col) for col in range(start, end)]


class dListControl(dControlItemMixin, ListMixin.ListCtrlAutoWidthMixin, wx.ListCtrl):
    """
    Creates a list control, which is a flexible, virtual list box.

    The List Control is ideal for visually dealing with data sets where each
    'row' is a unit, where it doesn't make sense to deal with individual
    elements inside of the row. If you need to be able to work with individual
    elements, you should use a dGrid.
    """

    def __init__(self, parent, properties=None, attProperties=None, style=None, *args, **kwargs):
        self._baseClass = dListControl

        self._lastSelectedIndex = None
        self._hitIndex = None
        self._valCol = 0
        self._sortOrder = 0
        self._sortColumn = -1
        self._sortOnHeaderClick = True
        # Do we auto-convert all entries to strings?
        self._autoConvertToString = True
        # Do we grow the ExpandColumn to fill the width of the control?
        self._expandToFit = True
        # Which column expands to fill the width of the control?
        self._expandColumn = "LAST"

        try:
            style = style | wx.LC_REPORT
        except TypeError:
            style = wx.LC_REPORT
        preClass = wx.ListCtrl
        dControlItemMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            style=style,
            *args,
            **kwargs,
        )
        ListMixin.ListCtrlAutoWidthMixin.__init__(self)
        # Dictionary for tracking images by key value
        self.__imageList = {}
        # Need to set this after the superclass call in order to override the default for
        # a control with items
        self.SortFunction = self._listControlSort
        # Set the default sorting column to 0 after everything is instantiated
        ui.setAfter(self, "SortColumn", 0)
        self._columnAccessor = _ListColumnAccessor(self)

    def _initEvents(self):
        super()._initEvents()
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.__onSelection)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.__onDeselection)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.__onActivation)
        self.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.__onFocus)
        self.Bind(wx.EVT_LIST_KEY_DOWN, self.__onWxKeyDown)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.__onWxHeaderClick)
        self.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.__onWxHeaderRightClick)
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self.__onWxColumnResize)

        self.bindEvent(events.ListHeaderMouseLeftClick, self.__onHeaderMouseLeftClick)
        self.bindEvent(events.ListHeaderMouseRightClick, self.__onHeaderMouseRightClick)
        self.bindEvent(events.ListColumnResize, self.__onColumnResize)

    def _getInitPropertiesList(self):
        return super()._getInitPropertiesList() + ("ColumnsAlignment",)

    def _doResize(self):
        if self and self.ExpandToFit:
            ListMixin.ListCtrlAutoWidthMixin._doResize(self)

    def addColumn(self, caption, align="Left", width=-1):
        """Add a column with the selected caption."""
        self.insertColumn(self.GetColumnCount(), caption, align, width)

    def insertColumn(self, pos, caption, align="Left", width=-1):
        """
        Inserts a column at the specified position
        with the selected caption.
        """
        try:
            align = self.ColumnsAlignment[pos]
        except IndexError:
            pass
        self.InsertColumn(pos, caption, self._getWxAlign(align), width)

    def removeColumn(self, pos=None):
        """
        Removes the specified column, or the last column if
        no column number is passed.
        """
        if pos is None:
            pos = self.GetColumnCount() - 1
        self.DeleteColumn(pos)

    def _getCurrentData(self):
        ds = []
        for row in range(self.RowCount):
            rr = []
            for col in range(self.ColumnCount):
                rr.append(self.GetItem(row, col).GetText())
            ds.append(rr)
        return ds

    def _getWxAlign(self, align):
        try:
            wxAlign = {
                "l": wx.LIST_FORMAT_LEFT,
                "c": wx.LIST_FORMAT_CENTRE,
                "r": wx.LIST_FORMAT_RIGHT,
            }[align[:1].lower()]
        except:
            wxAlign = wx.LIST_FORMAT_LEFT
        return wxAlign

    def setColumns(self, colList):
        """
        Accepts a list/tuple of column headings, removes any existing columns,
        and creates new columns, one for each element in the list. The current
        display settings and data is preserved as much as possible: setting more
        columns will result in empty columns, and setting fewer columns will
        truncate the data.
        """
        self.lockDisplay()
        ds = self._getCurrentData()
        wds = [self.getColumnWidth(col) for col in range(self.ColumnCount)]
        expandCol = self.ExpandColumn
        self.clear()
        self.DeleteAllColumns()
        for col in colList:
            self.addColumn(col)
        self.appendRows(ds)
        dummy = [self.setColumnWidth(col, wd) for col, wd in enumerate(wds)]
        self.ExpandColumn = expandCol
        self.unlockDisplay()

    def getCaptionForColumn(self, colnum):
        """Convenience method for getting the caption for a given column number."""
        captions = [self.GetColumn(ii).GetText() for ii in range(self.ColumnCount)]
        return captions[colnum]

    def setCaptionForColumn(self, colnum, val):
        """Convenience method for setting the caption for a given column number."""
        captions = [self.GetColumn(ii).GetText() for ii in range(self.ColumnCount)]
        captions[colnum] = val
        self.setColumns(captions)

    def select(self, row):
        """
        Selects the specified row. In a MultipleSelect control, any
        other selected rows remain selected.
        """
        if row < self.RowCount:
            self.SetItemState(row, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        else:
            dabo_module.error("An attempt was made to select a non-existent row")

    def selectOnly(self, row):
        """
        Selects the specified row. In a MultipleSelect control, any
        other selected rows are de-selected first.
        """
        if self.MultipleSelect:
            self.unselectAll()
        self.SetItemState(row, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

    def unselect(self, row):
        """
        De-selects the specified row. In a MultipleSelect control, any
        other selected rows remain selected.
        """
        self.SetItemState(row, 0, wx.LIST_STATE_SELECTED)

    def selectAll(self):
        """
        Selects all rows in a MultipleSelect control, or generates a
        warning if the control is not set to MultipleSelect.
        """
        if self.MultipleSelect:
            for row in range(self.RowCount):
                self.select(row)
        else:
            dabo_module.error(
                "'selectAll()' may only be called on List Controls that designated as "
                "MultipleSelect"
            )

    def unselectAll(self):
        """De-selects all rows."""
        for row in range(self.RowCount):
            self.unselect(row)

    # Override the default selectNone to something appropriate for this control.
    selectNone = unselectAll

    def getColumnWidth(self, col):
        return self.GetColumnWidth(col)

    def setColumnWidth(self, col, wd):
        """Sets the width of the specified column."""
        if isinstance(wd, str):
            self.autoSizeColumn(col)
        else:
            self.SetColumnWidth(col, wd)
        ui.callAfterInterval(100, self._doResize)

    def autoSizeColumn(self, col):
        """Auto-sizes the specified column."""
        self.lockDisplay()
        self.SetColumnWidth(col, wx.LIST_AUTOSIZE)
        wd = self.GetColumnWidth(col)
        self.SetColumnWidth(col, wx.LIST_AUTOSIZE_USEHEADER)
        if self.GetColumnWidth(col) < wd:
            self.SetColumnWidth(col, wd)
        self.unlockDisplay()
        ui.callAfterInterval(100, self._doResize)

    def autoSizeColumns(self, colList=None):
        """Auto-sizes all the columns."""
        if colList is None:
            colList = range(self.ColumnCount)
        for col in colList:
            self.autoSizeColumn(col)

    def append(self, tx, col=0, row=None):
        """
        Appends a row with the associated text in the specified column.
        If the value for tx is a list/tuple, the values will be set in the columns
        starting with the passed value. If either case results in an attempt to
        add to a non-existent column, it will be ignored.
        """
        insert = False
        new_item = None

        if row is None:
            row = self.RowCount
            insert = True
        if isinstance(tx, (list, tuple)):
            if insert:
                new_item = self.InsertItem(row, "")
            currCol = col
            for itm in tx:
                new_item = self.append(itm, currCol, row)
                currCol += 1
        else:
            if col < self.ColumnCount:
                if not isinstance(tx, str) and self.AutoConvertToString:
                    tx = "%s" % tx
                if insert:
                    new_item = self.InsertItem(row, tx)
                else:
                    new_item = self.SetItem(row, col, tx)
            else:
                # should we raise an error? Add the column automatically?
                pass
        return new_item

    def appendRows(self, seq, col=0):
        """
        Accepts a list/tuple of data. Each element in the sequence
        will be another row in the control. If the data is plain text, it
        will be added in the specified column. If the data is also a
        list/tuple, it will be appended into columns beginning with the
        specified column.
        """
        for itm in seq:
            self.append(itm, col=col)

    def insert(self, tx, row=0, col=0):
        """
        Inserts the item at the specified row, or at the beginning if no
        row is specified. Item is inserted at the specified column, as in self.append()
        """
        self.InsertItem(row, "")
        self.append(tx, col, row)

    def insertRows(self, seq, row=0, col=0):
        """
        Accepts a list/tuple of data. Each element in the sequence
        will be another row in the control. If the data is plain text, it
        will be inserted in the specified column at the specified row.
        If the data is also a list/tuple, it will be inserted into columns
        beginning with the specified column.
        """
        for itm in seq:
            self.insert(itm, row=row, col=col)

    def removeRow(self, row):
        """
        Deletes the specified row if it exists, or generates a warning
        if it does not.
        """
        if row < self.RowCount:
            self.DeleteItem(row)
            self._restoreRowSelection(row)
        else:
            dabo_module.error("An attempt was made to remove a non-existent row")

    def _restoreRowSelection(self, row):
        """
        Restores selection of last selected row, helpful in list item
        manipulation conditions, e.g. removing list items.
        """
        if self._lastSelectedIndex:
            rowcnt = self.RowCount
            if rowcnt == 0 or self.MultipleSelect:
                self._lastSelectedIndex = None
            else:
                if row < rowcnt:
                    self.select(row)
                else:
                    self.select(rowcnt - 1)

    def clear(self):
        """Remove all the rows in the control."""
        self.DeleteAllItems()
        self._lastSelectedIndex = None

    # Need to alias this to work like other list controls.
    removeAll = clear

    def _GetString(self, idx=None, col=None):
        """
        Since the wx List Control doesn't have a direct GetString() method,
        which our code for dControlItemMixin expects, this 'fakes' it.
        """
        if idx is None:
            idx = self.LastSelectedIndex
        if col is None:
            col = self.ValueColumn
        return self.GetItem(idx, col).GetText()

    def setItemData(self, item, data):
        """Associate some data with the item."""
        return self.SetItemData(item, data)

    def getItemData(self, item):
        """Retrieve the data associated with the item."""
        return self.GetItemData(item)

    # Image-handling function
    def addImage(self, img, key=None):
        """
        Adds the passed image to the control's ImageList, and maintains
        a reference to it that is retrievable via the key value.
        """
        if key is None:
            key = ustr(img)
        if isinstance(img, str):
            img = ui.strToBmp(img)
        il = self.GetImageList(wx.IMAGE_LIST_NORMAL)
        if not il:
            il = wx.ImageList(16, 16, initialCount=0)
            self.AssignImageList(il, wx.IMAGE_LIST_NORMAL)
        idx = il.Add(img)
        self.__imageList[key] = idx

    def setItemImg(self, itm, imgKey):
        """
        Sets the specified item's image to the image corresponding
        to the specified key. May also optionally pass the index of the
        image in the ImageList rather than the key.
        """
        if isinstance(imgKey, int):
            imgIdx = imgKey
        else:
            imgIdx = self.__imageList[imgKey]
        self.SetItemImage(itm, imgIdx, imgIdx)
        self.GetItem(itm).SetImage(imgIdx)

    def getItemImg(self, itm):
        """
        Returns the index of the specified item's image in the
        current image list, or -1 if no image is set for the item.
        """
        ret = self.GetItem(itm).GetImage()
        return ret

    def getItemBackColor(self, itm):
        return self.GetItemBackgroundColour(itm)

    def setItemBackColor(self, itm, val):
        if isinstance(val, str):
            color = color_tools.colorTupleFromName(val)
        else:
            color = val
        self.SetItemBackgroundColour(itm, color)

    def getItemForeColor(self, itm):
        return self.GetItemTextColour(itm)

    def setItemForeColor(self, itm, val):
        if isinstance(val, str):
            color = color_tools.colorTupleFromName(val)
        else:
            color = val
        self.SetItemTextColour(itm, color)

    def __onActivation(self, evt):
        self._hitIndex = evt.GetIndex()
        # Call the default Hit code
        self._onWxHit(evt)

    def __onFocus(self, evt):
        self.raiseEvent(events.GotFocus, evt)

    def __onSelection(self, evt):
        self._lastSelectedIndex = evt.GetIndex()
        self.raiseEvent(events.ListSelection, evt)

    def __onDeselection(self, evt):
        self.raiseEvent(events.ListDeselection, evt)

    def __onWxKeyDown(self, evt):
        self.raiseEvent(events.KeyDown, evt)

    def __onWxHeaderClick(self, evt):
        self.raiseEvent(events.ListHeaderMouseLeftClick, evt)

    def __onWxHeaderRightClick(self, evt):
        self.raiseEvent(events.ListHeaderMouseRightClick, evt)

    def __onWxColumnResize(self, evt):
        self.raiseEvent(events.ListColumnResize, evt)

    def __onHeaderMouseLeftClick(self, evt):
        if self.SortOnHeaderClick:
            if self._sortColumn != evt.col:
                self._sortColumn = evt.col
                self._sortOrder = 0
            else:
                self._sortOrder += 1
            self.sort()

    def __onHeaderMouseRightClick(self, evt):
        pass

    def __onColumnResize(self, evt):
        pass

    def _listControlSort(self, x, y):
        # Default to standard Python comparison
        return (x > y) - (x < y)

    def sort(self, sortFunction=None):
        # Sorts the control based on the current sort column.
        if sortFunction is None:
            sortFunction = self.SortFunction
        itemData = self._getItemDataDict()
        self._fillItemData(self._sortColumn)
        self.SortItems(sortFunction)
        self._restoreItemData(itemData)

    def _getItemDataDict(self):
        """Return a dict with the items as keys, and the ItemData as values."""
        ret = {}
        for row in range(self.RowCount):
            ret[row] = self.GetItemData(row)
        return ret

    def _fillItemData(self, col):
        """
        Sets the Item Data for each row to be the value corresponding to the order
        for each column.
        """
        data = []
        # Don't allow the default -1 for sort column.
        col = max(0, self._sortColumn)
        for row in range(self.RowCount):
            try:
                itm = self.GetItem(row, col)
                data.append((itm.GetText(), row))
            except AttributeError:
                pass
        data.sort()
        if self._sortOrder % 2:
            # Odd number of sorts
            data.reverse()
        for pos, elem in enumerate(data):
            self.SetItemData(elem[1], pos)

    def _restoreItemData(self, dct):
        """After a sort, returns the original item data values."""
        for row, val in list(dct.items()):
            self.SetItemData(row, val)

    def _resetSize(self, col):
        # Called when a column was marked to expand, and then
        # changed to a normal column.
        cc = self.ColumnCount
        if isinstance(col, str):
            # Last column
            col = cc - 1
        if col < cc:
            self.autoSizeColumn(col)

    def SetSelection(self, index):
        """Wrapper for backend Select method."""
        if self.Count > index:
            self.Select(index)

    # Property definitions
    @property
    def AutoConvertToString(self):
        """
        When True (default), all non-string values are forced to strings. When False, attempting to
        use a non-string value will throw an error.  (bool)
        """
        return self._autoConvertToString

    @AutoConvertToString.setter
    def AutoConvertToString(self, val):
        if self._constructed():
            self._autoConvertToString = val
        else:
            self._properties["AutoConvertToString"] = val

    @property
    def Choices(self):
        """
        Since dListControl doesn't have the equivalent to 'Choices' as the other item controls do,
        this will return an empty list and print a warning message. (read-only) (list)
        """
        dabo_module.warn(_("'Choices' is not a valid property for a dListControl."))
        return []

    @property
    def ColumnCount(self):
        """Number of columns in the control  (int)"""
        return self.GetColumnCount()

    @ColumnCount.setter
    def ColumnCount(self, val):
        if self._constructed():
            cc = self.GetColumnCount()
            if val < cc:
                # Remove rightmost columns
                while val < self.GetColumnCount():
                    self.removeColumn()
            elif val > cc:
                while val > self.GetColumnCount():
                    self.addColumn(_("Column %s") % self.GetColumnCount())
        else:
            self._properties["ColumnCount"] = val

    @property
    def Columns(self):
        """Reference to the columns in the control. (read-only) (list)"""
        return self._columnAccessor

    @property
    def ColumnsAlignment(self):
        """
        Columns data alignment, the 'Left', 'Center' or 'Right' literals can be used or their
        abbreviations, e.g. ('l', 'c', 'r').  (tuple of str)
        """
        return getattr(self, "_columnsAlignment", ())

    @ColumnsAlignment.setter
    def ColumnsAlignment(self, align):
        self._columnsAlignment = align

    @property
    def ExpandColumn(self):
        """
        Designates the column to expand to fill the control when ExpandToFit is True.  Can either be
        an integer specifying the column number, or the string 'LAST' (default), which will expand
        the rightmost column.  (int or str)
        """
        return self._expandColumn

    @ExpandColumn.setter
    def ExpandColumn(self, val):
        if self._constructed():
            columnCount = self.ColumnCount
            if isinstance(val, str):
                val = val.upper().strip()
            else:
                if val >= columnCount and columnCount > 0:
                    raise IndexError(
                        _("Invalid column %s specified for dListControl.ExpandColumn") % val
                    )
            if self._expandColumn != val:
                if columnCount == 0:
                    self._expandColumn = val
                else:
                    if self._expandColumn:
                        self._resetSize(self._expandColumn)
                    self._expandColumn = val
                    if isinstance(val, int):
                        # Need to decrease by one, since the mixin uses a 1-based column numbering
                        self.setResizeColumn(val + 1)
                    else:
                        self.setResizeColumn(val)
        else:
            self._properties["ExpandColumn"] = val

    @property
    def ExpandToFit(self):
        """
        When True (default), the column designated by ExpandColumn expands to fill the width of the
        control.  (bool)
        """
        return self._expandToFit

    @ExpandToFit.setter
    def ExpandToFit(self, val):
        if self._constructed():
            self._expandToFit = val
        else:
            self._properties["ExpandToFit"] = val

    @property
    def HeaderVisible(self):
        """Specifies whether the header is shown or not."""
        return not self._hasWindowStyleFlag(wx.LC_NO_HEADER)

    @HeaderVisible.setter
    def HeaderVisible(self, val):
        if bool(val):
            self._delWindowStyleFlag(wx.LC_NO_HEADER)
        else:
            self._addWindowStyleFlag(wx.LC_NO_HEADER)
        self.refresh()

    @property
    def HitIndex(self):
        """Returns the index of the last hit item."""
        return self._hitIndex

    @property
    def HorizontalRules(self):
        """Specifies whether light rules are drawn between rows."""
        return self._hasWindowStyleFlag(wx.LC_HRULES)

    @HorizontalRules.setter
    def HorizontalRules(self, val):
        if bool(val):
            self._addWindowStyleFlag(wx.LC_HRULES)
        else:
            self._delWindowStyleFlag(wx.LC_HRULES)
        self.refresh()

    @property
    def LastSelectedIndex(self):
        """Returns the index of the last selected item."""
        return self._lastSelectedIndex

    @property
    def MultipleSelect(self):
        """Specifies whether multiple rows can be selected in the list."""
        return not self._hasWindowStyleFlag(wx.LC_SINGLE_SEL)

    @MultipleSelect.setter
    def MultipleSelect(self, val):
        if self._constructed():
            if bool(val):
                self._delWindowStyleFlag(wx.LC_SINGLE_SEL)
            else:
                self.unselectAll()
                self._addWindowStyleFlag(wx.LC_SINGLE_SEL)
            self.refresh()
        else:
            self._properties["MultipleSelect"] = val

    @property
    def RowCount(self):
        """Number of rows in the control (read-only).  (int)"""
        return self.GetItemCount()

    @property
    def SelectedIndices(self):
        """Returns a list of selected row indices.  (list of int)"""
        ret = []
        pos = -1
        while True:
            indx = self.GetNextItem(pos, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if indx == -1:
                break
            pos = indx
            ret.append(indx)
        return ret

    @SelectedIndices.setter
    def SelectedIndices(self, selList):
        if self._constructed():
            self.unselectAll()
            for id in selList:
                self.SetItemState(id, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        else:
            self._properties["SelectedIndices"] = selList

    @property
    def SortColumn(self):
        """Column to be sorted when sort() is called. Default=0  (int)"""
        return self._sortColumn

    @SortColumn.setter
    @ui.deadCheck
    def SortColumn(self, val):
        if self._constructed():
            self._sortColumn = val
        else:
            self._properties["SortColumn"] = val

    @property
    def SortOnHeaderClick(self):
        """
        When True (default), clicking a column header cycles the sorting on that column.  (bool)
        """
        return self._sortOnHeaderClick

    @SortOnHeaderClick.setter
    def SortOnHeaderClick(self, val):
        if self._constructed():
            self._sortOnHeaderClick = val
        else:
            self._properties["SortOnHeaderClick"] = val

    @property
    def Value(self):
        """Returns current value (str)"""
        if self.GetItemCount() == 0:
            return None
        item = None
        idx = self.LastSelectedIndex
        colcnt = self.ColumnCount
        vc = self.ValueColumn
        if idx is not None:
            if 0 <= vc <= colcnt:
                item = self.GetItem(idx, vc)
        if item is None:
            return None
        else:
            return item.GetText()

    @Value.setter
    def Value(self, val):
        if self._constructed():
            if isinstance(val, int):
                self.Select(val)
            elif isinstance(val, str):
                self.Select(self.FindItem(-1, val))
        else:
            self._properties["Value"] = val

    @property
    def Values(self):
        """Returns a list containing the Value of all selected rows  (list of str)"""
        ret = []
        indxs = self.SelectedIndices
        for idx in indxs:
            try:
                item = self.GetItem(idx, self.ValueColumn)
            except TypeError:
                item = None
            if item is not None:
                ret.append(item.GetText())
        return ret

    @property
    def ValueColumn(self):
        """The column whose text is reflected in Value (default=0).  (int)"""
        return self._valCol

    @ValueColumn.setter
    def ValueColumn(self, val):
        self._valCol = val

    @property
    def VerticalRules(self):
        """Specifies whether light rules are drawn between rows."""
        return self._hasWindowStyleFlag(wx.LC_VRULES)

    @VerticalRules.setter
    def VerticalRules(self, val):
        if bool(val):
            self._addWindowStyleFlag(wx.LC_VRULES)
        else:
            self._delWindowStyleFlag(wx.LC_VRULES)
        self.refresh()

    # Alias for RowCount
    Count = RowCount

    DynamicHeaderVisible = makeDynamicProperty(HeaderVisible)
    DynamicHorizontalRules = makeDynamicProperty(HorizontalRules)
    DynamicMultipleSelect = makeDynamicProperty(MultipleSelect)
    DynamicValue = makeDynamicProperty(Value)
    DynamicValueColumn = makeDynamicProperty(ValueColumn)
    DynamicVerticalRules = makeDynamicProperty(VerticalRules)


ui.dListControl = dListControl


class _dListControl_test(dListControl):
    def afterInit(self):
        self.setColumns(("Title", "Subtitle", "Release Year"))
        self.setColumnWidth(0, 150)
        self.setColumnWidth(1, 100)
        self.setColumnWidth(2, 200)
        self.append(("The Phantom Menace", "Episode 1", 1999))
        self.append(("Attack of the Clones", "Episode 2", 2002))
        self.append(("Revenge of the Sith", "Episode 3", 2005))
        self.append(("A New Hope", "Episode 4", 1977))
        self.append(("The Empire Strikes Back", "Episode 5", 1980))
        self.append(("Return of the Jedi", "Episode 6", 1983))

        self.Keys = [0, 1, 2, 3, 4, 5]

    def initProperties(self):
        self.MultipleSelect = True
        self.HorizontalRules = True
        self.VerticalRules = True
        # self.HeaderVisible = False

    def onHit(self, evt):
        print("KeyValue: ", self.KeyValue)
        print("PositionValue: ", self.PositionValue)
        print("StringValue: ", self.StringValue)
        print("Value: ", self.Value)

    def onListSelection(self, evt):
        print("List Selection!", self.Value, self.LastSelectedIndex, self.SelectedIndices)

    def onListDeselection(self, evt):
        print("Row deselected:", evt.EventData["index"])


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dListControl_test)
