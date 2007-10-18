# -*- coding: utf-8 -*-
import dabo.dEvents as dEvents
import dabo.ui
dabo.ui.loadUI("wx")
import myForms


def fill(form):
	menuBar = form.MenuBar
	fileMenu = menuBar.GetMenu(0)

	# The File/Open menu should be inserted before the File/Quit, but it doesn't 
	# work on Mac ('Open' appears as a menu item, not a submenu).
	if dabo.dApp.Platform == "Mac":
		fileMenu.appendMenu(FileOpenMenu(fileMenu))
	else:
		fileMenu.prependMenu(FileOpenMenu(fileMenu))


class FileOpenMenu(dabo.ui.dMenu):
	def afterInit(self):
		self.Caption = "&Open\tCtrl+O"
		self.HelpText = "Open a module"
		forms = (("Recipes", openRecipes),
				("Categories", openReccats))

		for form in forms:
			itm = dabo.ui.dMenuItem(self, Caption="&"+form[0],
					HelpText="Open the %s module" % form[0])
			self.appendItem(itm)
			itm.bindEvent(dEvents.Hit, form[1])

def openReccats(evt):
	openForm(myForms.frmReccats)

def openRecipes(evt):
	openForm(myForms.frmRecipes)

def openForm(classRef):
	dApp = dabo.dAppRef
	mainForm = dApp.MainForm
	dForm = classRef(mainForm)
	dForm.Show()

