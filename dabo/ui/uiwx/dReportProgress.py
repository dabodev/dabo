import dabo
from dForm import dBorderlessForm
from dGauge import dGauge
from dLabel import dLabel
from dButton import dButton

class dReportProgress(dBorderlessForm):
	def afterInit(self):
		self.gauge = dGauge(self)
		lblTitle = dLabel(self, Caption="Processing report...", FontBold=True, FontSize=12)
		butCancel = dButton(self, CancelButton=True, Caption="Cancel", OnHit=self.onCancel)
		ms = self.Sizer = dabo.ui.dBorderSizer(self, "v", DefaultBorder=10)
		ms.append(lblTitle)
		ms.append(self.gauge, "expand")
		ms.append(butCancel, alignment="right")
		butCancel.setFocus()
		self.fitToSizer()

	def initProperties(self):
		self.Centered = True

	def updateProgress(self, val, range):
		self.gauge.Range = range
		self.gauge.Value = val
		self.gauge.refresh()
		dabo.ui.yieldUI()
		
	def onCancel(self, evt):
		print "cancel"

