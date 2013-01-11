# -*- coding: utf-8 -*-
import os
import sys
import dabo
import dabo.dException as dException
import dabo.dEvents as dEvents
from dabo.dLocalize import _, n_
from dabo.dObject import dObject
from dabo.lib.utils import ustr
from dabo.ui import dPanel
from . import QRY_OPERATOR
import Grid

ASC, DESC = (n_("asc"), n_("desc"))

# Controls for the select page:
class SelectControlMixin(dObject):
	def initProperties(self):
		super(SelectControlMixin, self).initProperties()
		self.SaveRestoreValue = True

class SelectTextBox(SelectControlMixin, dabo.ui.dTextBox): pass
class SelectCheckBox(SelectControlMixin, dabo.ui.dCheckBox): pass
class SelectLabel(SelectControlMixin, dabo.ui.dLabel):
	def afterInit(self):
		# Basically, we don't want anything to display, but it's
		# easier if every selector has a matching control.
		self.Caption = ""
class SelectDateTextBox(SelectControlMixin, dabo.ui.dDateTextBox): pass
class SelectSpinner(SelectControlMixin, dabo.ui.dSpinner): pass

class SelectionOpDropdown(dabo.ui.dDropdownList):
	def initProperties(self):
		super(SelectionOpDropdown, self).initProperties()
		self.SaveRestoreValue = True

	def initEvents(self):
		super(SelectionOpDropdown, self).initEvents()
		self.bindEvent(dEvents.Hit, self.onChoiceMade)
		self.bindEvent(dEvents.ValueChanged, self.onValueChanged)

	def onValueChanged(self, evt):
		# italicize if we are ignoring the field:
		self.FontItalic = (QRY_OPERATOR.IGNORE in self.Value)
		if self.Target:
			self.Target.FontItalic = self.FontItalic

	def onChoiceMade(self, evt):
		if QRY_OPERATOR.IGNORE not in self.StringValue:
			# A comparison op was selected; let 'em enter a value
			self.Target.setFocus()

	def _getTarget(self):
		try:
			_target = self._target
		except AttributeError:
			_target = self._target = None
		return _target

	def _setTarget(self, tgt):
		self._target = tgt
		if self.Target:
			self.Target.FontItalic = self.FontItalic

	Target = property(_getTarget, _setTarget, None, "Holds a reference to the edit control.")


class Page(dabo.ui.dPage):
	def initEvents(self):
		super(Page, self).initEvents()
		self.bindEvent(dEvents.PageEnter, self.__onPageEnter)
		self.bindEvent(dEvents.PageLeave, self.__onPageLeave)


	def __onPageEnter(self, evt):
		self._onPageEnter()
		if self.UpdateOnPageEnter:
			dabo.ui.callAfter(self.update)


	def _onPageEnter(self):
		"""Subclass hook."""
		pass


	def __onPageLeave(self, evt):
		self._onPageLeave()


	def _onPageLeave(self):
		"""Subclass hook."""
		pass



	def newRecord(self, ds=None):
		"""Called by a browse grid when the user wants to add a new row."""
		if ds is None:
			self.Form.new()
			self.editRecord()
		else:
			self.Parent.newByDataSource(ds)


	def deleteRecord(self, ds=None):
		"""Called by a browse grid when the user wants to delete the current row."""
		if ds is None:
			self.Form.delete()
		else:
			self.Parent.deleteByDataSource(ds)


	def editRecord(self, ds=None):
		"""Called by a browse grid when the user wants to edit the current row."""
		if ds is None:
			self.Parent.SetSelection(2)
		else:
			self.Parent.editByDataSource(ds)


	def _getUpdateOnPageEnter(self):
		return getattr(self, "_updateOnPageEnter", True)

	def _setUpdateOnPageEnter(self, val):
		self._updateOnPageEnter = bool(val)

	UpdateOnPageEnter = property(_getUpdateOnPageEnter, _setUpdateOnPageEnter, None,
			_("""Specifies whether an implicit self.update() happens upon page entry."""))



class SelectOptionsPanel(dPanel):
	"""Base class for the select options panel."""
	def initProperties(self):
		self.Name = "selectOptionsPanel"


class SortLabel(dabo.ui.dLabel):
	def initEvents(self):
		super(SortLabel, self).initEvents()
		self.bindEvent(dEvents.MouseRightClick, self.Parent.Parent.onSortLabelRClick)
		# Add a property for the related field
		self.relatedDataField = ""


class SelectPage(Page):
	def _createItems(self):
		super(SelectPage, self)._createItems()

		## The following line is needed to get the Select page scrollbars to lay
		## out without the user having to resize manually. I tried putting it in
		## dPage but that caused problems with the Class Designer. We need to
		## figure out the best way to abstract this wx call, or find a different
		## way to get the scrollbars.
		self.Sizer.FitInside(self)


	def afterInit(self):
		super(SelectPage, self).afterInit()
		# Holds info which will be used to create the dynamic
		# WHERE clause based on user input
		self.selectFields = {}
		self.sortFields = {}
		self.__virtualFilters = []
		self.sortIndex = 0


	def _initProperties(self):
		self.UpdateOnPageEnter = False
		super(SelectPage, self)._initProperties()


	def onSortLabelRClick(self, evt):
		obj = self.sortObj = evt.EventObject
		sortDS = getattr(obj, "relatedDataField", None)
		if not self.Form.ShowSortFields or not sortDS:
			return
		self.sortDS = sortDS
		self.sortCap = obj.Caption
		mn = dabo.ui.dMenu()
		if self.sortFields:
			mn.append(_("Show sort order"), OnHit=self.handleSortOrder)
		if self.sortDS in self.sortFields:
			mn.append(_("Remove sort on ") + self.sortCap,
					OnHit=self.handleSortRemove)

		mn.append(_("Sort Ascending"), OnHit=self.handleSortAsc)
		mn.append(_("Sort Descending"), OnHit=self.handleSortDesc)
		self.PopupMenu(mn, obj.formCoordinates(evt.EventData["mousePosition"]))
		mn.release()

	def handleSortOrder(self, evt):
		self.handleSort(evt, "show")
	def handleSortRemove(self, evt):
		self.handleSort(evt, "remove")
	def handleSortAsc(self, evt):
		self.handleSort(evt, ASC)
	def handleSortDesc(self, evt):
		self.handleSort(evt, DESC)
	def handleSort(self, evt, action):
		if action == "remove":
			try:
				del self.sortFields[self.sortDS]
			except KeyError:
				pass
		elif action == "show":
			# Get the descrips and order
			sf = self.sortFields
			dd = [(sf[kk][0], kk, "%s %s" % (sf[kk][2], sf[kk][1]))
					for kk in sf]
			sortDesc = [itm[2] for itm in sorted(dd)]
			sortedList = dabo.ui.sortList(sortDesc)
			newPos = 0
			for itm in sortedList:
				origPos = sortDesc.index(itm)
				key = dd[origPos][1]
				self.sortFields[key] = (newPos, self.sortFields[key][1], self.sortFields[key][2])
				newPos += 1
		elif action != "show":
			if self.sortDS in self.sortFields:
				self.sortFields[self.sortDS] = (self.sortFields[self.sortDS][0],
						action, self.sortCap)
			else:
				self.sortFields[self.sortDS] = (self.sortIndex, action, self.sortCap)
				self.sortIndex += 1
		self.sortCap = self.sortDS = ""



	def createItems(self):
		if not self.Sizer:
			self.Sizer = dabo.ui.dSizer("v")
		self.selectOptionsPanel = self.getSelectOptionsPanel()
		if self.selectOptionsPanel:
			self.Sizer.append(self.selectOptionsPanel, "expand", 1, border=20)
			self.selectOptionsPanel.setFocus()
		super(SelectPage, self).createItems()


	def setFrom(self, biz):
		"""Subclass hook."""
		pass

	def setGroupBy(self, biz):
		"""Subclass hook."""
		pass


	def setOrderBy(self, biz):
		orderBy = self._orderByClause()
		if orderBy:
			# Only set (overriding the bizobj) if the user specified a sort
			biz.setOrderByClause(orderBy)

	def _orderByClause(self, infoOnly=False):
		sf = self.sortFields
		if infoOnly:
			parts = lambda (k): (sf[k][2], sf[k][1])
		else:
			parts = lambda (k): (k, sf[k][1].upper())

		flds = sorted((self.sortFields[k][0], k, " ".join(parts(k)))
			for k in self.sortFields)
		if infoOnly:
			return [e[1:] for e in flds]
		else:
			return ",".join([ k[2] for k in flds])


	def setWhere(self, biz):
		if not self.itemsCreated:
			self.createItems()
		try:
			baseWhere = biz.getBaseWhereClause()
		except AttributeError:
			# prior datanav apps inherited from dBizobj directly,
			# and dBizobj doesn't define getBaseWhereClause.
			baseWhere = ""
		biz.setWhereClause(baseWhere)
		tbl = getattr(biz, "DataSourceName", biz.DataSource)
		whr = ""
		for fld in self.selectFields:
			if fld in biz.VirtualFields:
				#virtual field, save for later use and ignore
				self.__virtualFilters.append(fld)
				continue
			if fld == "limit":
				# Handled elsewhere
				continue

			try:
				## the datanav bizobj has an optional dict that contains
				## mappings from the fld to the actual names of the backend
				## table and field, so that you can have fields in your where
				## clause that aren't members of the "main" table.
				table, field = biz.BackendTableFields[fld]
			except (AttributeError, KeyError):
				table, field = tbl, fld

			try:
				opVal = self.selectFields[fld]["op"].Value
			except AttributeError:
				# Operator could be Enum type.
				opVal = self.selectFields[fld]["op"]
			opStr = opVal
			expJoint = self.selectFields[fld].get("joint", "and")
			if not QRY_OPERATOR.IGNORE in opVal:
				fldType = self.selectFields[fld]["type"]
				ctrl = self.selectFields[fld]["ctrl"]
				if fldType == "bool":
					# boolean fields won't have a control; opVal will
					# be either 'Is True' or 'Is False'
					matchVal = (opVal == QRY_OPERATOR.TRUE)
				elif callable(ctrl):
					try:
						matchVal = ctrl()
					except AttributeError:
						matchVal = None
				else:
					matchVal = ctrl.Value
				try:
					matchStr = "%s" % matchVal
				except TypeError:
					matchStr = ""
				#matchStr = "%s" % matchVal
				useStdFormat = True

				if fldType in ("char", "memo"):
					if opVal in (QRY_OPERATOR.EQUAL, QRY_OPERATOR.IS):
						opStr = "="
						matchStr = biz.escQuote(matchVal)
					elif opVal == QRY_OPERATOR.MATCH:
						useStdFormat = False
						whrMatches = []
						for word in matchVal.split():
							mtch = {"table": table.strip(), "field": field.strip(), "value": word.strip()}
							whrMatches.append(biz.getWordMatchFormat() % mtch)
						if len(whrMatches) > 0:
							whr = " and ".join(whrMatches)
					else:
						# "Begins With" or "Contains"
						opStr = "LIKE"
						if matchVal is None:
							matchStr = biz.escQuote("null")
						elif opVal == QRY_OPERATOR.BEGINS:
							matchStr = biz.escQuote(matchVal + "%")
						else:
							matchStr = biz.escQuote("%" + matchVal + "%")

				elif fldType in ("date", "datetime"):
					if isinstance(ctrl, dabo.ui.dDateTextBox):
						dtTuple = ctrl.getDateTuple()
						dt = "%s-%s-%s" % (dtTuple[0], ustr(dtTuple[1]).zfill(2),
								ustr(dtTuple[2]).zfill(2))
					else:
						dt = matchVal
					matchStr = biz.formatDateTime(dt)
					if opVal in (QRY_OPERATOR.EQUAL, QRY_OPERATOR.IS):
						opStr = "="
					elif opVal == QRY_OPERATOR.ONBEFORE:
						opStr = "<="
					elif opVal == QRY_OPERATOR.ONAFTER:
						opStr = ">="
					elif opVal == QRY_OPERATOR.BEFORE:
						opStr = "<"
					elif opVal == QRY_OPERATOR.AFTER:
						opStr = ">"

				elif fldType in ("int", "float"):
					#PVG: if we have a int tuple, use all values
					if isinstance(matchVal, tuple):
						useStdFormat = False
						whrMatches = []
						for word in matchVal:
							mtch = {"table": table, "field": field, "value": word}
							whrMatches.append(biz.getWordMatchFormat() % mtch)
						if len(whrMatches) > 0:
							whr = "(" + " or ".join(whrMatches) + ")"
					if opVal in (QRY_OPERATOR.EQUAL, QRY_OPERATOR.IS):
						opStr = "="
					elif opVal == QRY_OPERATOR.LESSEQUAL:
						opStr = "<="
					elif opVal == QRY_OPERATOR.GREATEREQUAL:
						opStr = ">="
					elif opVal == QRY_OPERATOR.LESS:
						opStr = "<"
					elif opVal == QRY_OPERATOR.GREATER:
						opStr = ">"

				elif fldType == "bool":
					opStr = "="
					if opVal == QRY_OPERATOR.TRUE:
						matchStr = "True"
					else:
						matchStr = "False"

				# We have the pieces of the clause; assemble them together
				if useStdFormat:
					whr = "%s.%s %s %s" % (table, field, opStr, matchStr)
				if len(whr) > 0:
					biz.addWhere(whr, expJoint)
		return


	def onRequery(self, evt):
		self.requery()


	def setLimit(self, biz):
		if "limit" in self.selectFields:
			biz.setLimitClause(self.selectFields["limit"]["ctrl"].Value)


	def requery(self):
		frm = self.Form
		bizobj = frm.getBizobj()
		ret = False
		if bizobj:
			sql = frm.CustomSQL
			if sql is not None:
				bizobj.UserSQL = sql
			else:
				# CustomSQL is not defined. Get it from the select page settings:
				bizobj.UserSQL = None
				self.setFrom(bizobj)
				self.setWhere(bizobj)
				self.setOrderBy(bizobj)
				self.setGroupBy(bizobj)
				self.setLimit(bizobj)

				sql = bizobj.getSQL()
				bizobj.setSQL(sql)

			ret = frm.requery(_fromSelectPage=True)

			if bizobj.RowCount > 0:  # don't bother applying this if there are no records to work on
				# filter virtual fields
				for vField in self.__virtualFilters:
					opVal = self.selectFields[vField]["op"].Value
					ctrl = self.selectFields[vField]["ctrl"]

					if not QRY_OPERATOR.IGNORE in opVal:
						bizobj.filter(vField, ctrl.Value, opVal.lower())

		if ret:
			if self.Parent.SelectedPageNumber == 0:
				# If the select page is active, now make the browse page active
				self.Parent.SelectedPageNumber = 1


	def getSelectorOptions(self, typ, wordSearch=False):
		# The fieldspecs version sends the wordSearch parameter as a "1" or "0"
		# string. The following conversion should work no matter what:
		wordSearch = bool(int(wordSearch))
		if typ in ("char", "memo"):
			if typ == "char":
				chcList = (QRY_OPERATOR.EQUAL,
						QRY_OPERATOR.BEGINS,
						QRY_OPERATOR.CONTAINS)
			elif typ == "memo":
				chcList = (QRY_OPERATOR.BEGINS,
						QRY_OPERATOR.CONTAINS)
			if wordSearch:
				chcList += (QRY_OPERATOR.MATCH,)
			chc = tuple(chcList)
		elif typ in ("date", "datetime"):
			chc = (QRY_OPERATOR.EQUAL,
					QRY_OPERATOR.ONBEFORE,
					QRY_OPERATOR.ONAFTER,
					QRY_OPERATOR.BEFORE,
					QRY_OPERATOR.AFTER)
		elif typ in ("int", "float", "decimal"):
			chc = (QRY_OPERATOR.EQUAL,
					QRY_OPERATOR.GREATER,
					QRY_OPERATOR.GREATEREQUAL,
					QRY_OPERATOR.LESS,
					QRY_OPERATOR.LESSEQUAL)
		elif typ == "bool":
			chc = (QRY_OPERATOR.TRUE, QRY_OPERATOR.FALSE)
		else:
			dabo.log.error(_("Type '%s' not recognized.") % typ)
			chc = ()
		return chc


	def getSelectOptionsPanel(self):
		"""Subclass hook. Return the panel instance to display on the select page."""
		pass


	def onCustomSQL(self, evt):
		cb = evt.EventObject
		bizobj = self.Form.getBizobj()
		if cb.Value:
			# Get default SQL, display to user, and then use whatever the user enters
			sql = self.Form.CustomSQL
			if sql is None:
				# CustomSQL is not defined. Get it from the select page settings:
				bizobj.UserSQL = None
				self.setWhere(bizobj)
				self.setOrderBy(bizobj)
				self.setLimit(bizobj)

				sql = bizobj.getSQL()

			dlg = dabo.ui.dDialog(self, Caption=_("Set Custom SQL"),
					SaveRestorePosition=True, BorderResizable=True)
			eb = dlg.addObject(dabo.ui.dEditBox, Value=sql, Size=(400, 400))
			for ff in ["Monospace", "Monaco", "Courier New"]:
				try:
					eb.FontFace = ff
					break
				except dabo.ui.assertionException:
					continue
			dlg.Sizer.append1x(eb)
			dlg.show()
			self.Form.CustomSQL = eb.Value
			dlg.release()

		else:
			# Clear the custom SQL
			self.Form.CustomSQL = None


	def getSearchCtrlClass(self, typ):
		"""Returns the appropriate editing control class for the given data type."""
		if typ in ("char", "memo", "float", "int", "decimal", "datetime"):
			return SelectTextBox
		elif typ == "bool":
			return SelectLabel
		elif typ == "date":
			return SelectDateTextBox
		return None


class BrowsePage(Page):
	def __init__(self, parent, Name=None, *args, **kwargs):
		if Name is None:
			Name = "pageBrowse"
		super(BrowsePage, self).__init__(parent, Name=Name, *args, **kwargs)


	def _onPageEnter(self):
		if not self.itemsCreated:
			self.createItems()
		if self.Form.SetFocusToBrowseGrid:
			self.BrowseGrid.setFocus()
		if not self.Form.EnableChildRequeriesWhenBrowsing:
			biz = self.Form.getBizobj()
			biz.RequeryChildrenOnNavigate = False

	def _onPageLeave(self):
		if self.Form.EnableChildRequeriesWhenEditing:
			biz = self.Form.getBizobj()
			biz.RequeryChildrenOnNavigate = True
			biz.requeryAllChildren()


	def createItems(self):
		biz = self.Form.getBizobj()
		grid = self.Form.BrowseGridClass(self, NameBase="BrowseGrid", Size=(10, 10))
		if biz:
			grid.DataSource = biz.DataSource
		self.Sizer.append(grid, 2, "expand")
		self.layout()
		self.itemsCreated = True



class EditPage(Page):
	def __init__(self, parent, ds=None, *args, **kwargs):
		self._focusToControl = None
		self.itemsCreated = False
		self._dataSource = ds
		self.childGrids = []
		self.childrenAdded = False
		super(EditPage, self).__init__(parent, *args, **kwargs)
		if self.DataSource:
			self.buildPage()


	def initEvents(self):
		super(EditPage, self).initEvents()
		self.Form.bindEvent(dEvents.RowNumChanged, self.__onRowNumChanged)


	def buildPage(self):
		if not self.DataSource:
			return
		self.createItems()


	def __onRowNumChanged(self, evt):
		for cg in self.childGrids:
			cg.populate()


	def _onPageLeave(self):
		self.Form.setPrimaryBizobjToDefault(self.DataSource)


	def _onPageEnter(self):
		self.Form.PrimaryBizobj = self.DataSource
		focusToControl = self._focusToControl
		if focusToControl is not None:
			focusToControl.setFocus()
			self._focusToControl = None
		# The current row may have changed. Make sure that the
		# values are current
		self.__onRowNumChanged(None)


	def createItems(self):
		"""Subclass hook. Create your items and then call super()"""
		self.Sizer.layout()
		self.itemsCreated = True

	def _getDS(self):
		return self._dataSource

	def _setDS(self, val):
		self._dataSource = val
		if not self.itemsCreated:
			self.buildPage()

	DataSource = property(_getDS, _setDS, None,
			_("Table that is the primary source for the fields displayed on the page  (str)"))

