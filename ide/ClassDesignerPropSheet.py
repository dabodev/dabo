# -*- coding: utf-8 -*-
from six import text_type as sixUnicode
from six import string_types as sixBasestring
import os
import pydoc
import dabo.ui
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
from dabo.dLocalize import _
from dabo.ui import dKeys as dKeys
import dabo.dEvents as dEvents
from ClassDesignerComponents import LayoutPanel
from ClassDesignerComponents import LayoutSpacerPanel
from ClassDesignerComponents import LayoutSizer
from ClassDesignerComponents import LayoutBorderSizer
from ClassDesignerComponents import LayoutGridSizer
from ClassDesignerExceptions import PropertyUpdateException



class PropSheet(dabo.ui.dPanel):
	def afterInit(self):
		self._sashPct = 80
		self.mainSplit = msp = dabo.ui.dSplitter(self, Orientation="H", createPanes=True,
				MinimumPanelSize=75, SashPercent=self._sashPct,
				OnSashDoubleClick=self.onSash2Click)
		self.mainSplit.bindEvent(dEvents.SashPositionChanged, self.onSashPosChanged)
		self.panePropGrid = ppg = msp.Panel1
		self.panePropDoc = ppd = msp.Panel2
		self.propGrid = pg = PropertyGrid(ppg)
		pg.Handler = self
		self.btnEdit = dabo.ui.dButton(ppg, Caption=_("Edit..."), Visible=False)
		self.btnEdit.bindEvent(dEvents.Hit, self.onBtnEdit)
		self.edtPropDoc = dabo.ui.dEditBox(ppd, ReadOnly=True,
			FontSize=9, Height=49)
		sz = self.Sizer = dabo.ui.dSizer("v")
		sz.appendSpacer(10)
		sz.DefaultBorderLeft = sz.DefaultBorderRight = True
		sz.DefaultBorder = 10
		sz.append1x(msp)
		sz = ppg.Sizer = dabo.ui.dSizer("v")
		sz.append1x(pg)
		sz.append(self.btnEdit, halign="center", border=5)
		sz = ppd.Sizer = dabo.ui.dSizer("v")
		sz.append1x(self.edtPropDoc)
		self.Sizer.appendSpacer(10)
		# Reference to the currently selected object(s)
		self._selected = []
		# Holds a reference to the custom editor method
		self._custEditor = None
		dabo.ui.callAfter(self.setInitialSizing)
		dabo.ui.callAfter(self.layout)


	def setPanels(self):
		# On some platforms (Gtk especially), the final size is not
		# set, even with callAfter(). But with two levels of callAfter()
		# it seems to work properly
		dabo.ui.callAfter(self._setPanels1)
	def _setPanels1(self):
		dabo.ui.callAfter(self._setPanels2)
	def _setPanels2(self):
		self._sashPct = self.mainSplit.SashPercent = 80
		self.layout()


	def onSashPosChanged(self, evt):
		if self.mainSplit.SashPercent:
			self._sashPct = self.mainSplit.SashPercent


	def setInitialSizing(self):
		"""Called to fit the prop sheet to the form"""
		self.propGrid.autoSizeCol(0)
		# Give it a little extra
		self.propGrid.Columns[0].Width += 25
		self.sizeGrid(True)
		dabo.ui.callAfter(self.setPanels)


	def onResize(self, evt):
		"""Size the value column to fit the panel"""
		dabo.ui.callAfter(self.sizeGrid)


	def sizeGrid(self, initial=False):
		try:
			pg = self.propGrid
		except dabo.ui.deadObjectException:
			return
		# Grid has already been resized by the sizer;
		# adjust the columns if needed
		col1 = pg.Columns[1]
		col1Allot = pg.Parent.Width - pg.Columns[0].Width - 20
		if initial or (col1.Width > col1Allot):
			col1.Width = col1Allot


	def onSash2Click(self, evt):
		"""Prevent the splitter from closing."""
		evt.stop()


	def select(self, obj):
		"""Called when the selected object changes. 'obj' will
		be a list containing either a single object or multiple
		objects. We need to query those objects for their editable
		properties, and if there are multiple objects, limit the
		editing to only those props that are common to all of
		the selection.
		"""
		if not isinstance(obj, (list, tuple)):
			obj = [obj]
		# Move the selected cell of the grid to the property column.
		self.propGrid.selectPropColumn()
		self._selected = obj
		if len(obj) == 0:
			# Nothing selected
			propDict = {}
		else:
			ob = obj[0]
			# If the selected object is an empty sizer slot, the way that this
			# is passed along is a tuple containing the sizer item and its sizer,
			# since there is no way to determine the sizer given the SizerItem.
			isSpacer = isinstance(ob, LayoutSpacerPanel)
			isSlot = isinstance(ob, LayoutPanel) and not isSpacer
			isSizer = isinstance(ob, dabo.ui.dSizer)
			propDict = None
			if isSlot or isSpacer:
				szItem = ob.ControllingSizerItem
				sz = ob.ControllingSizer
				propDict = sz.ItemDesignerProps
				if isSpacer:
					propDict.update(ob.DesignerProps)
			elif isSizer:
				sz = ob
			if propDict is None:
				propDict = ob.DesignerProps
			obRest = obj[1:]

		# Copy it to the grid
		self.updatePropGrid(propDict)


	def updatePropGrid(self, propDict=None):
		if propDict is None:
			obj = self._selected[0]
			if not obj:
				return
			propDict = obj.DesignerProps
		pg = self.propGrid
		pg.propDict = propDict
		ds = self.dataSetFromPropDict(propDict)
		if ds != pg.DataSet:
			# The dataset has changed, so update the grid:
			pg.DataSet = ds


	def dataSetFromPropDict(self, propDict):
		props = propDict.keys()
		if self.propGrid.sortOrder == "DESC":
			props = sorted(props, reverse=True)
		else:
			props = sorted(props)
		obj = self._selected
		mult = len(obj) > 1
		ds = []
		if len(obj) > 0:
			ob = obj[0]
			# If the selected object is an empty sizer slot, the way that this
			# is passed along is a tuple containing the sizer item and its sizer,
			# since there is no way to determine the sizer given the SizerItem.
			isSpacer = isinstance(ob, LayoutSpacerPanel)
			isSlot = isinstance(ob, LayoutPanel) and not isSpacer
			isSizer = isinstance(ob, dabo.ui.dSizer)
			if isSlot or isSpacer:
				szItem = ob.ControllingSizerItem
				sz = ob.ControllingSizer
			if isSizer:
				sz = ob
			obRest = obj[1:]
			# This dict holds all common props among the remaining
			# objects. If they all share a value, that value will be set;
			# otherwise, the value will be None.
			restDict = {}
			restProps = []

			if not mult:
				restDict = propDict
				restProps = props
			else:
				for indiv in obRest:
					if isinstance(indiv, LayoutPanel):
						szItem = indiv.ControllingSizerItem
						sz = indiv.ControllingSizer
						indivDict = sz.ItemDesignerProps
						indivProps = indivDict.keys()
					else:
						indivDict = indiv.DesignerProps
						indivProps = indivDict.keys()

					badProps = []
					for prop in props:
						if prop not in indivProps:
							badProps.append(prop)
							continue
						if prop in restProps:
							# already added; make sure the values are in sync
							rp = restProps[prop]
							rp["readonly"] = rp["readonly"] and indivDict[prop]["readonly"]
							# If the value is already None, no need to test
							if rp["val"] is None:
								continue
							if isinstance(indiv, LayoutPanel):
								nextVal = indiv.ControllingSizer.getItemProp(indiv.ControllingSizerItem, prop)
							else:
								nextVal = self.getObjPropVal(indiv, prop)
							if not rp["val"] == nextVal:
								rp["val"] = None
						else:
							restDict[prop] = {}
							rp = restDict[prop]
							rp["readonly"] = indivDict[prop]["readonly"]
							if isinstance(indiv, LayoutPanel):
								rp["val"] = indiv.ControllingSizer.getItemProp(indiv.ControllingSizerItem, prop)
							else:
								rp["val"] = self.getObjPropVal(indiv, prop)

					# Remove all non-common props
					props = [pp for pp in props
						if pp not in badProps]

			if len(props) == 0:
				ds = [{"prop" : "", "val" : "", "type" : sixUnicode, "readonly" : True}]
			else:
				# Construct the data set from the props
				ds = []
				for prop in props:
					propInfo = propDict[prop]
					rec = {}
					rec["prop"] = prop
					if isSlot:
						val = sz.getItemProp(szItem, prop)
					elif isSpacer:
						# Can be either the item props or its own
						try:
							val = self.getObjPropVal(ob, prop)
						except:
							val = sz.getItemProp(szItem, prop)
					elif prop == "Font":
						val = ob.FontDescription
					elif prop == "HeaderFont":
						val = ob.HeaderFontDescription
					else:
						val = self.getObjPropVal(ob, prop)
					rec["val"] = val
					rec["type"] = propInfo["type"]
					ro = propInfo["readonly"]
					if callable(ro):
						ro = ro(ob)
					rec["readonly"] = ro

					if mult:
						# Make sure that all the other objects share the values.
						rp = restDict[prop]
						if rp["val"] is None or (rp["val"] != rec["val"]):
							rec["val"] = None
						rec["readonly"] = rec["readonly"] and rp["readonly"]
					ds.append(rec)
		return ds


	def getObjPropDoc(self, obj, prop):
		"""Return the docstring for the passed property."""
		if isinstance(obj, (LayoutSpacerPanel, LayoutPanel)):
			obj = obj.ControllingSizer
			prop = "Sizer_%s" % prop
		try:
			doc = getattr(obj.__class__, prop).__doc__
		except AttributeError:
			try:
				doc = self.Controller.getPropDictForObject(obj)[prop]["comment"]
			except (AttributeError, KeyError, IndexError):
				doc = ""
		if doc is None:
			doc = ""
		return self.formatDocString(doc)


	def formatDocString(self, doc):
		doc = pydoc.splitdoc(doc)
		bodylines = doc[1].splitlines()
		body = ""
		for idx, line in enumerate(bodylines):
			if len(line) == 0:
				body += "\n"
			body += line.strip() + " "
		ret = "%s\n\n%s" % (doc[0], body)
		return ret.strip()


	def getObjPropVal(self, obj, prop):
		"""Subclasses (ie the report designer) can override."""
		ret = None
		if hasattr(obj, prop):
			ret = eval("obj.%s" % prop)
		else:
			# Custom-defined property
			propDict = self.Controller.getPropDictForObject(obj)
			if propDict:
				ret = propDict[prop]["defaultValue"]
		return ret


	def updateVal(self, prop, val, typ):
		"""Called from the grid to notify that the current cell's
		value has been changed. Update the corresponding
		property value.
		"""
		try:
			self.Controller.updatePropVal(prop, val, typ)
			if prop.startswith("Font"):
				self.updateGridValues()
		except PropertyUpdateException as e:
			dabo.ui.stop(_("Could not set property '%(prop)s' to value '%(val)s'\nReason: '%(e)s'")
					% locals())
			self.updateGridValues()


	def updateGridValues(self):
		"""Updates all the cells in the Value column.
		NOTE: only works with single-selection for now. Code to handle
		multiple selections still needs to be written.
		"""
		pg = self.propGrid
		ob = self._selected[0]
		for row in xrange(pg.RowCount):
			prop = pg.getValue(row, 0)
			if prop == "Font":
				val = ob.FontDescription
			else:
				val = eval("ob.%s" % prop)
			pg.setValue(row, 1, val)


	def setCustomEditor(self, ed, propName):
		if isinstance(ed, sixBasestring):
			# it is the name of a method in this class
			ed = eval("self.%s" % ed)
		self._custEditor = ed
		self.btnEdit.Caption = _("Edit %s") % propName
		self.btnEdit.Visible = (ed is not None)
		self.layout()


	def onBtnEdit(self, evt):
		ed = self._custEditor
		if ed is not None:
			# Pass the selected object(s), and the prop being edited
			pg = self.propGrid
			ed(self._selected, pg.CurrentProperty, pg.CurrentValue)


	def gridCellChanged(self):
		pg = self.propGrid
		obj = self._selected
		if obj:
			obj = self._selected[0]
			prop = pg.CurrentProperty
			self.edtPropDoc.Value = self.getObjPropDoc(obj, prop)


	##############################
	#  Custom property editor methods
	##############################
	def editColor(self, objs, prop, val):
		# Call the Color dialog
		obj = objs[0]
		newVal = dabo.ui.getColor(val)
		if newVal is not None:
			self.propGrid.CurrentValue = newVal
			self.updateVal(prop, newVal, "color")
			self.propGrid.refresh()


	def editFont(self, objs, prop, val):
		# Call the Font selection dialog
		obj = objs[0]
		newVal = dabo.ui.getFont(obj.Font)
		if newVal is not None:
			self.updateVal(prop, newVal, "font")
			self.select(self._selected)


	def editHeaderFont(self, objs, prop, val):
		# Call the Font selection dialog
		obj = objs[0]
		newVal = dabo.ui.getFont(obj.HeaderFont)
		if newVal is not None:
			self.updateVal(prop, newVal, "font")
			self.select(self._selected)


	def editPicture(self, objs, prop, val):
		# Select an image file to display
		obj = objs[0]
		newVal = dabo.ui.getFile("jpg", "png", "gif", "tif", "bmp", "*")
		if newVal is not None:
			self.propGrid.CurrentValue = newVal
			self.updateVal(prop, newVal, sixUnicode)
			self.propGrid.refresh()


	def editStdPicture(self, objs, prop, val):
		"""Give the option of selecting a standard image, or picking
		an image file.
		"""
		defIcons = dabo.icons.getAvailableIcons()

		class IconSelectDialog(dabo.ui.dDialog):
			def addControls(self):
				self.useStandard = True
				self.Caption = _("Select a Picture")
				sz = self.Sizer
				sz.appendSpacer(20)
				sz.DefaultSpacing = 10
				sz.DefaultBorder = 20
				sz.DefaultBorderLeft = sz.DefaultBorderRight = True
				btn = dabo.ui.dButton(self, Caption=_("Select your own image..."))
				btn.bindEvent(dEvents.Hit, self.onSelectOwn)
				sz.append(btn, halign="center")
				sz.append(dabo.ui.dLine(self), border=25, borderSides=("left", "right"))
				sz.append(dabo.ui.dLabel(self, Caption="- or -"), halign="center")
				lbl = dabo.ui.dLabel(self, Caption=_("Select a standard image:"))
				dd = dabo.ui.dDropdownList(self, RegID="ddIcons", Choices=defIcons,
						OnHit=self.updImage)
				hsz = dabo.ui.dSizer("h")
				hsz.append(lbl)
				hsz.appendSpacer(5)
				hsz.append(dd)
				sz.append(hsz, halign="center", border=16)
				hsz = dabo.ui.dSizer("h")
				img = dabo.ui.dImage(self, Picture="", Size=(64, 64), RegID="img")
				bsz = dabo.ui.dBorderSizer(self)
				bsz.append(img, border=8, halign="center", valign="middle")
				hsz.append(bsz)
				hsz.appendSpacer(16)
				btn = dabo.ui.dButton(self, Caption=_("Select"), OnHit=self.onSelect)
				hsz.append(btn, valign="middle")
				sz.append(hsz, halign="center")
				sz.append(dabo.ui.dLine(self), border=25, borderSides=("left", "right"))
				btn = dabo.ui.dButton(self, Caption=_("Cancel"), OnHit=self.onCancel)
				sz.append(btn, halign="right", border=20, borderSides=("right",))
				sz.appendSpacer(25)
				self._selected = False

			def onSelect(self, evt):
				self._selected = True
				self.hide()

			def onCancel(self, evt):
				self.hide()

			def onSelectOwn(self, evt):
				self.useStandard = False
				self.hide()

			def updImage(self, evt=None):
				pic = self.ddIcons.StringValue
				self.img.Picture = pic
				origW, origH = self.img.getOriginalImgSize()
				if (origW <= self.img.Width) and (origH <= self.img.Height):
					self.img.ScaleMode = "clip"
				else:
					self.img.ScaleMode = "proportional"

			def getSelectedIcon(self):
				if self._selected:
					return self.ddIcons.StringValue
				else:
					return None

			def setCurrent(self, strval):
				try:
					self.ddIcons.StringValue = strval
					self.updImage()
				except ValueError:
					# Not the name of a std. icon; default to first
					self.ddIcons.PositionValue = 0

		dlg = IconSelectDialog(None)
		currPic = eval("objs[0].%s" % prop)
		dlg.setCurrent(currPic)
		dlg.show()
		if not dlg:
			# User clicked the close button
			return
		if dlg.useStandard:
			newVal = dlg.getSelectedIcon()
			if newVal is not None:
				self.propGrid.CurrentValue = newVal
				self.updateVal(prop, newVal, sixUnicode)
				self.propGrid.refresh()
		else:
			self.editPicture(objs, prop, val)
		dlg.release()


	def editMenuBarFile(self, objs, prop, val):
		# Select a connection file
		obj = objs[0]
		newVal = dabo.ui.getFile("mnxml", "*")
		if newVal is not None:
			self.propGrid.CurrentValue = newVal
			self.updateVal(prop, newVal, sixUnicode)
			self.propGrid.refresh()


	def editChoice(self, objs, prop, val=[]):
		# Create a list of choices. 'val' may be a list of existing choices
		obj = objs[0]
		class ChoiceDialog(dabo.ui.dOkCancelDialog):
			def addControls(self):
				self.editor = dabo.ui.dEditableList(self, Choices=val,
						Caption=_("Editing choices for '%s'") % prop)
				self.Sizer.append1x(self.editor)

		dlg = ChoiceDialog(self, Modal=True)
		dlg.show()
		if dlg.Accepted:
			newVal = dlg.editor.Choices
			self.propGrid.CurrentValue = newVal
			self.updateVal(prop, newVal, list)
			self.propGrid.refresh()
		dlg.release()


	def editKeys(self, objs, prop, val=[]):
		# Create a list of keys. 'val' may be a list of existing keys
		obj = objs[0]
		class KeysDialog(dabo.ui.dOkCancelDialog):
			def addControls(self):
				self.editor = dabo.ui.dEditableList(self, Choices=val,
						Caption=_("Editing keys for '%s'") % prop)
				self.Sizer.append1x(self.editor)

		dlg = KeysDialog(self, Modal=True)
		dlg.show()
		if dlg.Accepted:
			newVal = dlg.editor.Choices
			self.propGrid.CurrentValue = newVal
			self.updateVal(prop, newVal, list)
			self.propGrid.refresh()
		dlg.release()


	def editBorderSides(self, objs, prop, val=[]):
		# Select one or more border sides from a list of choices.
		obj = objs[0]
		class MultiListDialog(dabo.ui.dOkCancelDialog):
			def addControls(self):
				self.Caption = _("Border Sides")
				lbl = dabo.ui.dLabel(self,
						Caption=_("Select the sides to which the border will apply:"))
				self.Sizer.append(lbl, halign="center")
				choices = ["All", "Top", "Bottom", "Left", "Right", "None"]
				self.editor = dabo.ui.dCheckList(self, Choices=choices,
						ValueMode="String", Height=200)
				self.editor.bindEvent(dEvents.Hit, self.onSidesChanged)
				self.editor.Value = self._currVal = val
				self.Sizer.append1x(self.editor)

			def onSidesChanged(self, evt):
				newVal = list(self.editor.Value)
				if "All" in newVal:
					if "All" in self._currVal:
						# They added a different choice
						newVal.remove("All")
					else:
						# They just clicked all; clear the rest
						newVal = ["All"]
				elif "None" in newVal:
					if "None" in self._currVal:
						# They added a different choice
						newVal.remove("None")
					else:
						# They just clicked None; clear the rest
						newVal = ["None"]
				self.editor.Value = self._currVal = newVal
				self.editor.refresh()

		dlg = MultiListDialog(self, Modal=True)
		dlg.show()
		if dlg.Accepted:
			newVal = dlg.editor.Value
			if "All" in newVal:
				newVal = ["All"]
			elif "None" in newVal:
				newVal = ["None"]
			self.propGrid.CurrentValue = newVal
			self.updateVal(prop, newVal, list)
			self.propGrid.refresh()
		dlg.release()


	def editHotKey(self, objs, prop, val):
		obj = objs[0]
		from dabo.ui.dialogs.HotKeyEditor import HotKeyEditor
		dlg = HotKeyEditor(self)
		dlg.setKey(obj.HotKey)
		dlg.Centered = True
		dlg.show()
		if dlg.Accepted and dlg.Changed:
			keyText = dlg.KeyText
			if keyText is None:
				keyText = ""
			# Setting the HotKey prop should update the related sub-props.
			obj.HotKey = keyText
			self.updateVal(prop, keyText, sixUnicode)
			self.propGrid.CurrentValue = keyText
			self.propGrid.refresh()
		dlg.release()


	def _getController(self):
		try:
			return self._controller
		except AttributeError:
			self._controller = self.Application
			return self._controller

	def _setController(self, val):
		if self._constructed():
			self._controller = val
		else:
			self._properties["Controller"] = val


	Controller = property(_getController, _setController, None,
			_("Object to which this one reports events  (object (varies))"))



class PropertyGrid(dabo.ui.dGrid):
	def initProperties(self):
		self.SelectionMode = "Row"
		self.MultipleSelection = False
		self.RowColorEven = "papayawhip"
		self.RowColorOdd = "white"
		self.AlternateRowColoring = True


	def afterInit(self):
		self._handler = None
		self.HeaderHeight = 20

		self.propDict = {}
		self.useCustomGetValue = self.useCustomSetValue = True
		self.Editable = True
		self.ActivateEditorOnSelect = False

		# Create the property name column
		col = dabo.ui.dColumn(self, Order=10, DataField="prop",
				DataType="string", Width=100, Caption=_("Property"), Sortable=True,
				Searchable=True, Editable=False)
		self.addColumn(col, inBatch=True)

		# Now create the property Value column
		col = dabo.ui.dColumn(self, Order=20, DataField="val",
				DataType="string", Width=200, Caption=_("Value"), Sortable=False,
				Searchable=False, Editable=True)
		self.addColumn(col, inBatch=True)
		self.autoBindEvents()

		# Set the font size for each platform
		c0 = self.Columns[0]
		fsize = c0.FontSize
		if self.Application.Platform == "Win":
			self.setAll("FontSize", fsize-2, filt="BaseClass == dabo.ui.dColumn")
		# Set the row height to match
		face = c0.FontFace
		size = c0.FontSize
		bold = c0.FontBold
		italic = c0.FontItalic
		rh  = dabo.ui.fontMetric("M", wind=self.Form, face=face, size=size,
				bold=bold, italic=italic)[1] + 7
		if 0 < rh < 999:
			# Make sure that these are sane values
			self.RowHeight = rh
		# Reference to default classes. Don't know if this is the best solution...
		self.stringRendererClass = col.stringRendererClass
		self.boolRendererClass = col.boolRendererClass
		self.intRendererClass = col.intRendererClass
		self.longRendererClass = col.longRendererClass
		self.decimalRendererClass = col.decimalRendererClass
		self.floatRendererClass = col.floatRendererClass
		self.listRendererClass = col.listRendererClass
		self.stringEditorClass = col.stringEditorClass
		self.boolEditorClass = col.boolEditorClass
		self.intEditorClass = col.intEditorClass
		self.longEditorClass = col.longEditorClass
		self.decimalEditorClass = col.decimalEditorClass
		self.floatEditorClass = col.floatEditorClass
		self.listEditorClass = col.listEditorClass


	def getPropDictForRow(self, row):
		if not self.RowCount:
			return None
		prop = self.getValue(row, 0)
		if not prop:
			return None
		try:
			return self.propDict[prop]
		except KeyError as e:
			return None
# 			print "PROP DICT ERROR: >%s<, row=%s" % (prop, row)


	def fillGrid(self, force=False):
		super(PropertyGrid, self).fillGrid(force)
		self.refresh()
		# Set the renderers and editors manually by cell
		if not self.Controller.Selection:
			return
		valColumn = self.Columns[1]
		for row in xrange(self.RowCount):
			pd = self.getPropDictForRow(row)
			if pd is None:
				if row == 0 and self.getValue(row, 0) == "":
					# skip the below errorLog entry for ReportDesigner
					pass
				else:
					dabo.log.error(_("Property Grid out of sync for property '%s' of object '%'") %
							(self.getValue(row, 0), self.Controller.Selection[0]))
				continue
			if not isinstance(pd, dict):
				print(_("BAD PROP DICT:"), pd, type(pd), _("ROW"), row)
				continue
			typ = pd["type"]
			rnd = self.stringRendererClass
			if typ is list:
				ed = self.listEditorClass
				# Need to set the particular choices for this row
				valColumn.CustomListEditorChoices[row] =  pd["values"]
			elif typ is int:
				ed = self.intEditorClass
				rnd = self.intRendererClass
			elif typ is float:
				ed = self.floatEditorClass
				rnd = self.floatRendererClass
			elif typ is bool:
				ed = self.boolEditorClass
				rnd = self.boolRendererClass
			else:
				ed = self.stringEditorClass
			valColumn.CustomEditors[row] = ed
			valColumn.CustomRenderers[row] = rnd
		self.updateGridDisplay()


	def customCanGetValueAs(self, row, col, typ):
		ret = True
		if col == 0:
			ret = typ in ("str", "string", "unicode", "u")
		else:
			if not self.Controller.Selection:
				return type(None)
			pd = self.getPropDictForRow(row)

			if not isinstance(pd, dict):
				if pd is not None:
					print(_("BAD PROP DICT:"), pd, type(pd), _("ROW="), row)
			else:
				if pd["type"] == "multi":
					# This is a catch-all setting for props such as 'Value' that
					# can have any number of types.
					ret = True
				else:
					typtyp = {"str" : str, "unicode" : str, "bool" : bool, "int" : int, "long" : int,
							"szinfo" : str, "double" : float}[typ]
					ret = pd["type"] == typtyp
		return ret


	def customCanSetValueAs(self, row, col, typ):
		if col == 0:
			return isinstance(typ, sixBasestring)
		else:
			pd = self.getPropDictForRow(row)
			if pd["type"] == "multi":
				# This is a catch-all setting for props such as 'Value' that
				# can have any number of types.
				return True
			else:
				typtyp = {"str" : str, "unicode" : str, "bool" : bool, "int" : int, "long" : int,
						"double" : float}[typ]
				return pd["type"] == typtyp


	def selectPropColumn(self):
		"""Move the selected cell to the prop column."""
		if self.CurrentColumn is 1:
			self.CurrentColumn = 0


	def onGridCellEditBegin(self, evt):
		# Save the pre-editing value so we only update
		# if it changes.
		self.Controller.startPropEdit()
		self._origVal = self.getValue(evt.row, evt.col)


	def onGridCellSelected(self, evt):
		row, col = evt.EventData["row"], evt.EventData["col"]
		self.updateGridDisplay(row, col)
		if self.Handler:
			dabo.ui.callAfter(self.Handler.gridCellChanged)


	def updateGridDisplay(self, row=None, col=None):
		if row is None:
			row = self.CurrentRow
		if col is None:
			col = self.CurrentColumn
		try:
			sel = self.Controller.Selection
		except AttributeError:
			# App doesn't support this property yet
			sel = None
		if not sel:
			self.CurrentRow = self.CurrentColumn = 0
			return
		pd = self.getPropDictForRow(row)
		if pd is None:
			return
		if col == 1:
			# Only the second column is directly editable, and only
			# if the property permits editing.
			isRO = pd["readonly"]
			if callable(isRO):
				isRO = isRO(sel[0])
			self.Editable = not isRO
		else:
			self.Editable = False

		custEditor = pd.get("customEditor")
		if custEditor is not None:
			if not pd.get("alsoDirectEdit", False):
				self.Editable = False

		# Tell the Handler how to handle any custom edits
		self.Handler.setCustomEditor(custEditor, self.getValue(row, 0))
		if not getattr(self.Handler.Controller, "isClosing", False):
			if self.Editable:
				# For some reason, this doesn't seem to work...
				dabo.ui.callAfter(self.EnableCellEditControl)
			else:
				dabo.ui.callAfter(self.DisableCellEditControl)


	def onGridCellEdited(self, evt):
		row, col = evt.EventData["row"], evt.EventData["col"]
		newVal = self.getValue(row, col)
		if newVal != self._origVal:
			prop = self.getValue(row, 0)
			pd = self.getPropDictForRow(row)
			typ = pd["type"]
			self.Handler.updateVal(prop, newVal, typ)


	def onGridCellEditEnd(self, evt):
		self.Controller.endPropEdit()


	def _getController(self):
		try:
			return self._controller
		except AttributeError:
			self._controller = self.Form.Controller
			return self._controller

	def _setController(self, val):
		if self._constructed():
			self._controller = val
		else:
			self._properties["Controller"] = val


	def _getCurrProp(self):
		return self.getValue(self.CurrentRow, 0)


	def _getCurrVal(self):
		return self.getValue(self.CurrentRow, 1)

	def _setCurrVal(self, val):
		self.setValue(self.CurrentRow, 1, val)


	def _getHandler(self):
		return self._handler

	def _setHandler(self, val):
		self._handler = val


	Controller = property(_getController, _setController, None,
			_("Object to which this one reports events  (object (varies))"))

	CurrentProperty = property(_getCurrProp, None, None,
			_("Name of currently selected property  (string)") )

	CurrentValue = property(_getCurrVal, _setCurrVal, None,
			_("Value of currently selected property  (varies)") )

	Handler = property(_getHandler, _setHandler, None,
			_("Target object to handle events for this grid  (PropSheet)"))



if __name__ == "__main__":
	pass
