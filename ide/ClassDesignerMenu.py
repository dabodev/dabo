# -*- coding: utf-8 -*-
import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _
import sys

def mkDesignerMenu(parent, target=None):
	""" This creates a common menu for all forms in the ClassDesigner. The two
	parameters refer to the parent of the menu (i.e., the form to which the
	menu is being attached. If this is a child of the main ClassDesigner form, the
	second parameter is a reference to that form, which contains the code
	that the menus will be bound to.
	"""
	if target is None:
		target = parent
	try:
		mb = parent.MenuBar
	except AttributeError:
		mb = None
	if mb:
		app = target.Controller
		fm = mb.getMenu(_("File"))
		em = mb.getMenu(_("Edit"))
		vm = mb.getMenu(_("View"))
		
		app.barShowPropSheet = vm.append(_("Hide Object Info Form"),  
				OnHit=app.onTogglePropSheet, 
				help=_("Show/hide the Object Info form"))
		app.barShowEditor = vm.append(_("Hide Code Editor"),  
				OnHit=app.onToggleEditor, 
				help=_("Show/hide the Code Editor"))
		app.barShowPalette = vm.append(_("Show Tool Palette"),  
				OnHit=app.onTogglePalette, 
				help=_("Show/hide the Tool Palette"))
		app.barShowSizerPalette = vm.append(_("Show Sizer Palette"),  
				OnHit=app.onToggleSizerPalette, 
				help=_("Show/hide the Sizer Palette"))
		# Add some hotkeys for displaying the various PemObject panels
		vm.appendSeparator()
		vm.append(_("Display Properties"), HotKey="Ctrl+Shift+P", 
				OnHit=app.onShowProp,
				help=_("Display the property editing page"))
		vm.append(_("Display Object Tree"), HotKey="Ctrl+Shift+O", 
				OnHit=app.onShowObjTree,
				help=_("Display the object tree page"))
		vm.append(_("Display Methods"), HotKey="Ctrl+Shift+M", 
				OnHit=app.onShowMethods,
				help=_("Display the method selection page"))
		vm.append(_("Select Prior Object"), HotKey="Ctrl+PgUp", 
				OnHit=app.onPriorObj,
				help=_("Select the object on the previous node of the object tree"))
		vm.append(_("Select Next Object"), HotKey="Ctrl+PgDn",
				OnHit=app.onNextObj,
				help=_("Select the object on the next node of the object tree"))
		
		
		# Add a separator and the 'Run...' item after the 
		# Open/Save items. Since we are prepending, we need
		# to prepend them in reverse order.
		fm.prependSeparator()
		fm.prepend(_("&Run..."), HotKey="Ctrl+Shift+R", OnHit=app.onRunDesign, 
				help=_("Test your design by running the form"))
		fm.prependSeparator()
		fm.prepend(_("Revert to Saved"), OnHit=app.onRevert, 
				help=_("Re-load the form from disk, losing any pending changes"))
		fm.prepend(_("Save Runnable App"), OnHit=app.onSaveRunnable, 
				help=_("Create a mini app to run your form"))
		fm.prependSeparator()
		itm = fm.prepend(_("&Import Declarations..."), HotKey="Ctrl-I", OnHit=app.onDeclareImports, 
				help=_("Edit the import statements for the code for this class"))
		itm = fm.prepend(_("Single &File for Layout and Code"), OnHit=app.onToggleSaveType,
				help=_("Toggle whether you want code saved in the XML or in a separate file"),
				menutype="check")
		itm.Checked = target.Application.getUserSetting("saveCodeInXML", False)
		itm = fm.prepend(_("Save as C&lass"), HotKey="Ctrl+Shift+S", OnHit=app.onSaveClassDesign, 
				help=_("Save the ClassDesigner contents as a class"))
		itm.DynamicEnabled = app.shouldEnableSaveAsClass
		fm.prepend(_("&Save"), HotKey="Ctrl+S", OnHit=app.onSaveDesign, 
				help=_("Save the ClassDesigner contents as a form"))
		fm.prepend(_("&Open"), HotKey="Ctrl+O", OnHit=app.onOpenDesign, 
				help=_("Open a saved design file"))
		fm.prepend(_("&New Class..."), HotKey="Ctrl+N", OnHit=app.onNewDesign, 
				help=_("Create a new design file"))
					
		alignMenu = dabo.ui.dMenu(Caption=_("Align"))
		itm = alignMenu.append(_("Align Top Edges"), OnHit=app.onAlignTopEdge,
				help=_("Align controls by their top edge"))
		itm.DynamicEnabled = app.shouldEnableAlignControls
		itm = alignMenu.append(_("Align Bottom Edges"), OnHit=app.onAlignBottomEdge,
				help=_("Align controls by their bottom edge"))
		itm.DynamicEnabled = app.shouldEnableAlignControls
		itm = alignMenu.append(_("Align Left Edges"), OnHit=app.onAlignLeftEdge,
				help=_("Align controls by their left edge"))
		itm.DynamicEnabled = app.shouldEnableAlignControls
		itm = alignMenu.append(_("Align Right Edges"), OnHit=app.onAlignRightEdge,
				help=_("Align controls by their right edge"))
		itm.DynamicEnabled = app.shouldEnableAlignControls
		itm = alignMenu.append(_("Bring to Front"), OnHit=app.onBringToFront,
				help=_("Move control to the top of the visible stack"))
		itm.DynamicEnabled = app.shouldEnableZOrdering
		itm = alignMenu.append(_("Send to Back"), OnHit=app.onSendToBack,
				help=_("Move control to the bottom of the visible stack"))
		itm.DynamicEnabled = app.shouldEnableZOrdering
		
		emCnt = len(em.Children)
		em.insertMenu(emCnt-1, alignMenu)
# 		alignMenu.DynamicEnabled = app.shouldEnableAlignMenu
		
		try:
			isMain = parent._isMain
		except:
			isMain = False
		if isMain:
			cm = mb.append(_("Controls"))
			ctlList = [(ct["order"], ct["name"]) 
					for ct in app.designerControls]
			ctlList.sort()
			for ctl in ctlList:
				itm = cm.append(ctl[1], OnHit=parent.onAddControl)
				itm.DynamicEnabled = app.shouldEnableAddControl

