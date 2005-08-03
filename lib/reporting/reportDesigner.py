import sys, os, copy
import dabo, dabo.ui
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.lib.reporting_old.reportWriter import ReportWriter


#------------------------------------------------------------------------------
#  ObjectPanel Class
# 
class ObjectPanel(dabo.ui.dPanel):
	"""Base class for all report objects
	
	All of the various types of report objects like strings, images, rectangles,
	etc. are ObjectPanels. ObjectPanels get instantiated from the Band's 
	getObject() method.
	"""
	def afterInit(self):
		self._rd = self.Form.editor
		self._rw = self._rd._rw
		self._props = {}
		self._anchors = {}

	def initEvents(self):
		self.bindEvent(dEvents.Paint, self.onPaint)
		self.bindEvent(dEvents.MouseLeftClick, self.onLeftClick)
		self.bindEvent(dEvents.MouseLeftDoubleClick, self.onDoubleClick)
		self.bindEvent(dEvents.MouseMove, self.onMouseMove)
		self.bindEvent(dEvents.MouseEnter, self.onMouseEnter)
		self.bindEvent(dEvents.MouseLeave, self.onMouseLeave)

	def getProp(self, prop, evaluate=True):
		try:
			val = self.Props[prop]
		except KeyError:
			val = None

		if evaluate and val is not None and prop not in ("type",):
			try:
				vale = eval(val)
			except:
				vale = "?: %s" % str(val)
		else:
			vale = val
		return vale

	def setProp(self, prop, val, sendPropsChanged=True):
		"""Set the specified object property to the specified value.

		If setting more than one property, self.setProps() is faster.
		"""
		self.Props[prop] = str(val)
		if sendPropsChanged:
			self._rd.propsChanged(redraw=False)
			self.draw()
			self.Refresh()

	def setProps(self, propvaldict):
		"""Set the specified object properties to the specified values."""
		for p,v in propvaldict.items():
			self.setProp(p, v, False)
		self.draw()

	def draw(self):
		self.Parent.drawObject(self.Props)

	def onDoubleClick(self, evt):
		self.Parent._rd.propertyDialog(self)

	def onMouseLeave(self, evt):
		import wx
		self.SetCursor(wx.NullCursor)	

	def onMouseEnter(self, evt):
		self._setMouseCursor(evt.EventData["mousePosition"])

	def onMouseMove(self, evt):
		self._setMouseCursor(evt.EventData["mousePosition"])

	def _setMouseCursor(self, pos):
		import wx
		if self.Selected:
			if self._mouseOnAnchor(pos):
				self.SetCursor(wx.StockCursor(wx.CURSOR_SIZING))
			else:
				self.SetCursor(wx.StockCursor(wx.CURSOR_SIZENWSE))
		else:
			self.SetCursor(wx.NullCursor)					

	def _mouseOnAnchor(self, pos):
		retval = False
		for v in self._anchors.values():
			vv = []
			for x in range(self._anchorThickness):
				for y in range(self._anchorThickness):
					vv.append((v[2]+x,v[3]+y))						
			if pos in vv:
				retval = True
				break
		return retval

	def onLeftClick(self, evt):
		if not self.Selected:
			if evt.EventData["shiftDown"] or evt.EventData["controlDown"]:
				self._rd._selectedObjects.append(self)
			else:
				oldSelectedObjects = copy.copy(self._rd._selectedObjects)
				self._rd._selectedObjects = [self,]
				for obj in oldSelectedObjects:
					obj.Refresh()
		else:
			if evt.EventData["shiftDown"] or evt.EventData["controlDown"]:
				for idx in range(len(self._rd._selectedObjects)):
					if self._rd._selectedObjects[idx] == self:
						del self._rd._selectedObjects[idx]
						break
		self.Refresh()

	def onPaint(self, evt):
		import wx		## (need to abstract DC drawing)
		dc = wx.PaintDC(self)
		rect = self.GetClientRect()
		dc.SetBrush(wx.Brush(self.BackColor, wx.SOLID))
		if self.Selected:
			# border around selected control with sizer boxes:
			dc.DrawRectangle(rect[0]+1,rect[1]+1,rect[2]-2,rect[3]-2)
			dc.SetBrush(wx.Brush(self.ForeColor, wx.SOLID))

			x,y = (rect[0], rect[1])
			width, height = (rect[2], rect[3])
			thickness = 3

			if self.Props.has_key("hAnchor"):
				hAnchor = eval(self.Props["hAnchor"])
			else:
				hAnchor = self._rw.default_hAnchor

			if self.Props.has_key("vAnchor"):
				vAnchor = eval(self.Props["vAnchor"])
			else:
				vAnchor = self._rw.default_vAnchor

			anchors = {"tl": ["top", "left", x, y],
				    "bl": ["bottom", "left", x, y + height - thickness],
				    "tc": ["top", "center", x+(.5*width), y],
				    "bc": ["bottom", "center", x+(.5*width), y+height-thickness],
				    "tr": ["top", "right", x+width-thickness, y],
				    "br": ["bottom", "right", x+width-thickness, y+height-thickness],}

			self._anchors = anchors
			self._anchorThickness = thickness

			pen = dc.GetPen()

			for k,v in anchors.items():
				if hAnchor == v[1] and vAnchor == v[0]:
					dc.SetBrush(wx.Brush((192,0,192), wx.SOLID))
					dc.SetPen(wx.Pen((192,0,192)))
				else:
					dc.SetBrush(wx.Brush(self.ForeColor, wx.SOLID))
					dc.SetPen(pen)
				dc.DrawRectangle(v[2], v[3], thickness, thickness)
		else:
			# border around unselected control
			dc.DrawRectangle(rect[0],rect[1],rect[2],rect[3])

		if self.getProp("type") == "string":
			expr = self.getProp("expr", evaluate=False)
			if expr is None:
				expr = "<< missing expression >>"

			alignments = {"left": wx.ALIGN_LEFT,
					"center": wx.ALIGN_CENTER,
					"right": wx.ALIGN_RIGHT,}

			alignment = self.getProp("align")
			if alignment is None:
				alignment = self._rw.default_align
			dc.DrawLabel(expr, (rect[0]+2, rect[1], rect[2]-4, rect[3]),
				      alignments[alignment])

	def _getSelected(self):
		return self in self._rd._selectedObjects
	
	def _setSelected(self, val):
		if val:
			self._rd._selectedObjects.append(self)
		else:
			for idx in range(len(self._rd._selectedObjects)):
				if self._rd._selectedObjects[idx] == self:
					del self._rd._selectedObjects[idx]
					break
		self.Refresh
			
	def _getProps(self):
		return self._props

	def _setProps(self, val):
		self._props = val
		self.availableProps = [{"name": "x", "caption": "x", 
		                        "defaultValue": self._rw.default_x},
		                       {"name": "y", "caption": "y",
		                        "defaultValue": self._rw.default_y},
		                       {"name": "width", "caption": "Width",
		                        "defaultValue": self._rw.default_width},
		                       {"name": "height", "caption": "Height",
		                        "defaultValue": self._rw.default_height},
		                       {"name": "hAnchor", "caption": "Horizontal Anchor",
		                        "defaultValue": '"%s"' % self._rw.default_hAnchor},
		                       {"name": "vAnchor", "caption": "Vertical Anchor",
		                        "defaultValue": '"%s"' % self._rw.default_vAnchor},
		                       {"name": "rotation", "caption": "Rotation",
		                        "defaultValue": self._rw.default_rotation},]

		if val["type"] == "string":
			self.availableProps.insert(0, {"name": "expr", "caption": "Expression",
			                               "defaultValue": self._rw.default_expr})

	Props = property(_getProps, _setProps)
	Selected = property(_getSelected)

#  End of ObjectPanel Class
#
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
#  BandLabel Class
# 
class BandLabel(dabo.ui.dPanel):
	"""Base class for the movable label at the bottom of each band.
	
	These are the bands like pageHeader, pageFooter, and detail that
	the user can drag up and down to make the band smaller or larger,
	respectively.
	"""
	def afterInit(self):
		self._dragging = False
		self._dragStart = (0,0)
		self._dragImage = None


	def initEvents(self):
		self.bindEvent(dEvents.Paint, self.onPaint)
		self.bindEvent(dEvents.MouseLeftDown, self.onLeftDown)
		self.bindEvent(dEvents.MouseLeftUp, self.onLeftUp)
		self.bindEvent(dEvents.MouseLeftDoubleClick, self.onDoubleClick)
		self.bindEvent(dEvents.MouseEnter, self.onMouseEnter)
		self.bindEvent(dEvents.MouseMove, self.onMouseMove)


	def onMouseMove(self, evt):
		import wx  ## need to abstract DC and mouse cursors!!
		if self._dragging:
			self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
			pos = evt.EventData["mousePosition"]

			if pos[1] != self._dragStart[1]:
				ypos = (self.Parent.Top + self.Top + pos[1] 
				     - self._dragStart[1]    ## (correct for ypos in the band)
				     + 2)                    ## fudge factor


				if ypos < self.Parent.Top:
					# Don't show the band dragging above the topmost valid position:
					ypos = self.Parent.Top

				if self._dragImage is None:
					# Erase the band label, and instantiate the dragImage rendition of it.
					dc = wx.WindowDC(self)
					dc.Clear()

					self._dragImage = wx.DragImage(self._captureBitmap,
					                               wx.StockCursor(wx.CURSOR_HAND))

					self._dragImage.BeginDragBounded((self.Parent.Left, ypos), 
					                                 self, self.Parent.Parent)
					self._dragImage.Show()

				self._dragImage.Move((self.Parent.Left,ypos))



	def onLeftUp(self, evt):
		dragging = self._dragging
		self._dragging = False
		if dragging:
			if self._dragImage is not None:
				self._dragImage.EndDrag()
			self._dragImage = None
			pos = evt.EventData["mousePosition"]
			starty = self._dragStart[1]
			currenty = pos[1]
			yoffset = currenty - starty
			if yoffset != 0:
				z = self.Parent.Parent._zoom
				# dragging the band is changing the height of the band.
				oldHeight = self.Parent._rw.getPt(self.Parent.getProp("height"))
				newHeight = oldHeight + (yoffset/z)
				if newHeight < 0: newHeight = 0
				self.Parent.setProp("height", newHeight)
			self.Form.Refresh()

	def onLeftDown(self, evt):
		if self.Application.Platform == "Mac":
			# Mac needs the following line, or LeftUp will never fire. TODO:
			# figure out how to abstract this into dPemMixin (if possible).
			# I posted a message to wxPython-mac regarding this - not sure if
			# it is a bug or a "by design" platform inconsistency.
			evt.stop()
		if not self.Parent.getProp("designerLock"):
			self._dragging = True
			self._dragStart = evt.EventData["mousePosition"]
			self._captureBitmap = self.getCaptureBitmap()


	def onMouseEnter(self, evt):
		import wx		## need to abstract mouse cursor

		if self.Parent.getProp("designerLock"):
			self.SetCursor(wx.NullCursor)
		else:
			self.SetCursor(wx.StockCursor(wx.CURSOR_SIZENS))


	def onDoubleClick(self, evt):
		self.Parent._rd.propertyDialog(self.Parent)


	def onPaint(self, evt):
		import wx		## (need to abstract DC drawing)
		dc = wx.PaintDC(self)
		rect = self.GetClientRect()
		font = self.Font

		dc.SetTextForeground(self.ForeColor)
		dc.SetBrush(wx.Brush(self.BackColor, wx.SOLID))
		dc.SetFont(font)
		dc.DrawRectangle(rect[0],rect[1],rect[2],rect[3])
		rect[0] = rect[0]+5
		rect[1] = rect[1]+1
		dc.DrawLabel(self.Caption, rect, wx.ALIGN_LEFT)


	def _getCaption(self):
		try:
			c = self._caption
		except:
			c = self._caption = ""
		return c

	def _setCaption(self, val):
		self._caption = val

	Caption = property(_getCaption, _setCaption)

#  End BandLabel Class
#
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
#
#  Band Class
#
class Band(dabo.ui.dPanel):
	"""Base class for report bands.
	
	Bands contain any number of objects, which can receive the focus and be
	acted upon. Bands also manage their own BandLabels.
	"""
	def initProperties(self):
		self.BackColor = (255,255,255)
		self.Top = 100

	def afterInit(self):
		self._rd = self.Form.editor
		self._rw = self._rd._rw
		self.Bands = self._rw.Bands
		self._objects = {}

		self._bandLabelHeight = 18
		self.addObject(BandLabel, "bandLabel", FontSize=9, 
		               BackColor=(215,215,215), ForeColor=(128,128,128),
		               Height=self._bandLabelHeight)

		self.availableProps = [{"name": "height", 
		                        "defaultValue": self._rw.default_bandHeight,
		                        "caption": "Band Height"},
		                       {"name": "designerLock", 
		                        "defaultValue": "False",
		                        "caption": "Designer Lock"}]


	def initEvents(self):
		self.bindEvent(dEvents.MouseLeftClick, self.onLeftClick)


	def onLeftClick(self, evt):
		oldSelectedObjects = copy.copy(self._rd._selectedObjects)
		self._rd._selectedObjects = []
		for obj in oldSelectedObjects:
			obj.Refresh()


	def drawObjects(self):
		if self.props.has_key("objects"):
			for obj in self.props["objects"]:
				self.drawObject(obj)

	def drawObject(self, obj):
		self.getObject(obj)
	

	def getObject(self, obj):
		if not obj.has_key("name"):
			# The report designer needs to identify objects uniquely, and saves the
			# 'name' property to the object in the rfxml file. However, perhaps a 
			# separate builder or manual edit of the rfxml resulted in name not being
			# included. Generate it now:
			while True:
				name = self.Parent._rw._getUniqueName()
				if name not in self._objects.keys():
					break
			obj["name"] = name
			dabo.infoLog.write("Report object didn't have a name... assigned '%s'." % name)

		if obj["name"] not in self._objects.keys():
			o = ObjectPanel(self)
			self._objects[obj["name"]] = o
			o.Props = obj
		else:
			o = self._objects[obj["name"]]

		rw = self.Parent._rw
		z = self.Parent._zoom

		if obj.has_key("x"):
			x = rw.getPt(eval(obj["x"]))
		else:
			x = rw.default_x

		if obj.has_key("y"):
			y = rw.getPt(eval(obj["y"]))
		else:
			y = rw.default_y
		y = ((self.Height - self._bandLabelHeight)/z) - y

		if obj.has_key("width"):
			width = rw.getPt(eval(obj["width"]))
		else:
			width = rw.default_width

		if obj.has_key("height"):
			height = rw.getPt(eval(obj["height"]))
		else:
			height = rw.default_height

		if obj.has_key("hAnchor"):
			hAnchor = eval(obj["hAnchor"])
		else:
			hAnchor = rw.default_hAnchor

		if obj.has_key("vAnchor"):
			vAnchor = eval(obj["vAnchor"])
		else:
			vAnchor = rw.default_vAnchor

		if hAnchor == "right":
			x = x - width
		elif hAnchor == "center":
			x = x - (width/2)

		if vAnchor == "top":
			y = y + height
		elif vAnchor == "center":
			y = y + (height/2)

		o.Size = (z*width, z*height)
		o.Position = (z*x, (z*y) - o.Height)
		return o

	def getProp(self, prop, evaluate=True):
		try:
			val = self.props[prop]
		except KeyError:
			val = None

		if evaluate and val is not None and prop not in ("type",):
			try:
				vale = eval(val)
			except:
				vale = "?: %s" % str(val)
		else:
			vale = val
		return vale


	def setProp(self, prop, val, sendPropsChanged=True):
		"""Set the specified object property to the specified value.

		If setting more than one property, self.setProps() is faster.
		"""
		self.props[prop] = str(val)
		if sendPropsChanged:
			self.Parent.propsChanged()

	def setProps(self, propvaldict):
		"""Set the specified object properties to the specified values."""
		for p,v in propvaldict.items():
			self.setProp(p, v, False)
		self.Parent.propsChanged()


	def _getCaption(self):
		return self.bandLabel.Caption

	def _setCaption(self, val):
		self.bandLabel.Caption = val

	Caption = property(_getCaption, _setCaption)

#  End Band Class
#
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
#
#  ReportDesigner Class
#
class ReportDesigner(dabo.ui.dScrollPanel):
	"""Main report designer panel.
	
	This is the main report designer panel that contains the bands and
	handles setting properties on report objects. While a given object is
	considered to be owned by a particular band, the report designer still
	controls the placement of the object because, among other things, a given
	object can cross bands (a rectangle extending from the group header to the
	group footer, for instance) or move from one band to another.
	"""
	def afterInit(self):
		self._bands = []
		self._rulers = {}
		self._selectedObjects = []
		self._zoom = self._normalZoom = 1.3
		self.BackColor = (192,192,192)
		self.clearReportForm()

		self.Form.bindEvent(dEvents.Resize, self._onFormResize)
		self.bindEvent(dEvents.KeyDown, self._onKeyDown)
		self.bindEvent(dEvents.KeyUp, self._onKeyUp)

	def _onKeyDown(self, evt):
		# eat the arrow keys which will otherwise scroll the window.
		from dabo.ui import dKeys
		keyCode = evt.EventData["keyCode"]
		arrows = {dKeys.key_Up: "up",
		          dKeys.key_Down: "down", 
		          dKeys.key_Right: "right",
		          dKeys.key_Left: "left"}
		if arrows.has_key(keyCode):
			evt.stop()


	def _onKeyUp(self, evt):
		# Note: using onKeyUp because it appears something is eating KeyDown on 
		# Windows, perhaps the scrollPanel scrollbars.
		# certain keys, like the arrow keys, are used by the designer.
		from dabo.ui import dKeys
		shiftDown = evt.EventData["shiftDown"]
		ctrlDown = evt.EventData["controlDown"]	 # ? handled differently? (linux at least)
		keyCode = evt.EventData["keyCode"]
		keys = {dKeys.key_Up: "up",
		        dKeys.key_Down: "down", 
		        dKeys.key_Right: "right",
		        dKeys.key_Left: "left"}

		if keys.has_key(keyCode):
			key = keys[keyCode]
			if len(self._selectedObjects) > 0:
				evt.stop()  ## don't let the arrow key scroll the window
				size, turbo = False, False
				if shiftDown:
					if key in ["up", "down"]:
						propName = "height"
					else:
						propName = "width"
				else:
					if key in ["up", "down"]:
						propName = "y"
					else:
						propName = "x"
				
				if key in ["up", "right"]:
					adj = 1
				else:
					adj = -1
				
				if ctrlDown:
					adj = adj * 10
				
				for o in self._selectedObjects:
					val = o.getProp(propName)
					if val is None:
						val = eval("self._rw.default_%s" % propName)
					val = self._rw.getPt(val)
					o.setProp(propName, val+adj)
						

	def clearReportForm(self):
		"""Called from afterInit and closeFile to clear the report form."""
		for o in self._rulers.values():
			o.Destroy()
		self._rulers = {}
		for o in self._bands:
			o.Destroy()
		self._bands = []
		self._rw = ReportWriter()
		self.ReportForm = None


	def propertyDialog(self, obj=None):
		"""Display the property dialog for the passed object."""
		if obj is None:
			obj = self
		rw = self._rw

		class PropertyDialog(dabo.ui.dDialog):
			def addControls(self):
				for prop in obj.availableProps:
					propVal = obj.getProp(prop["name"], evaluate=False)
					if propVal is None:
						propVal = str(prop["defaultValue"])

					lbl = self.addObject(dabo.ui.dLabel, Name="lbl%s" % prop["name"], 
					                     Caption="%s:" % prop["caption"],
					                     Alignment="Right", Width=125)
					txt = self.addObject(dabo.ui.dTextBox, Name="txt%s" % prop["name"], 
					                     Width=300, Value=propVal)
			
					h = dabo.ui.dSizer("h")
					h.append(lbl, "fixed", alignment=("middle", "right"))
					h.append(txt, alignment=("middle", "right"), border=1)
					self.Sizer.append(h, border=1)

				self.addObject(dabo.ui.dButton, Name="cmdAccept", Caption="&Accept",
				               DefaultButton=True)
				self.addObject(dabo.ui.dButton, Name="cmdCancel", Caption="&Cancel",
				               CancelButton=True)

				self.cmdAccept.bindEvent(dEvents.Hit, self.onAccept)
				self.cmdCancel.bindEvent(dEvents.Hit, self.onCancel)
				self.bindKey("enter", self.onAccept)

				h = dabo.ui.dSizer("h")
				h.append(self.cmdAccept, border=5)
				h.append(self.cmdCancel, border=5)
				self.Sizer.append(h, border=5, alignment="right")

			def onAccept(self, evt):
				props = {}
				for prop in obj.availableProps:
					o = eval("self.txt%s" % prop["name"])
					props[prop["name"]] = o.Value
				obj.setProps(props)
				self.Visible = False

			def onCancel(self, evt):
				self.Visible = False


		caption = obj.Caption
		if len(caption.strip()) == 0:
			caption = obj.Props["name"]

		dlg = PropertyDialog(self.Form, 
		                     Caption="%s Properties" % caption)
		dlg.show()


	def promptToSave(self):
		"""Decides whether user should be prompted to save, and whether to save."""
		result = True
		if self._rw._isModified():
			result = dabo.ui.areYouSure("Save changes to file %s?" 
			                                        % self._fileName)
			if result:
				self.saveFile()
		return result


	def promptForFileName(self, prompt="Select a file"):
		"""Prompt the user for a file name."""
		import wx   ## need to abstract getFile()
		try:
			dir_ = self._curdir
		except:
			dir_ = ""
	
		dlg = wx.FileDialog(self, 
			message = prompt,
			defaultDir = dir_, 
			wildcard="Dabo Report Forms (*.rfxml)|*.rfxml|All Files (*)|*")

		if dlg.ShowModal() == wx.ID_OK:
			fname = dlg.GetPath()
		else:
			fname = None
		dlg.Destroy()
		return fname


	def promptForSaveAs(self):
		"""Prompt user for the filename to save the file as.
		
		If the file exists, confirm with the user that they really want to
		overwrite.
		"""
		while True:
			fname = self.promptForFileName(prompt="Save As")
			if fname is None:
				break
			if os.path.exists(fname):
				r = dabo.ui.areYouSure("File '%s' already exists. "
					"Do you want to overwrite it?" % fname, defaultNo=True)
					
				if r == None:
					# user canceled.
					fname = None
					break
				elif r == False:
					# let user pick another file
					pass
				else:
					# User chose to overwrite fname
					break
			else:
				break
		
		return fname


	def saveFile(self, fileSpec=None):
		if fileSpec == None:
			fileSpec = self._rw.ReportFormFile
			if fileSpec is None:
				fileSpec = self.promptForSaveAs()
				if fileSpec is None:
					return False
				else:
					self._fileName = fileSpec
		else:
			self._fileName = fileSpec
		xml = self._rw._getXMLFromForm(self._rw.ReportForm)
		file = open(fileSpec, "w")
		file.write(xml)
		file.close()
		self._rw._setMemento()
		self.setCaption()


	def closeFile(self):
		result = self.promptToSave()

		if result is not None:
			self._rw.ReportFormFile = None
			self.clearReportForm()
		return result


	def setCaption(self):
		"""Sets the form's caption based on file name, whether modified, etc."""
		if self._rw._isModified():
			modstr = "* "
		else:
			modstr = ""
		self.Form.Caption = "%s%s: %s" % (modstr,
		                                  self.Form._captionBase,
		                                  self._fileName)

	def newFile(self):
		if self.closeFile():
			self._rw.ReportForm = self._rw._getEmptyForm()
			self.initReportForm()
			self._fileName = "< New >"
			self.setCaption()

	def openFile(self, fileSpec):
		if os.path.exists(fileSpec):
			if self.closeFile():
				self._rw.ReportFormFile = fileSpec
				self.initReportForm()
				self._fileName = fileSpec
				self.setCaption()
		else:
			raise ValueError, "File %s does not exist." % fileSpec


	def initReportForm(self):
		"""Called from openFile and newFile when time to set up the Report Form."""
		self.ReportForm = self._rw.ReportForm
		self._rw.UseTestCursor = True
		self._rw.write()

		self._rulers = {}
		self._rulers["top"] = self.getRuler("h")
		self._rulers["bottom"] = self.getRuler("h")

		for band in ("pageHeader", "detail", "pageFooter"):
			if self.ReportForm.has_key(band):
				self._rulers["%s-left" % band] = self.getRuler("v")
				self._rulers["%s-right" % band] = self.getRuler("v")
				b = Band(self, Caption=band)
				b.props = self.ReportForm[band]
				b._rw = self._rw
				self._bands.append(b)

		self.drawReportForm()


	def propsChanged(self, redraw=True):
		"""Called by subobjects to notify the report designer that a prop has changed."""
		self.setCaption()
		if redraw:
			self.drawReportForm()
		
	def _onFormResize(self, evt):
		self.drawReportForm()

	def drawReportForm(self):
		"""Resize and position the bands accordingly."""
		rw = self._rw
		rf = self._rw.ReportForm
		z = self._zoom

		if rf is None:
			return

		pageWidth = rw.getPageSize()[0] * z
		ml = rw.getPt(eval(rf["page"]["marginLeft"])) * z
		mr = rw.getPt(eval(rf["page"]["marginRight"])) * z
		mt = rw.getPt(eval(rf["page"]["marginTop"])) * z
		mb = rw.getPt(eval(rf["page"]["marginBottom"])) * z
		bandWidth = pageWidth - ml - mr

		tr = self._rulers["top"]
		tr.Length = pageWidth

		for index in range(len(self._bands)):
			band = self._bands[index]
			band.Width = bandWidth
			b = band.bandLabel
			b.Width = band.Width
		
			bandCanvasHeight = z * (band._rw.getPt(eval(band.props["height"])))
			band.Height = bandCanvasHeight + b.Height
			b.Top = band.Height - b.Height

			if index == 0:
				band.Top = mt + tr.Height
			else:
				band.Top = self._bands[index-1].Top + self._bands[index-1].Height

			lr = self._rulers["%s-left" % band.Caption]
			lr.Length = bandCanvasHeight
			
			rr = self._rulers["%s-right" % band.Caption]
			rr.Length = bandCanvasHeight

			band.Left = ml + lr.Thickness
			lr.Position = (0, band.Top)
			rr.Position = (lr.Width + pageWidth, band.Top)
			totPageHeight = band.Top + band.Height

			band.drawObjects()

		u = 10
		totPageHeight = totPageHeight + mb

		br = self._rulers["bottom"]
		br.Length = pageWidth

		tr.Position = (lr.Width,0)
		br.Position = (lr.Width, totPageHeight)
		totPageHeight += br.Height

		self.SetScrollbars(u,u,(pageWidth + lr.Width + rr.Width)/u,totPageHeight/u)
		self.SetFocus()


	def getRuler(self, orientation):
		defaultThickness = 10
		defaultLength = 1

		class Ruler(dabo.ui.dPanel):
			def initProperties(self):
				self.BackColor = (192,128,192)
				self._orientation = orientation[0].lower()

			def _getThickness(self):
				if self._orientation == "v":
					val = self.Width
				else:
					val = self.Height
				return val

			def _setThickness(self, val):
				if self._orientation == "v":
					self.Width = val
				else:
					self.Height = val
				
			def _getLength(self):
				if self._orientation == "v":
					val = self.Height
				else:
					val = self.Width
				return val

			def _setLength(self, val):
				if self._orientation == "v":
					self.Height = val
				else:
					self.Width = val
			
			Length = property(_getLength, _setLength)
			Thickness = property(_getThickness, _setThickness)

		return Ruler(self, Length=defaultLength, Thickness=defaultThickness)

#  End of ReportDesigner Class
# 
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
#
#  ReportDesignerForm Class
#
class ReportDesignerForm(dabo.ui.dForm):
	"""Main form, status bar, and menu for the report designer.
	"""
	def initProperties(self):
		self._captionBase = self.Caption = "Dabo Report Designer"
		self.Sizer = None
		
	def afterInit(self):
		self.addObject(ReportDesigner, Name="editor")
		self.fillMenu()

	def initEvents(self):
		self.bindEvent(dEvents.Close, self.onClose)

	def getCurrentEditor(self):
		return self.editor

	def onClose(self, evt):
		result = self.editor.closeFile()
		if result is None:
			evt.stop()
		
	def onFileNew(self, evt):
		o = self.editor
		if o._rw.ReportFormFile is None and not o._rw._isModified():
			# open in this editor
			o = self
		else:
			# open in a new editor
			o = ReportDesignerForm(self.Parent)
			o.Size = self.Size
			o.Position = self.Position + (20,20)
		o.editor.newFile()
		o.Show()

	def onFileOpen(self, evt):
		o = self.editor
		fileName = o.promptForFileName("Open")
		if fileName is not None:
			if o._rw.ReportFormFile is None and not o._rw._isModified():
				# open in this editor
				o = self
			else:
				# open in a new editor
				o = ReportDesignerForm(self.Parent)
				o.Size = self.Size
				o.Position = self.Position + (20,20)
			o.editor.newFile()
			o.Show()
			o.editor.openFile(fileName)

	def onFileSave(self, evt):
		self.editor.saveFile()
		
	def onFileClose(self, evt):
		result = self.editor.closeFile()
		if result is not None:
			self.Close()
		
	def onFileSaveAs(self, evt):
		fname = self.editor.promptForSaveAs()
		if fname:
			self.editor.saveFile(fname)
			
	def onViewZoomIn(self, evt):
		ed = self.getCurrentEditor()
		ed._zoom = ed._zoom + .1
		ed._onFormResize(None)

	def onViewZoomNormal(self, evt):
		ed = self.getCurrentEditor()
		ed._zoom = ed._normalZoom
		ed._onFormResize(None)

	def onViewZoomOut(self, evt):
		ed = self.getCurrentEditor()
		ed._zoom = ed._zoom - .1
		ed._onFormResize(None)

	def fillMenu(self):
		mb = self.MenuBar
		fileMenu = mb.getMenu("File")
		viewMenu = mb.getMenu("View")
		dIcons = dabo.ui.dIcons
				
		fileMenu.prependSeparator()

		fileMenu.prepend("Save &As", bindfunc=self.onFileSaveAs, bmp="saveAs", 
		                 help="Save under a different file name")

		fileMenu.prepend("&Save\tCtrl+S", bindfunc=self.onFileSave, bmp="save",
		                 help="Save file")

		fileMenu.prepend("&Close\tCtrl+W", bindfunc=self.onFileClose, bmp="close",
		                 help="Close file")

		fileMenu.prepend("&Open\tCtrl+O", bindfunc=self.onFileOpen, bmp="open",
		                 help="Open file")

		fileMenu.prepend("&New\tCtrl+N", bindfunc=self.onFileNew, bmp="new",
		                 help="New file")

		viewMenu.appendSeparator()

		viewMenu.append("Zoom &In\tCtrl++", bindfunc=self.onViewZoomIn, 
		                bmp="zoomIn", help="Zoom In")

		viewMenu.append("&Normal Zoom\tCtrl+/", bindfunc=self.onViewZoomNormal, 
		                bmp="zoomNormal", help="Normal Zoom")

		viewMenu.append("Zoom &Out\tCtrl+-", bindfunc=self.onViewZoomOut, 
		                bmp="zoomOut", help="Zoom Out")

#  End of ReportDesignerForm Class
#
#------------------------------------------------------------------------------


if __name__ == "__main__":
	app = dabo.dApp()
	app.MainFormClass = None
	app.setup()
	if len(sys.argv) > 1:
		for fileSpec in sys.argv[1:]:
			form = ReportDesignerForm(None)
			form.editor.openFile("%s" % fileSpec)
			form.Show()
	else:
		form = ReportDesignerForm(None)
		form.editor.newFile()
		form.Show()
	app.start()
