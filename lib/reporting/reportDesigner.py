import dabo.ui
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from reportWriter import ReportWriter

default_bandHeight = 40

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
			lock = self.Parent.props["designerLock"] 
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

		dc.SetTextForeground(wx.BLACK)
		dc.SetBrush(wx.Brush("WHEAT", wx.SOLID))
		dc.SetFont(font)
		dc.DrawRectangle(rect[0],rect[1],rect[2],rect[3])
		rect[0] = rect[0]+5
		rect[1] = rect[1]+5
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
		self._bandLabelHeight = 27
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
		self._rulers = []
		self._bands = []
		self._rw = ReportWriter()
		self._rw.ReportFormFile = "samplespec.rfxml"
		self.ReportForm = self._rw.ReportForm
		self.BackColor = (192,192,192)

		for band in ("pageHeader", "detail", "pageFooter"):
			b = Band(self, Caption=band)
			b.props = self.ReportForm[band]
			b._rw = self._rw
			self._bands.append(b)

		self.Form.bindEvent(dEvents.Resize, self._onFormResize)


	def _onFormResize(self, evt):
		"""Resize and position the bands accordingly."""
		rw = self._rw
		rf = self._rw.ReportForm
		z = self._zoom

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
		self.Sizer = None
		self.addObject(ReportDesigner, Name="reportDesigner")

		self.Caption = "Dabo Report Designer: %s" % self.reportDesigner._rw.ReportFormFile
		self.fillMenu()

	def getCurrentEditor(self):
		return self.reportDesigner

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
		viewMenu = mb.getMenu("View")
		dIcons = dabo.ui.dIcons
				
		viewMenu.appendSeparator()

		viewMenu.append("Zoom &In\tCtrl++", bindfunc=self.onViewZoomIn, 
		                bmp="zoomIn", help="Zoom In")

		viewMenu.append("&Normal Zoom\tCtrl+/", bindfunc=self.onViewZoomNormal, 
		                bmp="zoomNormal", help="Normal Zoom")

		viewMenu.append("Zoom &Out\tCtrl+-", bindfunc=self.onViewZoomOut, 
		                bmp="zoomOut", help="Zoom Out")

if __name__ == "__main__":
	app = dabo.dApp()
	app.MainFormClass = ReportDesignerForm
	app.setup()
	app.start()
