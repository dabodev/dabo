import dabo
import wx
import dabo.dEvents as dEvents
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlMixin as dcm
import locale, wx, sys, cStringIO
import wx.lib.mixins.listctrl as listmix
from wx import ImageFromStream, BitmapFromImage

"""
wxPython Custom Widget Collection 20060207
Written By: Edward Flick (eddy -=at=- cdf-imaging -=dot=- com)
		Michele Petrazzo (michele -=dot=- petrazzo -=at=- unipex -=dot=- it)
		Will Sadkin (wsadkin-=at=- nameconnector -=dot=- com)
Copyright 2006 (c) CDF Inc. ( http://www.cdf-imaging.com )
Contributed to the wxPython project under the wxPython project's license.
"""


def getSmallUpArrowData():
	return \
"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x00<IDAT8\x8dcddbf\xa0\x040Q\xa4{h\x18\xf0\xff\xdf\xdf\xffd\x1b\x00\xd3\
\x8c\xcf\x10\x9c\x06\xa0k\xc2e\x08m\xc2\x00\x97m\xd8\xc41\x0c \x14h\xe8\xf2\
\x8c\xa3)q\x10\x18\x00\x00R\xd8#\xec\xb2\xcd\xc1Y\x00\x00\x00\x00IEND\xaeB`\
\x82"


def getSmallUpArrowBitmap():
	return BitmapFromImage(getSmallUpArrowImage())


def getSmallUpArrowImage():
	stream = cStringIO.StringIO(getSmallUpArrowData())
	return ImageFromStream(stream)


def getSmallDnArrowData():
	return \
"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\
\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\
\x00\x00HIDAT8\x8dcddbf\xa0\x040Q\xa4{\xd4\x00\x06\x06\x06\x06\x06\x16t\x81\
\xff\xff\xfe\xfe'\xa4\x89\x91\x89\x99\x11\xa7\x0b\x90%\ti\xc6j\x00>C\xb0\x89\
\xd3.\x10\xd1m\xc3\xe5*\xbc.\x80i\xc2\x17.\x8c\xa3y\x81\x01\x00\xa1\x0e\x04e\
?\x84B\xef\x00\x00\x00\x00IEND\xaeB`\x82"


def getSmallDnArrowBitmap():
	return BitmapFromImage(getSmallDnArrowImage())


def getSmallDnArrowImage():
	stream = cStringIO.StringIO(getSmallDnArrowData())
	return ImageFromStream(stream)



#----------------------------------------------------------------------
class myListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
	def __init__(self, parent, ID=-1, pos=wx.DefaultPosition,
			size=wx.DefaultSize, style=0):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
		listmix.ListCtrlAutoWidthMixin.__init__(self)



class TextCtrlAutoComplete (wx.TextCtrl, listmix.ColumnSorterMixin):
	def __init__ ( self, parent, colNames=None, choices = None,
			multiChoices=None, showHead=True, dropDownClick=True,
			colFetch=-1, colSearch=0, hideOnNoMatch=True,
			selectCallback=None, entryCallback=None, matchFunction=None,
			**therest) :
		"""
		Constructor works just like wx.TextCtrl except you can pass in a
		list of choices. You can also change the choice list at any time
		by calling setChoices.
		"""
		if "style" in therest:
			therest["style"]=wx.TE_PROCESS_ENTER | therest["style"]
		else:
			therest["style"]=wx.TE_PROCESS_ENTER
		wx.TextCtrl.__init__(self, parent, **therest )
		#Some variables
		self._dropDownClick = dropDownClick
		self._colNames = colNames
		self._multiChoices = multiChoices
		self._showHead = showHead
		self._choices = choices
		self._lastinsertionpoint = 0
		self._hideOnNoMatch = hideOnNoMatch
		self._selectCallback = selectCallback
		self._entryCallback = entryCallback
		self._matchFunction = matchFunction
		self._screenheight = wx.SystemSettings.GetMetric( wx.SYS_SCREEN_Y )
		#sort variable needed by listmix
		self.itemDataMap = dict()
		#Load and sort data
		if not (self._multiChoices or self._choices):
			raise ValueError, "Pass me at least one of multiChoices OR choices"
		#widgets
		self.dropdown = wx.PopupWindow( self )
		#Control the style
		flags = wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_SORT_ASCENDING
		if not (showHead and multiChoices) :
			flags = flags | wx.LC_NO_HEADER
		#Create the list and bind the events
		self.dropdownlistbox = myListCtrl( self.dropdown, style=flags,
				pos=wx.Point( 0, 0) )
		#initialize the parent
		if multiChoices: ln = len(multiChoices)
		else: ln = 1
		#else: ln = len(choices)
		listmix.ColumnSorterMixin.__init__(self, ln)
		#load the data
		if multiChoices: self.SetMultipleChoices (multiChoices, colSearch=colSearch, colFetch=colFetch)
		else: self.SetChoices ( choices )
		gp = self
		while gp != None :
			gp.Bind ( wx.EVT_MOVE , self.onControlChanged, gp )
			gp.Bind ( wx.EVT_SIZE , self.onControlChanged, gp )
			gp = gp.GetParent()
		self.Bind( wx.EVT_KILL_FOCUS, self.onControlChanged, self )
		self.Bind( wx.EVT_TEXT , self.onEnteredText, self )
		self.Bind( wx.EVT_KEY_DOWN , self.onKeyDown, self )
		#If need drop down on left click
		if dropDownClick:
			self.Bind ( wx.EVT_LEFT_DOWN , self.onClickToggleDown, self )
			self.Bind ( wx.EVT_LEFT_UP , self.onClickToggleUp, self )
		self.dropdown.Bind( wx.EVT_LISTBOX , self.onListItemSelected, self.dropdownlistbox )
		self.dropdownlistbox.Bind(wx.EVT_LEFT_DOWN, self.onListClick)
		self.dropdownlistbox.Bind(wx.EVT_LEFT_DCLICK, self.onListDClick)
		self.dropdownlistbox.Bind(wx.EVT_LIST_COL_CLICK, self.onListColClick)
		self.il = wx.ImageList(16, 16)
		self.sm_dn = self.il.Add(getSmallDnArrowBitmap())
		self.sm_up = self.il.Add(getSmallUpArrowBitmap())
		self.dropdownlistbox.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
		self._ascending = True


	#-- methods called from mixin class
	def GetSortImages(self):
		return (self.sm_dn, self.sm_up)


	def GetListCtrl(self):
		return self.dropdownlistbox
	# -- event methods


	def onListClick(self, evt):
		toSel, flag = self.dropdownlistbox.HitTest( evt.GetPosition() )
		#no values on poition, return
		if toSel == -1: return
		self.dropdownlistbox.Select(toSel)


	def onListDClick(self, evt):
		self._setValueFromSelected()


	def onListColClick(self, evt):
		col = evt.GetColumn()
		#reverse the sort
		if col == self._colSearch:
			self._ascending = not self._ascending
		self.SortListItems( evt.GetColumn(), ascending=self._ascending )
		self._colSearch = evt.GetColumn()
		evt.Skip()


	def onEnteredText(self, event):
		text = event.GetString()
		if self._entryCallback:
			self._entryCallback()
		if not text:
			# control is empty; hide dropdown if shown:
			if self.dropdown.IsShown():
				self._showDropDown(False)
			event.Skip()
			return
		found = False
		if self._multiChoices:
			#load the sorted data into the listbox
			dd = self.dropdownlistbox
			choices = [dd.GetItem(x, self._colSearch).GetText()
					for x in xrange(dd.GetItemCount())]
		else:
			choices = self._choices
		for numCh, choice in enumerate(choices):
			if self._matchFunction and self._matchFunction(text, choice):
				found = True
			elif choice.lower().startswith(text.lower()) :
				found = True
			if found:
				self._showDropDown(True)
				item = self.dropdownlistbox.GetItem(numCh)
				toSel = item.GetId()
				self.dropdownlistbox.Select(toSel)
				break
		if not found:
			self.dropdownlistbox.Select(self.dropdownlistbox.GetFirstSelected(), False)
			if self._hideOnNoMatch:
				self._showDropDown(False)
		self._listItemVisible()
		event.Skip ()


	def onKeyDown ( self, event ) :
		"""
		Do some work when the user press on the keys: up and down: move the cursor
		left and right: move the search
		"""
		skip = True
		sel = self.dropdownlistbox.GetFirstSelected()
		visible = self.dropdown.IsShown()
		KC = event.GetKeyCode()
		if KC == wx.WXK_DOWN :
			if sel < self.dropdownlistbox.GetItemCount () - 1:
				self.dropdownlistbox.Select ( sel+1 )
				self._listItemVisible()
			self._showDropDown ()
			skip = False
		elif KC == wx.WXK_UP :
			if sel > 0 :
				self.dropdownlistbox.Select ( sel - 1 )
				self._listItemVisible()
			self._showDropDown ()
			skip = False
		##elif KC == wx.WXK_LEFT :
			##if not self._multiChoices: return
			##if self._colSearch > 0:
				##self._colSearch -=1
			##self._showDropDown ()
		##elif KC == wx.WXK_RIGHT:
			##if not self._multiChoices: return
			##if self._colSearch < self.dropdownlistbox.GetColumnCount() -1:
				##self._colSearch += 1
			##self._showDropDown()
		if visible :
			if event.GetKeyCode() == wx.WXK_RETURN :
				self._setValueFromSelected()
				skip = False
			if event.GetKeyCode() == wx.WXK_ESCAPE :
				self._showDropDown( False )
				skip = False
		if skip :
			event.Skip()


	def onListItemSelected (self, event):
		self._setValueFromSelected()
		event.Skip()


	def onClickToggleDown(self, event):
		self._lastinsertionpoint = self.GetInsertionPoint()
		event.Skip ()


	def onClickToggleUp ( self, event ) :
		if self.GetInsertionPoint() == self._lastinsertionpoint :
			self._showDropDown ( not self.dropdown.IsShown() )
		event.Skip ()


	def onControlChanged(self, event):
		if self.IsShown():
			self._showDropDown( False )
		event.Skip()


	# -- Interfaces methods
	def SetMultipleChoices(self, choices, colSearch=0, colFetch=-1):
		""" Set multi-column choice
		"""
		self._multiChoices = choices
		self._choices = None
		if not isinstance(self._multiChoices, list):
			self._multiChoices = list(self._multiChoices)
		flags = wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_SORT_ASCENDING
		if not self._showHead:
			flags |= wx.LC_NO_HEADER
		self.dropdownlistbox.SetWindowStyleFlag(flags)
		#prevent errors on "old" systems
		if sys.version.startswith("2.3"):
			self._multiChoices.sort(lambda x, y: cmp(x[0].lower(), y[0].lower()))
		else:
			self._multiChoices.sort(key=lambda x: locale.strxfrm(x[0]).lower() )
		self._updateDataList(self._multiChoices)
		if len(choices)<2 or len(choices[0])<2:
			raise ValueError("You have to pass me a multi-dimension list with "
					"at least two entries")
			# with only one entry, the dropdown artifacts
		for numCol, rowValues in enumerate(choices[0]):
			if self._colNames: colName = self._colNames[numCol]
			else: colName = "Select %i" % numCol
			self.dropdownlistbox.InsertColumn(numCol, colName)
		for numRow, valRow in enumerate(choices):
			for numCol, colVal in enumerate(valRow):
				if numCol == 0:
					index = self.dropdownlistbox.InsertImageStringItem(
							sys.maxint, colVal, -1)
				self.dropdownlistbox.SetStringItem(index, numCol, colVal)
				self.dropdownlistbox.SetItemData(index, numRow)
		self._setListSize()
		self._colSearch = colSearch
		self._colFetch = colFetch


	def SetChoices(self, choices):
		"""
		Sets the choices available in the popup wx.ListBox.
		The items will be sorted case insensitively.
		"""
		self._choices = choices
		self._multiChoices = None
		flags = wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_SORT_ASCENDING | wx.LC_NO_HEADER
		self.dropdownlistbox.SetWindowStyleFlag(flags)
		if not isinstance(choices, list):
			self._choices = list(choices)
		#prevent errors on "old" systems
		if sys.version.startswith("2.3"):
			self._choices.sort(lambda x, y: cmp(x.lower(), y.lower()))
		else:
			self._choices.sort(key=lambda x: locale.strxfrm(x).lower())
		self._updateDataList(self._choices)
		self.dropdownlistbox.InsertColumn(0, "")
		for num, colVal in enumerate(self._choices):
			index = self.dropdownlistbox.InsertImageStringItem(sys.maxint, colVal, -1)
			self.dropdownlistbox.SetStringItem(index, 0, colVal)
			self.dropdownlistbox.SetItemData(index, num)
		self._setListSize()
		# there is only one choice for both search and fetch if setting a single column:
		self._colSearch = 0
		self._colFetch = -1


	def GetChoices(self):
		return self._choices or self._multiChoices


	def SetSelectCallback(self, cb=None):
		self._selectCallback = cb


	def SetEntryCallback(self, cb=None):
		self._entryCallback = cb


	def SetMatchFunction(self, mf=None):
		self._matchFunction = mf


	#-- Internal methods
	def _setValueFromSelected( self ) :
		"""
		Sets the wx.TextCtrl value from the selected wx.ListCtrl item.
		Will do nothing if no item is selected in the wx.ListCtrl.
		"""
		sel = self.dropdownlistbox.GetFirstSelected()
		if sel > -1:
			if self._colFetch != -1: col = self._colFetch
			else: col = self._colSearch
			itemtext = self.dropdownlistbox.GetItem(sel, col).GetText()
			if self._selectCallback:
				dd = self.dropdownlistbox
				values = [dd.GetItem(sel, x).GetText()
						for x in xrange(dd.GetColumnCount())]
				self._selectCallback( values )
			self.SetValue (itemtext)
			self.SetInsertionPointEnd ()
			self.SetSelection ( -1, -1 )
			self._showDropDown ( False )


	def _showDropDown ( self, show = True ) :
		"""
		Either display the drop down list (show = True) or hide it (show = False).
		"""
		if show :
			size = self.dropdown.GetSize()
			width, height = self . GetSizeTuple()
			x, y = self . ClientToScreenXY ( 0, height )
			#if size.GetHeight() < 100:
				#size.SetHeight(100)
			if size.GetWidth() != width :
				size.SetWidth(width)

			self.dropdown.SetSize(size)
			self.dropdownlistbox.SetSize(self.dropdown.GetClientSize())

			if y + size.GetHeight() < self._screenheight :
				self.dropdown . SetPosition ( wx.Point(x, y) )
			else:
				self.dropdown . SetPosition ( wx.Point(x, y - height - size.GetHeight()) )
		self.dropdown.Show ( show )


	def _listItemVisible( self ) :
		"""
		Moves the selected item to the top of the list ensuring it is always visible.
		"""
		toSel = self.dropdownlistbox.GetFirstSelected ()
		if toSel == -1: return
		self.dropdownlistbox.EnsureVisible( toSel )


	def _updateDataList(self, choices):
		#delete, if need, all the previous data
		if self.dropdownlistbox.GetColumnCount() != 0:
			self.dropdownlistbox.DeleteAllColumns()
			self.dropdownlistbox.DeleteAllItems()
		#and update the dict
		if choices:
			for numVal, data in enumerate(choices):
				self.itemDataMap[numVal] = data
		else:
			numVal = 0
		self.SetColumnCount(numVal)


	def _setListSize(self):
		if self._multiChoices:
			choices = self._multiChoices
		else:
			choices = self._choices
		longest = 0
		for choice in choices :
			longest = max(len(choice), longest)
		longest += 3
		itemcount = min( len( choices ) , 7 ) + 2
		charheight = self.dropdownlistbox.GetCharHeight()
		charwidth = self.dropdownlistbox.GetCharWidth()
		self.popupsize = wx.Size( charwidth*longest, charheight*(itemcount+1) )
		self.dropdownlistbox.SetSize ( self.popupsize )
		self.dropdown.SetClientSize( self.popupsize )



class dAutoComplete(dcm.dControlMixin, TextCtrlAutoComplete):
	"""
	Creates a text box with a dropdown list that has the ability to filter
	multiple records or choices in the list based on entered text.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dAutoComplete
		preClass = TextCtrlAutoComplete
		kwargs["entryCallback"] = self.fillDynamicChoices
		kwargs["choices"] = [""]
		self._userColNames = False
		self._dynamicChoices = None
		dcm.dControlMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)


	def _initEvents(self):
		super(dAutoComplete, self)._initEvents()


	def onKeyDown(self,evt):
		"""This prevents dEvents from being passed to autocomplete's onKeyDown"""
		if isinstance(evt, wx.KeyEvent):
			super(dAutoComplete, self).onKeyDown(evt)


	def onKeyUp(self,evt):
		if isinstance(evt, wx.KeyEvent):
			if evt.GetKeyCode() == wx.WXK_BACK:
				#Make sure fillDynamicChoices() gets called on backspace as well
				self.fillDynamicChoices()


	def getBizobj(self):
		ds = self.DataSource
		if isinstance(ds, dabo.biz.dBizobj):
			return ds
		if isinstance(ds, basestring) and self.Form is not None:
			form = self.Form
			while form is not None:
				if hasattr(form, "getBizobj"):
					biz = form.getBizobj(ds)
					if isinstance(biz, dabo.biz.dBizobj):
						if not biz.isRemote():
							self._dataSource = biz
					return biz
				form = form.Form
		return None


	def listFromDS(self):
		"""
		Takes a data set from the DataSource bizobj or the DataSet property
		directly and formats it as a choice list for autocomplete, using field
		names as column headers by default or the ColNames property as column
		headers if defined.
		"""
		colSearch = colFetch = None
		biz = self.getBizobj()

		if biz:
			ds = biz.getDataSet()
			if biz.RowCount == 0:
				# Manually update for empty data source
				flds = self.DataFields
				if flds and len(flds) > 1:
					self._setDynamicChoices(["" for rec in flds])
				elif not flds and biz.DataStructure:
					self._setDynamicChoices(["" for rec in biz.DataStructure])
				else:
					self._setDynamicChoices([""])
		else:
			ds = self.DataSet
		if not ds:
			return

		choices = []
		colKeys = self.DataFields
		if not colKeys:
			colKeys = [key for key in ds[0].keys()]

		if len(colKeys) == 1:
			#Single column
			for rec in ds:
				choices.append(str(rec[colKeys[0]]))
		else:
			#Multi column
			try:
				for rec in ds:
					choices.append([str(rec[key]) for key in colKeys])
			except KeyError:
				raise ValueError("DataField '%s' is not a valid column name" % key)

			#Find search index
			try:
				if self.SearchField is not None:
					if isinstance(self.SearchField, basestring):
						colSearch = colKeys.index(self.SearchField)
					else:
						colSearch = self.SearchField
				else: colSearch = 0
			except ValueError:
				raise ValueError("SearchField '%s' is not a valid column name"
						% self.SearchField)

			#Find fetch index
			try:
				if self.FetchField is not None:
					if isinstance(self.FetchField, basestring):
						colFetch = colKeys.index(self.FetchField)
					else:
						colFetch = self.FetchField
				else: colFetch = -1
			except ValueError:
				raise ValueError("FetchField '%s' is not a valid column name"
						% self.FetchField)

		self._colNames = colKeys if not self._userColNames else self._colNames
		self._setDynamicChoices(choices, colSearch=colSearch, colFetch=colFetch)


	def fillDynamicChoices(self):
		"""
		The default entry callback function: takes the user-entered text from
		the text box and updates the dropdown list to include only entries in
		which the value of the search field starts with the given string.i
		"""
		text = self.GetValue().lower()
		current_choices = self.Choices
		if not self._dynamicChoices:
			return
		if not text:
			choices = self._dynamicChoices
		elif isinstance(self._dynamicChoices[0], list):
			choices = [choice for choice in self._dynamicChoices
					if choice[self._colSearch].lower().startswith(text)]
			while len(choices) < 2:
				choices.append(["" for col in self._dynamicChoices[0]])
		else:
			choices = [choice for choice in self._dynamicChoices
					if choice.lower().startswith(text)]
			while len(choices) < 2:
				choices.append("")
		if choices != current_choices:
			self._insertChoices(choices)
		if not self.IsShown():
			self._showDropDown()


	def update(self):
		"""
		Call this when your datasource or dataset has changed to get the list showing
		the proper number of rows with current data.
		"""
		self.listFromDS()


	def _setDynamicChoices(self, choices, colSearch=None, colFetch=None):
		"""Updates the choices and sets self._dynamicChoices (needed for callback)"""
		self._insertChoices(choices, colSearch, colFetch)
		self._dynamicChoices = self.Choices


	def _insertChoices(self, choices, colSearch=None, colFetch=None):
		"""
		Handles all choice list modifications. If the list is one-dimensional,
		calls SetChoices(); if two-dimensional, calls SetMultipleChoices().
		"""
		if isinstance(choices[0], list):
			if not colSearch:
				colSearch = self._colSearch
			if not colFetch:
				colFetch = self._colFetch
			while len(choices) < 2:
				choices.append(["" for col in choices[0]])
			if self._colNames:
				while len(self._colNames) < len(choices[0]):
					self._colNames.append("")
			self.SetMultipleChoices(choices, colSearch=colSearch, colFetch=colFetch)
		else:
			self.SetChoices(choices)


	##                                ##
	##  Property getters and setters  ##
	##                                ##
	def _getDataSource(self):
		try:
			src = self._dataSource
		except AttributeError:
			src = self._dataSource = None
		return src

	def _setDataSource(self,src):
		if self._constructed():
			self._dataSource = src
			dabo.ui.callAfter(self.listFromDS)
		else:
			self._properties["DataSource"] = src


	def _getDataFields(self):
		try:
			fld = self._dataFields
		except AttributeError:
			fld = self._dataFields = None
		return fld

	def _setDataFields(self, flds):
		if self._constructed():
			self._dataFields = flds
		else:
			self._properties["DataFields"] = flds


	def _getDataSet(self):
		ds = None
		biz = self.DataSource
		if biz:
			if isinstance(biz, dabo.biz.dBizobj):
				ds = self._dataSource.getDataSet()
			else:
				try:
					ds = eval(biz).getDataSet()
				except StandardError:
					pass
				self._dataSet = ds
		else:
			try:
				ds = self._dataSet
			except AttributeError:
				ds = self._dataSet = None
		return ds

	def _setDataSet(self, ds):
		if self._constructed():
			if self.DataSource:
				raise ValueError("Cannot set DataSet: DataSource defined.")
			self._dataSet = ds
			dabo.ui.callAfter(self.listFromDS)
		else:
			self._properties["DataSet"] = ds


	def _getSearchField(self):
		try:
			fld = self._searchField
		except AttributeError:
			fld = self._searchField = None
		return fld

	def _setSearchField(self, fld):
		if self._constructed():
			self._searchField = fld
			if isinstance(fld, int):
				self._colSearch = fld
		else:
			self._properties["SearchField"] = fld


	def _getFetchField(self):
		try:
			fld = self._fetchField
		except AttributeError:
			fld = self._fetchField = None
		return fld

	def _setFetchField(self, fld):
		if self._constructed():
			self._fetchField = fld
			if isinstance(fld, int):
				self._colFetch = fld
		else:
			self._properties["FetchField"] = fld


	def _getChoices(self):
		return self.GetChoices()

	def _setChoices(self, choices):
		if self._constructed():
			if self.DataSource or self.DataSet:
				raise ValueError("Cannot set Choices: DataSource or DataSet already defined.")
			try:
				choices[0]
			except:
				raise ValueError("Cannot set Choices: A single or multi-columna"
						"list with at least one element must be provided.")
			dabo.ui.callAfter(self._setDynamicChoices, choices)
		else:
			self._properties["Choices"] = choices


	def _getColNames(self):
		return self._colNames

	def _setColNames(self, names):
		if self._constructed():
			self._colNames = names
			self._userColNames = False if names is None else True

		else:
			self._properties["ColNames"] = names


	##                        ##
	##  Property definitions  ##
	##                        ##
	DataSource = property(_getDataSource, _setDataSource, None,
			"""The source of the data to display in the list.  (str)

			This corresponds to a bizobj with a matching DataSource on the form,
			and setting this makes it impossible to set DataSet.""")

	DataFields = property(_getDataFields, _setDataFields, None,
			"""The fields from the data set to display in the list.  (list of strs)

			Fields will be displayed in order of this list. If not set, all
			fields in the data set will be displayed in default order.""")

	DataSet = property(_getDataSet, _setDataSet, None,
			"""The set of data displayed in the list.  (set of dicts)

			When DataSource isn't defined, setting DataSet to a set of dicts,
			such as what you get from calling dBizobj.getDataSet(), will
			define the source of the data that the list displays.

			If DataSource is defined, DataSet is read-only and returns the data set
			from the bizobj.""")

	SearchField = property(_getSearchField, _setSearchField, None,
			"""The field or column used to compare with user-entered text.  (str or int)

			When given a field name, strings in the text box will be matched
			with the corresponding field's value. If an int is provided,
			columns are chosen by index (starting with 0). If not set, the
			search will be done on the leftmost field (index 0).""")

	FetchField = property(_getFetchField, _setFetchField, None,
			"""The field or column displayed in the text box when a value is
			selected from the list. (str or int)

			When given a field name, selecting an entry in the dropdown list
			will diplay the corresponding field's value for that entry in the
			text box. If an int is provided, columns are chosen by index
			(starting with 0). If not set, the field specified by SearchField
			will be used.""")

	Choices = property(_getChoices, _setChoices, None,
			"""The choices to put in the dropdown list when no DataSource or
			DataSet is provided.  (list)

			This list can consist of strings (one-dimensional) or sublists of
			strings (two-dimensional) and the number of columns in the list
			will be set accordingly. All sublists must be of the same length.

			If DataSource or DataSet are defined, this field becomes read-only
			and returns the choices currently in the list.""")

	ColNames = property(_getColNames, _setColNames, None,
			"""The names used to label columns.  (list of strs)

			If this list is of a different length than the number of columns,
			blank column names will be added or extra column names ignored as
			appropriate.""")



if __name__ == "__main__":
	import test

	class TestPanel(dabo.ui.dPanel):
		def afterInit(self):
			import datetime
			currentYear = datetime.datetime.now().year
			self.Caption = "dAutoComplete"
			self.Sizer = vs = dabo.ui.dSizer("v")
			ds = [{"landmark":"Eiffel Tower", "loc":"Paris, France", "constructed":"1889"},
					{"landmark":"Statue of Liberty", "loc":"New York, New York", "constructed":"1884"},
					{"landmark":"Great Sphinx of Giza", "loc":"Giza, Egypt", "constructed":"c. 2558 BC"},
					{"landmark":"Stonehenge", "loc":"Wiltshire, England", "constructed":"3000 - 2000 BC"}]

			vs.append(dabo.ui.dLabel(self, Caption="Press the down arrow key to see the list of choices.",
					FontBold=True), alignment="center")
			vs.appendSpacer(15)
			vs.append(dabo.ui.dLabel(self, Caption="User defined choices (single-column)"))
			vs.append(dAutoComplete(self, Choices=["Bob","Joe","Mary","Bill","Marcia","Eric"]), "x")
			vs.appendSpacer(5)
			vs.append(dabo.ui.dLabel(self, Caption="Data set (single-column)"))
			vs.append(dAutoComplete(self, DataSet=ds, DataFields=["landmark"]), "x")
			vs.appendSpacer(5)
			vs.append(dabo.ui.dLabel(self, Caption="Data set (multi-column):"))
			vs.append(dAutoComplete(self, DataSet=ds, SearchField="landmark", FetchField="loc",
					ColNames=["Landmark", "Location", "Year Constructed"]), "x")


	test.Test().runTest(TestPanel)

