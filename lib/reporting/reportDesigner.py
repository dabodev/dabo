import dabo.ui
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from reportWriter import ReportWriter

default_bandHeight = 40

class BandLabel(dabo.ui.dButton): pass

class Band(dabo.ui.dPanel):
	def afterInit(self):
		self._bandLabelHeight = 27
		self.BackColor = (255,255,255)
		self.Top = 100
		self.addObject(BandLabel, "bandLabel", FontSize=7, Height=self._bandLabelHeight)

		self.bandLabel.bindEvent(dEvents.Hit, self._onBandLabelHit)


	def propertyDialog(self):
		band = self
		class PropertyDialog(dabo.ui.dDialog):
			def afterInit(self):
				self.Accepted = False

			def addControls(self):
				self.addObject(dabo.ui.dLabel, Name="lblHeight", Caption="Band Height:",
				               Alignment="Right", Width=125)
				self.addObject(dabo.ui.dTextBox, Name="txtHeight", Width=200, 
				               Value=band.props["height"])
			
				h = dabo.ui.dSizer("h")
				h.append(self.lblHeight, "fixed", alignment=("middle", "right"))
				h.append(self.txtHeight, alignment=("middle", "right"), border=5)
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
			self.reposition()

	def reposition(self):
		self.Parent._onFormResize(None)

	def _onBandLabelHit(self, evt):
		self.propertyDialog()


	def _getCaption(self):
		return self.bandLabel.Caption

	def _setCaption(self, val):
		self.bandLabel.Caption = val

	Caption = property(_getCaption, _setCaption)


class ReportDesigner(dabo.ui.dScrollPanel):
	def afterInit(self):
		self._bands = []
		self._rw = ReportWriter()
		self._rw.ReportFormFile = "samplespec.rfxml"
		self.ReportForm = self._rw.ReportForm

		for band in ("pageHeader", "pageFooter"):
			b = Band(self, Caption=band)
			b.props = self.ReportForm[band]
			b._rw = self._rw
			self._bands.append(b)

		self.Form.bindEvent(dEvents.Resize, self._onFormResize)


	def _onFormResize(self, evt):
		print 'resize'
#		print self._rw.getPageSize()
#		self.Width = self._rw.getPageSize()[0]
		bandWidth = self._rw.getPageSize()[0]
		for index in range(len(self._bands)):
			band = self._bands[index]
			band.Width = bandWidth
			b = band.bandLabel
			b.Width = band.Width
		
			band.Height = band._rw.getPt(eval(band.props["height"])) + b.Height
			b.Top = band.Height - b.Height

			if index == 0:
				band.Top = 0
			else:
				band.Top = self._bands[index-1].Top + self._bands[index-1].Height
			totBandHeight = band.Top + band.Height
	
		u = 10
		self.SetScrollbars(u,u,bandWidth/u,totBandHeight/u)

class ReportDesignerForm(dabo.ui.dForm):
	def afterInit(self):
		self.Sizer = None
		self.addObject(ReportDesigner, Name="reportDesigner")

		self.Caption = "Dabo Report Designer: %s" % self.reportDesigner._rw.ReportFormFile

if __name__ == "__main__":
	app = dabo.dApp()
	app.MainFormClass = ReportDesignerForm
	app.setup()
	app.start()
