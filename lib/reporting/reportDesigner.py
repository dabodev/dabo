import sys, os
import dabo.ui
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from reportWriter import ReportWriter


class BandLabel(dabo.ui.dPanel):
	def initEvents(self):
		self.bindEvent(dEvents.Paint, self.onPaint)
		self.bindEvent(dEvents.MouseLeftDown, self.onLeftDown)
		self.bindEvent(dEvents.MouseLeftDoubleClick, self.onDoubleClick)
		self.bindEvent(dEvents.MouseEnter, self.onMouseEnter)

	def onLeftDown(self, evt):
		print "onLeftDown", self.Caption

	def onMouseEnter(self, evt):
		import wx		## need to abstract mouse cursor
		try:
			lock = eval(self.Parent.props["designerLock"])
		except KeyError:
			lock = False
		if lock:
			self.SetCursor(wx.NullCursor)
		else:
			self.SetCursor(wx.StockCursor(wx.CURSOR_SIZENS))

	def onDoubleClick(self, evt):
		self.Parent.propertyDialog()

	def onPaint(self, evt):
		import wx		## (need to abstract DC drawing)
		dc = wx.PaintDC(self)
		rect = self.GetClientRect()
		font = dc.GetFont()
		font.SetPointSize(8)

		dc.SetTextForeground(wx.BLACK)
		dc.SetBrush(wx.Brush("WHEAT", wx.SOLID))
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


class Band(dabo.ui.dPanel):
	def afterInit(self):
		self._bandLabelHeight = 18
		self.BackColor = (255,255,255)
		self.Top = 100
		self.addObject(BandLabel, "bandLabel", FontSize=10, 
		               BackColor=(128,128,128), Height=self._bandLabelHeight)


	def propertyDialog(self):
		band = self
		class PropertyDialog(dabo.ui.dDialog):
			def afterInit(self):
				self.Accepted = False

			def addControls(self):
				try:
					lock = eval(band.props["designerLock"])
				except KeyError:
					lock = False

				self.addObject(dabo.ui.dLabel, Name="lblHeight", Caption="Band Height:",
				               Alignment="Right", Width=125)
				self.addObject(dabo.ui.dTextBox, Name="txtHeight", Width=200, 
				               Value=band.props["height"])
				self.addObject(dabo.ui.dCheckBox, Name="chkLock", Caption="Lock", Value=lock)
			
				h = dabo.ui.dSizer("h")
				h.append(self.lblHeight, "fixed", alignment=("middle", "right"))
				h.append(self.txtHeight, alignment=("middle", "right"), border=5)
				h.append(self.chkLock, alignment=("middle", "right"), border=5)
				self.Sizer.append(h, border=5)

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
				self.Accepted = True
				self.Visible = False

			def onCancel(self, evt):
				self.Accepted = False
				self.Visible = False


		dlg = PropertyDialog(self.Form, 
		                     Caption="%s Properties" % self.bandLabel.Caption)
		dlg.show()

		if dlg.Accepted:
			self.props["height"] = dlg.txtHeight.Value
			self.props["designerLock"] = str(dlg.chkLock.Value)
			self.reposition()

	def reposition(self):
		self.Parent._onFormResize(None)

	def _getCaption(self):
		return self.bandLabel.Caption

	def _setCaption(self, val):
		self.bandLabel.Caption = val

	Caption = property(_getCaption, _setCaption)


class ReportDesigner(dabo.ui.dScrollPanel):
	def afterInit(self):
		self._zoom = self._normalZoom = 1.3
		self.BackColor = (192,192,192)
		self.clearReportForm()

		self.Form.bindEvent(dEvents.Resize, self._onFormResize)

	
	def clearReportForm(self):
		"""Called from afterInit and closeFile to clear the report form."""
		self._rulers = []
		self._bands = []
		self._rw = ReportWriter()
		self.ReportForm = None


	def promptToSave(self):
		"""Decides whether user should be prompted to save, and whether to save."""
		ret = True
		if self._rw._isModified():
			result = dabo.ui.dMessageBox.areyousure("Save changes?")
			if result:
				self.saveFile()
			else:
				ret = False
		return ret


	def saveFile(self):
		xml = self._rw._getXMLFromForm()
		file = open(self._rw.ReportFormFile, "w")
		file.write(xml)
		file.close()


	def closeFile(self):
		result = self.promptToSave()
		if result:
			self._rw.ReportFormFile = None
			return True
		else:
			return False


	def newFile(self):
		if self.closeFile():
			self._rw.ReportForm = self._rw._getEmptyForm()
			self.initReportForm()
			self.Form.Caption = "%s: %s" % (self.Form._captionBase,
			                                "< New >")

	def openFile(self, fileSpec):
		if os.path.exists(fileSpec):
			if self.closeFile():
				self._rw.ReportFormFile = fileSpec
				self.initReportForm()
				self.Form.Caption = "%s: %s" % (self.Form._captionBase,
				                                self._rw.ReportFormFile)
		else:
			raise ValueError, "File %s does not exist." % fileSpec


	def initReportForm(self):
		"""Called from openFile and newFile when time to set up the Report Form."""
		self.ReportForm = self._rw.ReportForm

		for band in ("pageHeader", "detail", "pageFooter"):
			b = Band(self, Caption=band)
			b.props = self.ReportForm[band]
			b._rw = self._rw
			self._bands.append(b)


	def _onFormResize(self, evt):
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

		self.clearRulers()

		tr = self.getRuler("h", pageWidth)

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

			lr = self.getRuler("v", bandCanvasHeight)
			rr = self.getRuler("v", bandCanvasHeight)
			band.Left = ml + lr.Width
			lr.Position = (0, band.Top)
			rr.Position = (lr.Width + pageWidth, band.Top)
			totPageHeight = band.Top + band.Height
	
		u = 10
		totPageHeight = totPageHeight + mb

		br = self.getRuler("h", pageWidth)
		tr.Position = (lr.Width,0)
		br.Position = (lr.Width, totPageHeight)
		totPageHeight += br.Height

		self.SetScrollbars(u,u,(pageWidth + lr.Width + rr.Width)/u,totPageHeight/u)

	def clearRulers(self):
		for r in self._rulers:
			r.Destroy()
		self._rulers = []

	def getRuler(self, orientation, length):
		thickness = 10
		class Ruler(dabo.ui.dPanel):
			def afterInit(self):
				self.BackColor = (192,128,192)
				if orientation[0].lower() == "v":
					w = thickness
					h = length
				else:
					w = length
					h = thickness
				self.Size = (w,h)
		r = Ruler(self)
		self._rulers.append(r)
		return r

class ReportDesignerForm(dabo.ui.dForm):
	def afterInit(self):
		self._captionBase = self.Caption = "Dabo Report Designer"
		self.Sizer = None
		self.addObject(ReportDesigner, Name="editor")
		self.fillMenu()

	def getCurrentEditor(self):
		return self.editor

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
			if o._fileName == o._newFileName and not o.GetModify():
				# open in this editor
				o = self
			else:
				# open in a new editor
				o = EditorForm(self.Parent)
				o.restoreSizeAndPosition()
				o.Position = self.Position + (20,20)
			o.editor.newFile()
			o.Show()
			o.editor.openFile(fileName)

	def onFileSave(self, evt):
		self.editor.saveFile()
		
	def onFileClose(self, evt):
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

if __name__ == "__main__":
	app = dabo.dApp()
	app.MainFormClass = None
	app.setup()
	if len(sys.argv) > 1:
		for fileSpec in sys.argv[1:]:
			form = ReportDesignerForm(None)
			form.editor.openFile("./samplespec.rfxml")
			form.Show()
	else:
		form = ReportDesignerForm(None)
#		form.editor.newFile()
		form.Show()
	app.start()
