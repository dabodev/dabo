import wx
import wx.py
from wx.py import pseudo
import dabo
import dabo.dEvents as dEvents
from dSplitForm import dSplitForm

dabo.ui.loadUI("wx")

class dShell(dSplitForm):
	def _afterInit(self):
		super(dShell, self)._afterInit()
		
		splt = self.splitter
		splt.MinimumPanelSize = 80
		splt.unbindEvent()
		self.Orientation = "H"
		self.unsplit()
		self.split()
		self._sashPct = 0.7
		self.MainSplitter.bindEvent(dEvents.SashDoubleClick, 
				self.sashDoubleClick)
		
		self.MainSplitter.bindEvent(dEvents.SashPositionChanged, 
				self.sashPosChanged)
		
		cp = self.CmdPanel = self.Panel1
		op = self.OutPanel = self.Panel2
		cp.unbindEvent(dEvents.ContextMenu)
		op.unbindEvent(dEvents.ContextMenu)
		
		cp.Sizer = dabo.ui.dSizer()
		op.Sizer = dabo.ui.dSizer()
		self.shell = wx.py.shell.Shell(self.CmdPanel)
		cp.Sizer.append1x(self.shell)
		# create the output control
		outControl = dabo.ui.dEditBox(op, RegID="edtOut", 
				ReadOnly = True)
		op.Sizer.append1x(outControl)
		
		pseudoOut = pseudo.PseudoFileOut(write=self.appendOut)
		pseudoErr = pseudo.PseudoFileOut(write=self.appendOut)
		self.shell.interp.stdout = pseudoOut
		self.shell.interp.stderr = pseudoErr
		
		# Make 'self' refer to the calling form, or this form if no calling form.
		if self.Parent is None:
			ns = self
		else:
			ns = self.Parent
		self.shell.interp.locals['self'] = ns

		self.Caption = "dShell: self is %s" % ns.Name
		self.setStatusText("Use this shell to interact with the runtime environment")
		self.fillMenu()
		self.shell.SetFocus()
		
	
	def appendOut(self, tx):
		ed = self.edtOut
		ed.Value += tx
		endpos = ed.GetLastPosition()
		# Either of these commands should scroll the edit box
		# to the bottom, but neither do (at least on OS X) when 
		# called directly or via callAfter().
		dabo.ui.callAfter(ed.ShowPosition, endpos)
		dabo.ui.callAfter(ed.SetSelection, endpos, endpos)

		
		
	def onResize(self, evt):
		self.SashPosition = self._sashPct * self.Height
	

	def sashDoubleClick(self, evt):
		# We don't want the window to unsplit
		evt.stop()
		
		
	def sashPosChanged(self, evt):
		self._sashPct = float(self.SashPosition) / self.Height
		
		
	def fillMenu(self):
		viewMenu = self.MenuBar.getMenu("View")
		if viewMenu.Children:
			viewMenu.appendSeparator()
		viewMenu.append("Zoom &In\tCtrl+=", bindfunc=self.onViewZoomIn, 
				bmp="zoomIn", help="Zoom In")
		viewMenu.append("&Normal Zoom\tCtrl+/", bindfunc=self.onViewZoomNormal, 
				bmp="zoomNormal", help="Normal Zoom")
		viewMenu.append("Zoom &Out\tCtrl+-", bindfunc=self.onViewZoomOut, 
				bmp="zoomOut", help="Zoom Out")


	def onViewZoomIn(self, evt):
		self.shell.SetZoom(self.shell.GetZoom()+1)

	def onViewZoomNormal(self, evt):
		self.shell.SetZoom(0)

	def onViewZoomOut(self, evt):
		self.shell.SetZoom(self.shell.GetZoom()-1)
	


def main():
	app = dabo.dApp()
	app.MainFormClass = dShell
	app.setup()
	app.start()

if __name__ == "__main__":
	main()
