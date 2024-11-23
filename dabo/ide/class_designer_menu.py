# -*- coding: utf-8 -*-

from .. import events
from ..dLocalize import _
import sys

from ..ui import dMenu


def mkDesignerMenu(parent, target=None):
    """This creates a common menu for all forms in the ClassDesigner. The two
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
        fm = mb.fileMenu
        em = mb.editMenu
        vm = mb.viewMenu

        app.barShowPropSheet = vm.append(
            ("Hide Object Info Form"),
            OnHit=app.onTogglePropSheet,
            ItemID="view_objinfo",
            help=_("Show/hide the Object Info form"),
        )
        app.barShowEditor = vm.append(
            ("Hide Code Editor"),
            OnHit=app.onToggleEditor,
            ItemID="view_codeeditor",
            help=_("Show/hide the Code Editor"),
        )
        app.barShowPalette = vm.append(
            ("Show Tool Palette"),
            OnHit=app.onTogglePalette,
            ItemID="view_toolpalette",
            help=_("Show/hide the Tool Palette"),
        )
        app.barShowSizerPalette = vm.append(
            ("Show Sizer Palette"),
            OnHit=app.onToggleSizerPalette,
            ItemID="view_sizerpalette",
            help=("Show/hide the Sizer Palette"),
        )
        # Add some hotkeys for displaying the various PemObject panels
        vm.appendSeparator()
        vm.append(
            ("Display Properties"),
            HotKey="Ctrl+Shift+P",
            OnHit=app.onShowProp,
            ItemID="view_properties",
            help=("Display the property editing page"),
        )
        vm.append(
            ("Display Object Tree"),
            HotKey="Ctrl+Shift+O",
            OnHit=app.onShowObjTree,
            ItemID="view_objecttree",
            help=("Display the object tree page"),
        )
        vm.append(
            _("Display Methods"),
            HotKey="Ctrl+Shift+M",
            OnHit=app.onShowMethods,
            ItemID="view_methods",
            help=("Display the method selection page"),
        )
        vm.append(
            _("Select Prior Object"),
            HotKey="Ctrl+PgUp",
            OnHit=app.onPriorObj,
            ItemID="view_priorobj",
            help=("Select the object on the previous node of the object tree"),
        )
        vm.append(
            ("Select Next Object"),
            HotKey="Ctrl+PgDn",
            OnHit=app.onNextObj,
            ItemID="view_nextobj",
            help=("Select the object on the next node of the object tree"),
        )

        # Add a separator and the 'Run...' item after the
        # Open/Save items. Since we are prepending, we need
        # to prepend them in reverse order.
        fm.prependSeparator()
        fm.prepend(
            _("&Run..."),
            HotKey="Ctrl+Shift+R",
            OnHit=app.onRunDesign,
            ItemID="file_run",
            help=_("Test your design by running the form"),
        )
        fm.prependSeparator()
        fm.prepend(
            _("Revert to Saved"),
            OnHit=app.onRevert,
            ItemID="file_revert",
            help=_("Re-load the form from disk, losing any pending changes"),
        )
        fm.prepend(
            _("Save Runnable App"),
            OnHit=app.onSaveRunnable,
            ItemID="file_saverunnable",
            help=_("Create a mini app to run your form"),
        )
        fm.prependSeparator()
        itm = fm.prepend(
            _("&Import Declarations..."),
            HotKey="Ctrl-I",
            OnHit=app.onDeclareImports,
            ItemID="file_import",
            help=_("Edit the import statements for the code for this class"),
        )
        itm = fm.prepend(
            _("Single &File for Layout and Code"),
            OnHit=app.onToggleSaveType,
            ItemID="file_singlefile",
            help=_("Toggle whether you want code saved in the XML or in a separate file"),
            menutype="check",
        )
        itm.Checked = target.Application.getUserSetting("saveCodeInXML", False)
        itm = fm.prepend(
            _("Save as C&lass"),
            HotKey="Ctrl+Shift+S",
            OnHit=app.onSaveClassDesign,
            ItemID="file_saveasclass",
            help=_("Save the ClassDesigner contents as a class"),
        )
        itm.DynamicEnabled = app.shouldEnableSaveAsClass
        fm.prepend(
            _("Save &As..."),
            HotKey="Ctrl+Shift+V",
            OnHit=app.onSaveAsDesign,
            ItemID="file_saveas",
            help=_("Save the ClassDesigner contents in a new file"),
        )
        fm.prepend(
            _("&Save"),
            HotKey="Ctrl+S",
            OnHit=app.onSaveDesign,
            ItemID="file_save",
            help=_("Save the ClassDesigner contents as a form"),
        )
        fm.prepend(
            _("&Edit Text File..."),
            HotKey="Ctrl+E",
            OnHit=app.onEditTextFile,
            ItemID="file_edit_textfile",
            help=_("Open a text file for editing"),
        )
        recent = dMenu(Caption=_("Open Recent"), MenuID="file_open_recent", MRU=True)
        fm.prependMenu(recent)
        fm.prepend(
            _("&Open"),
            HotKey="Ctrl+O",
            OnHit=app.onOpenDesign,
            ItemID="file_open",
            help=_("Open a saved design file"),
        )
        fm.prepend(
            _("&New Class..."),
            HotKey="Ctrl+N",
            OnHit=app.onNewDesign,
            ItemID="file_new",
            help=_("Create a new design file"),
        )

        alignMenu = dMenu(Caption=_("Align"), MenuID="base_align")
        itm = alignMenu.append(
            _("Align Top Edges"),
            OnHit=app.onAlignTopEdge,
            ItemID="align_top",
            help=_("Align controls by their top edge"),
        )
        itm.DynamicEnabled = app.shouldEnableAlignControls
        itm = alignMenu.append(
            _("Align Bottom Edges"),
            OnHit=app.onAlignBottomEdge,
            ItemID="align_bottom",
            help=_("Align controls by their bottom edge"),
        )
        itm.DynamicEnabled = app.shouldEnableAlignControls
        itm = alignMenu.append(
            _("Align Left Edges"),
            OnHit=app.onAlignLeftEdge,
            ItemID="align_left",
            help=_("Align controls by their left edge"),
        )
        itm.DynamicEnabled = app.shouldEnableAlignControls
        itm = alignMenu.append(
            _("Align Right Edges"),
            OnHit=app.onAlignRightEdge,
            ItemID="align_right",
            help=_("Align controls by their right edge"),
        )
        itm.DynamicEnabled = app.shouldEnableAlignControls
        itm = alignMenu.append(
            _("Bring to Front"),
            OnHit=app.onBringToFront,
            ItemID="align_bringtofront",
            help=_("Move control to the top of the visible stack"),
        )
        itm.DynamicEnabled = app.shouldEnableZOrdering
        itm = alignMenu.append(
            _("Send to Back"),
            OnHit=app.onSendToBack,
            ItemID="align_sendtoback",
            help=_("Move control to the bottom of the visible stack"),
        )
        itm.DynamicEnabled = app.shouldEnableZOrdering

        emCnt = len(em.Children)
        em.insertMenu(emCnt - 1, alignMenu)
        #         alignMenu.DynamicEnabled = app.shouldEnableAlignMenu

        try:
            isMain = parent._isMain
        except:
            isMain = False
        if isMain:
            cm = mb.append(_("Controls"))
            ctlList = [(ct["order"], ct["name"]) for ct in app.designerControls]
            ctlList.sort()
            for ctl in ctlList:
                itm = cm.append(ctl[1], OnHit=parent.onAddControl)
                itm.DynamicEnabled = app.shouldEnableAddControl
