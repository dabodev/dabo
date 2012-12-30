# -*- coding: utf-8 -*-
import dabo

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dabo.ui
from dabo.dLocalize import _


class LblMessage(dabo.ui.dLabel):
	def initProperties(self):
		self.WordWrap = True
		self.FontSize = 12
		self.Width = 500


class DlgInfoMessage(dabo.ui.dStandardButtonDialog):
	def initProperties(self):
		self.AutoSize = True
		self.ShowCaption = False
		self.ShowCloseButton = False

	def addControls(self):
		vs = self.Sizer = dabo.ui.dSizer("v", DefaultBorder=10)
		vs.append1x(LblMessage(self, RegID="lblMessage", Caption=self.Message))
		vs.append(dabo.ui.dCheckBox(self, Caption=_("Show this message in the future?"),
				Value=self.DefaultShowInFuture, RegID="chkShowInFuture",
				FontSize=9))


	def _getDefaultShowInFuture(self):
		return getattr(self, "_defaultShowInFuture", True)

	def _setDefaultShowInFuture(self, val):
		self._defaultShowInFuture = bool(val)


	def _getMessage(self):
		return getattr(self, "_message", "")

	def _setMessage(self, val):
		self._message = val


	DefaultShowInFuture = property(_getDefaultShowInFuture, _setDefaultShowInFuture, None,
			_("Specifies whether the 'show in future' checkbox is checked by default."))

	Message = property(_getMessage, _setMessage, None,
			_("Specifies the message to display."))



if __name__ == '__main__':
	from dabo.dApp import dApp
	app = dApp(MainFormClass=None)
	app.setup()
	dlg = DlgInfoMessage(None, Message="This is a test of the emergency broadcast system. If this were an actual " \
			"emergency, you would have been given specific instructions. This is only a test.")
	dlg.show()
