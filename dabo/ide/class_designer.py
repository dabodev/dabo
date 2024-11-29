#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import copy
import inspect
import os
import sys

from ..application import dApp
from ..dException import dException
from ..dLocalize import _
from ..lib import DesignerUtils
from ..lib.DesignerClassConverter import DesignerClassConverter
from ..lib import utils as libutils
from ..lib.utils import dictStringify
from ..lib.utils import ustr
from .. import events
from .. import application
from .. import settings
from .. import ui
from ..ui import dBaseMenuBar
from ..ui import dBitmap
from ..ui import dBitmapButton
from ..ui import dBorderSizer
from ..ui import dBox
from ..ui import dButton
from ..ui import dCheckBox
from ..ui import dCheckList
from ..ui import dColumn
from ..ui import dComboBox
from ..ui import dDateTextBox
from ..ui import dDialog
from ..ui import dDockForm
from ..ui import dDropdownList
from ..ui import dEditBox
from ..ui import dEditor
from ..ui import dForm
from ..ui import dFormMain
from ..ui import dGauge
from ..ui import dGrid
from ..ui import dGridSizer
from ..ui import dHtmlBox
from ..ui import dImage
from ..ui import dLabel
from ..ui import dLed
from ..ui import dLine
from ..ui import dListBox
from ..ui import dListControl
from ..ui import dMaskedTextBox
from ..ui import dMediaControl
from ..ui import dMenu
from ..ui import dOkCancelDialog
from ..ui import dPage
from ..ui import dPageFrame
from ..ui import dPageFrameNoTabs
from ..ui import dPageList
from ..ui import dPageSelect
from ..ui import dPageStyled
from ..ui import dPanel
from ..ui import dRadioList
from ..ui import dScrollPanel
from ..ui import dShell
from ..ui import dSizer
from ..ui import dSizerMixin
from ..ui import dSlidePanel
from ..ui import dSlidePanelControl
from ..ui import dSlider
from ..ui import dSpinner
from ..ui import dSplitter
from ..ui import dTextBox
from ..ui import dToggleButton
from ..ui import dToolForm
from ..ui import dTreeView
from ..ui.dialogs import Wizard
from ..ui.dialogs import WizardPage

from . import class_designer_menu
from .class_designer_form_mixin import ClassDesignerFormMixin
from .class_designer_pem_form import PemForm
from .class_designer_editor import EditorForm
from .class_designer_components import LayoutPanel
from .class_designer_components import LayoutBasePanel
from .class_designer_components import LayoutSpacerPanel
from .class_designer_components import LayoutSizer
from .class_designer_components import LayoutBorderSizer
from .class_designer_components import LayoutGridSizer
from .class_designer_components import LayoutSaverMixin
from .class_designer_components import NoSizerBasePanel
from .class_designer_components import szItemDefaults
from .class_designer_components import classFlagProp
from .class_designer_control_mixin import ClassDesignerControlMixin as cmix
from .class_designer_custom_property_dialog import ClassDesignerCustomPropertyDialog
from .class_designer_sizer_palette import SizerPaletteForm
from .class_designer_exceptions import PropertyUpdateException
from .editor import EditorForm as TextEditorForm

dabo_module = settings.get_dabo_package()


class PageInfoDialog(dOkCancelDialog):
    def __init__(self, *args, **kwargs):
        self.noTabs = self._extractKey(kwargs, "NoTabs", False)
        self.pageCount = 3
        self.pageClass = _("<default>")
        self.tabPositions = ("Top", "Bottom", "Left", "Right")
        self.tabPosSelection = 0
        super(PageInfoDialog, self).__init__(*args, **kwargs)

    def addControls(self):
        self.Caption = _("Paged Control Settings")
        gsz = dGridSizer(MaxCols=2, HGap=5, VGap=12)
        lbl = dLabel(self, Caption=_("Number of pages:"))
        spn = dSpinner(self, DataSource="form", DataField="pageCount", Min=1, Max=20, Value=3)
        gsz.append(lbl, halign="right")
        gsz.append(spn)

        if not self.noTabs:
            lbl = dLabel(self, Caption=_("Tab Position:"))
            dd = dDropdownList(
                self,
                Choices=(_("Top"), _("Bottom"), _("Left"), _("Right")),
                ValueMode="Position",
                Value=0,
                DataSource="form",
                DataField="tabPosSelection",
            )
            gsz.append(lbl, halign="right")
            gsz.append(dd)

        lbl = dLabel(self, Caption=_("Default Page Class:"))
        txt = dTextBox(self, DataSource="form", DataField="pageClass", Enabled=False)
        btn = dButton(self, Caption="...")
        btn.bindEvent(events.Hit, self.onSelectClass)
        hsz = dSizer("h")
        hsz.append1x(txt)
        hsz.appendSpacer(4)
        hsz.append(btn)
        gsz.append(lbl, halign="right")
        gsz.append(hsz)

        gsz.setColExpand("all", True)

        self.Sizer.append1x(gsz, border=30, halign="Center", valign="Middle")
        self.update()
        self.layout()

    def onSelectClass(self, evt):
        f = ui.getFile("cdxml")
        if f:
            self.pageClass = libutils.relativePath(f)
            self.update()


class ClassDesigner(dApp):
    # Behaviors which are normal in the framework may need to
    # be modified when run as the ClassDesigner. This flag will
    # distinguish between the two states.
    isDesigner = True

    def __init__(self, clsFile=""):
        super(ClassDesigner, self).__init__(
            showSplashScreen=False, splashTimeout=10, ignoreScriptDir=True
        )

        self._basePrefKey = "ide.ClassDesigner"
        self._desFormClass = None
        self._selectedClass = dForm
        self._currentForm = None
        self._editorForm = None
        self._textEditorForm = None
        self._pemForm = None
        self._tree = None
        self._palette = None
        self._sizerPalette = None
        self._selection = []
        self._editors = []
        self._srcObj = None
        self._srcPos = None
        self._codeDict = {}
        self._classCodeDict = {}
        self._classPropDict = {}
        self._classImportDict = {}
        self._classDefaultVals = {}
        self._mixedControlClasses = {}
        self._superClassInfo = {}
        self._addingClass = False
        # Tuple of all paged-control classes
        self.pagedControls = (
            dPageFrame,
            dPageList,
            dPageSelect,
            dPageFrameNoTabs,
            dPageStyled,
        )
        self.MainFormClass = None
        # Only applies when running as an app
        if isinstance(self, dApp):
            self.setAppInfo("appName", "Class Designer")
        # Some processes need to behave differently when we are
        # importing a class from a cdxml file; this flag lets them
        # determine what process is being run.
        self.openingClassXML = False
        # Create the clipboard
        self._clipboard = None
        # This holds a reference to the target object when
        # there is a context menu event.
        self._contextObj = None
        # When saving classes, we need to note when we are inside
        # a class definition. The list is used as the class stack.
        self._classStack = []
        # We also need to save child class definitions on a stack, when
        # saving/recreating class components with nested objects.
        self._classChildDefStack = []
        # Flag for indicating that all props, not just non-default ones,
        # are saved in the .cdxml file
        self.saveAllProps = False
        # When we set the DefaultBorder for a sizer, should we
        # resize all its children?
        self._propagateDefaultBorder = True
        # Store the name of the custom class menu here instead of
        # hard-coding it in several places.
        self._customClassCaption = _("Custom Classes")
        # Temporary storage for values to avoid passing these among methods
        self._recreateValsDict = {}
        self._valsDictLIFO = []
        # Add this to the persistent MRUs
        self.Application._persistentMRUs[self._customClassCaption] = self.addCustomClass
        # Persist opened designs, too
        self.Application._persistentMRUs["OpenRecent"] = self.onMRUSelection
        # Save the default atts for sizers. This way we can distinguish
        # from default sizers that can be replaced from customized
        # sizers which should remain.
        self._defBoxSizerAtts = bsa = {}
        atts = LayoutSizer().getDesignerDict(allProps=True)["attributes"]
        bsa["DefaultBorder"] = atts["DefaultBorder"]
        bsa["DefaultBorderTop"] = atts["DefaultBorderTop"]
        bsa["DefaultBorderBottom"] = atts["DefaultBorderBottom"]
        bsa["DefaultBorderLeft"] = atts["DefaultBorderLeft"]
        bsa["DefaultBorderRight"] = atts["DefaultBorderRight"]
        self._defGridSizerAtts = gsa = {}
        atts = LayoutGridSizer().getDesignerDict(allProps=True)["attributes"]
        gsa["HGap"] = atts["HGap"]
        gsa["VGap"] = atts["VGap"]
        gsa["MaxDimension"] = atts["MaxDimension"]
        # Get rid of the update/refresh delays
        settings.useUpdateDelays = False
        # Flag that is set when the user is editing a property value
        self._inPropertyEditing = False

        # Define the controls that can be added to the ClassDesigner. The
        # 'order' value will determine their order in the menu. One plan
        # is to keep track of the user's choices, and weight the orders
        # so that their most frequent choices are at the top.
        self.designerControls = (
            {"name": "Box", "class": dBox, "order": 10},
            {"name": "Bitmap", "class": dBitmap, "order": 20},
            {"name": "BitmapButton", "class": dBitmapButton, "order": 30},
            {"name": "Button", "class": dButton, "order": 40},
            {"name": "CheckBox", "class": dCheckBox, "order": 50},
            {"name": "CodeEditor", "class": dEditor, "order": 60},
            {"name": "ComboBox", "class": dComboBox, "order": 70},
            {"name": "DateTextBox", "class": dDateTextBox, "order": 80},
            {"name": "DropdownList", "class": dDropdownList, "order": 90},
            {"name": "EditBox", "class": dEditBox, "order": 100},
            {"name": "SlidePanelControl", "class": dSlidePanelControl, "order": 110},
            {"name": "HtmlBox", "class": dHtmlBox, "order": 120},
            {"name": "Gauge", "class": dGauge, "order": 130},
            {"name": "Grid", "class": dGrid, "order": 140},
            {"name": "Image", "class": dImage, "order": 150},
            {"name": "Label", "class": dLabel, "order": 160},
            {"name": "LED", "class": dLed, "order": 170},
            {"name": "Line", "class": dLine, "order": 180},
            {"name": "ListBox", "class": dListBox, "order": 190},
            {"name": "ListControl", "class": dListControl, "order": 200},
            {"name": "CheckList", "class": dCheckList, "order": 210},
            {"name": "MaskedTextBox", "class": dMaskedTextBox, "order": 220},
            {"name": "RadioList", "class": dRadioList, "order": 230},
            {"name": "Page", "class": dPage, "order": 240},
            {"name": "Panel", "class": dPanel, "order": 250},
            {"name": "ScrollPanel", "class": dScrollPanel, "order": 260},
            {"name": "Shell", "class": dShell, "order": 270},
            {"name": "PageFrame", "class": dPageFrame, "order": 280},
            {"name": "PageList", "class": dPageList, "order": 290},
            {"name": "PageSelect", "class": dPageSelect, "order": 300},
            {"name": "PageStyled", "class": dPageStyled, "order": 310},
            {"name": "PageFrameNoTabs", "class": dPageFrameNoTabs, "order": 320},
            {"name": "Slider", "class": dSlider, "order": 330},
            {"name": "Spinner", "class": dSpinner, "order": 340},
            {"name": "Splitter", "class": dSplitter, "order": 350},
            {"name": "TextBox", "class": dTextBox, "order": 360},
            {"name": "ToggleButton", "class": dToggleButton, "order": 370},
            {"name": "TreeView", "class": dTreeView, "order": 380},
        )
        try:
            self.designerControls += (
                {"name": "MediaControl", "class": dMediaControl, "order": 155},
            )
        except AttributeError:
            # dMediaControl was not imported; some earlier wx versions don't include this
            pass
        self._initClassEvents()

        self.setup()

        clsOK = False
        if clsFile:
            if not clsFile.endswith(".cdxml"):
                clsFile += ".cdxml"
            try:
                frm = self.openClass(clsFile)
                clsOK = True
            except dException.XmlException as e:
                msg = _("Error: %s\n\nA new file will be created.") % e
                ui.stop(message=msg, title=_("Invalid XML File"))
            except IOError as e:
                msg = _("'%s' does not exist. Create it?") % clsFile
                if ui.areYouSure(message=msg, title=_("File Not Found"), cancelButton=False):
                    frm = self.onNewDesign(evt=None, pth=clsFile)
                    clsOK = True

        if not clsOK:
            frm = self.onNewDesign(None)
            if not frm:
                # They canceled
                sys.exit(0)
            # Use this to determine if an empty class should be released
            frm._initialStateDict = frm.getDesignerDict()
        else:
            frm._initialStateDict = {}
        frm.Controller = self
        self.MainForm = frm
        # When more than one ClassDesigner is open, this will
        # hold the active reference.
        self.CurrentForm = frm
        # Create the form the holds the PropSheet, Method listing
        # and object tree if it hasn't already been created.
        pf = self._pemForm
        if pf is None:
            pf = self._pemForm = PemForm(None)
        pf.Controller = self
        pf.Visible = True

        ## Create the control palette
        palette = self.ControlPalette
        palette.Controller = self
        palette.Visible = False

        # Create the sizer palette, but make it hidden to start
        palette = self.SizerPalette
        palette.Controller = self
        palette.Visible = False

        # Create the Code Editor
        ed = self.EditorForm
        ed.Controller = self
        ed.Visible = True

        ## Create the Text File Editor
        txed = self.TextEditorForm
        txed.Controller = self
        txed.Visible = False

        # Set the initial selection to the form
        self.select(self.CurrentForm)

        frm.Visible = True
        ui.callAfter(frm.layout)
        ui.callAfterInterval(100, self.updateLayout)
        ui.callAfter(frm.bringToFront)
        ui.callAfter(frm.saveState)
        self.start()

    def _initClassEvents(self):
        """Create a dict by baseclass of all applicable events."""
        self._classEvents = {}
        self._classMethods = {}
        baseEvents = (
            "DataEvent",
            "EditorEvent",
            "GridEvent",
            "KeyEvent",
            "ListEvent",
            "MenuEvent",
            "MouseEvent",
            "SashEvent",
            "CalendarEvent",
            "TreeEvent",
        )
        classes = (
            dBox,
            dBitmap,
            dBitmapButton,
            dButton,
            dCheckBox,
            dComboBox,
            dDateTextBox,
            dDialog,
            dDropdownList,
            dEditBox,
            dEditor,
            dSlidePanelControl,
            dForm,
            dFormMain,
            dDockForm,
            dGauge,
            dGrid,
            dHtmlBox,
            dImage,
            dLabel,
            dLed,
            dLine,
            dListBox,
            dListControl,
            dCheckList,
            dMaskedTextBox,
            dOkCancelDialog,
            dPanel,
            dPage,
            dScrollPanel,
            dPageFrame,
            dPageList,
            dPageSelect,
            dPageStyled,
            dPageFrameNoTabs,
            dRadioList,
            dShell,
            dSlider,
            dSpinner,
            dSplitter,
            dTextBox,
            dToggleButton,
            dTreeView,
            Wizard,
            WizardPage,
        )
        try:
            classes += (dMediaControl,)
        except AttributeError:
            # dMediaControl was not imported; some earlier wx versions don't include this
            pass

        def evtsForClass(cls):
            def safeApplies(itm, cls):
                try:
                    return itm.appliesToClass(cls)
                except (AttributeError, NameError):
                    return False

            ret = ["on%s" % k for k, v in list(events.__dict__.items()) if safeApplies(v, cls)]
            ret.sort()
            return ret

        def mthdsForClass(cls):
            ret = []
            mthds = inspect.getmembers(cls, inspect.ismethod)
            # We only want Dabo public methods, which will all begin with
            # a lower-case letter.
            ret = [mthd[0] for mthd in mthds if mthd[0][0] in "abcdefghijklmnopqrstuvwxyz"]
            return ret

        for cls in classes:
            self._classEvents[cls] = evtsForClass(cls)
            self._classMethods[cls] = mthdsForClass(cls)

    def getFormClass(self, filepath=None):
        """If the selected class is a form/dialog, return a mixed-in
        subclass of it. Otherwise, return the base ClassDesignerForm.
        """
        isDialog = issubclass(self._selectedClass, (dDialog,))
        isWizard = issubclass(self._selectedClass, (Wizard,))
        isDockForm = issubclass(self._selectedClass, (dDockForm,))
        formIsMain = issubclass(self._selectedClass, (dForm, dFormMain, dDialog))
        if formIsMain:
            if isDockForm:
                base = self._selectedClass  ##dForm
            elif not isDialog and self._desFormClass is not None:
                return self._desFormClass
            else:
                base = self._selectedClass
        else:
            base = dForm

        class DesForm(ClassDesignerFormMixin, base):
            _superBase = base
            _superMixin = ClassDesignerFormMixin
            try:
                _classFile = os.path.realpath(filepath)
            except (TypeError, AttributeError):
                _classFile = None

            def __init__(self, parent=None, *args, **kwargs):
                self._isMain = formIsMain
                if isDialog:
                    kwargs["BorderResizable"] = True
                    kwargs["ShowCloseButton"] = True
                if isWizard:
                    kwargs["Caption"] = "Dabo Wizard Designer"
                base.__init__(self, parent=parent, *args, **kwargs)
                ClassDesignerFormMixin.__init__(self, parent=parent, *args, **kwargs)
                self._basePrefKey = "ide.ClassDesigner.ClassDesignerForm"

            def _afterInit(self):
                self._designerMode = True
                self._formMode = True
                if isDockForm:
                    self._configureForDockForm()
                super(DesForm, self)._afterInit()

            def addControls(self):
                if not isinstance(self, dOkCancelDialog):
                    # Could be a wizard, or some other object with an 'addControls' method
                    self._superBase.addControls(self)
                    return
                if self.UseSizers:
                    self.mainPanel = LayoutBasePanel(self)
                    self.Sizer.append1x(self.mainPanel)
                    self.mainPanel.Sizer = LayoutSizer("v")
                    # Use a Layout Sizer instead of the default sizer.
                    self.initLayoutPanel = LayoutPanel(self.mainPanel)
                else:
                    self.mainPanel = self.initLayoutPanel = NoSizerBasePanel(
                        self, BackColor=(222, 222, 255)
                    )
                    self.Sizer.append1x(self.mainPanel)
                    self.layout()
                # We need to 'deactivate' the built-in buttons
                self.btnOK.unbindEvent(events.Hit)
                self.btnCancel.unbindEvent(events.Hit)
                self.btnOK.Enabled = self.btnCancel.Enabled = False

            def _setupPanels(self, fromNew=True, addBasePanel=False):
                if isinstance(self, Wizard):
                    self.mainPanel = self.pagePanel
                    if self.UseSizers:
                        self.mainPanel.Sizer = LayoutSizer("v")
                    if fromNew:
                        # Need to ask for number of pages.
                        numPages = ui.getInt(
                            _("How many pages?"),
                            caption=_("Wizard Pages"),
                            defaultValue=3,
                        )
                        pgCls = self.Controller.getControlClass(WizardPage)
                        pgs = [pgCls] * max(1, numPages)
                        self.append(pgs)
                        for num, p in enumerate(self._pages):
                            # Remove the title and line from the current sizer
                            p.Caption = _("Page %s Title") % num
                            if self.UseSizers:
                                # This will automatically add itself to the sizer
                                LayoutPanel(p)
                            else:
                                p.Sizer.append1x(NoSizerBasePanel(p))
                        self.initLayoutPanel = self._pages[0].Children[0]
                    else:
                        self.initLayoutPanel = self.mainPanel
                    self.CurrentPage = 0
                    self.btnCancel.Enabled = False
                    # Prevent the Finish button from closing the design surface.
                    self.finish = lambda: False
                    return

                if self.UseSizers:
                    if isinstance(self, dOkCancelDialog):
                        # already done
                        return
                    if isinstance(self, dDockForm):
                        self.mainPanel = self.CenterPanel
                    else:
                        self.Sizer = dSizer("v")
                        self.mainPanel = LayoutBasePanel(self)
                        self.Sizer.append1x(self.mainPanel)

                    self.mainPanel.Sizer = LayoutSizer("v")
                    if addBasePanel:
                        pnlCls = self.Controller.getControlClass(dPanel)
                        pnl = pnlCls(self.mainPanel)
                        self.mainPanel.Sizer.append1x(pnl)
                        pnl.Sizer = LayoutSizer("v")
                        self.initLayoutPanel = LayoutPanel(pnl)
                    else:
                        # Use a Layout Sizer instead of the default sizer.
                        self.initLayoutPanel = LayoutPanel(self.mainPanel)
                else:
                    self.Sizer.release()
                    self.Sizer = None
                    self.mainPanel = self.initLayoutPanel = NoSizerBasePanel(
                        self, BackColor=(222, 222, 255)
                    )
                    self.layout()

        ret = DesForm
        if formIsMain and not isDialog and not isDockForm:
            self._desFormClass = ret
        return ret

    def _reuseMainForm(self, useSizers=False):
        """Determines if the MainForm for the Class Designer is a blank, unedited
        form, which can be re-used when the user opens an existing class or
        creates a new class.
        """
        mf = self.MainForm
        if mf:
            if mf.UseSizers != useSizers:
                return False
            mfCurrDict = mf.getDesignerDict()
            # Position and size of the form may have changed; delete those
            # since they are irrelevant. Also, it seems that on Windows these
            # atts are set while the object is being created, so we have to
            # clear them in the _initialStateDict, too.
            for att in ("Left", "Top", "Width", "Height"):
                try:
                    del mfCurrDict["attributes"][att]
                except:
                    pass
                try:
                    del mf._initialStateDict["attributes"][att]
                except:
                    pass
        ret = mf and (mf._initialStateDict == mfCurrDict)
        return ret

    def updateNamespace(self, startFile=None):
        """When classes are added to the application being edited, we need to re-create the
        application namespaces.
        """
        stdBiz = self.Application.getStandardAppDirectory("biz", startFile)
        if not stdBiz:
            # Not running from a standard Dabo project
            return
        stdHome = os.path.split(stdBiz)[0]
        hd = self.Application.HomeDirectory
        if stdHome != hd:
            self.Application.HomeDirectory = stdHome
        if stdHome not in sys.path:
            sys.path.append(stdHome)
        self._initModuleNames()
        if stdHome != hd:
            self.Application.HomeDirectory = hd

    def onEditUndo(self, evt):
        dabo_module.log.info(_("Not implemented yet"))

    def onEditRedo(self, evt):
        dabo_module.log.info(_("Not implemented yet"))

    def _importClassXML(self, pth):
        """Read in the XML and associated code file (if any), and
        return a dict that can be used to re-create the object.
        """
        try:
            if not os.path.exists(pth):
                if os.path.exists(os.path.abspath(pth)):
                    pth = os.path.abspath(pth)
            converter = DesignerClassConverter()
            dct = converter.dictFromStoredText(pth)
        except dException.XmlException as e:
            raise
        except Exception as e:
            if pth.strip().startswith("<?xml") or os.path.exists(pth):
                raise IOError(_("This does not appear to be a valid class file."))
            else:
                raise IOError(_("The class file '%s' was not found.") % pth)

        # Traverse the dct, looking for superclass information
        sc = converter.flattenClassDict(dct)
        if sc:
            # We need to modify the info to incorporate the superclass info
            converter.addInheritedInfo(dct, sc, updateCode=True)
            # Store the base code so that we can determine if instances have
            # modified it.
            self._updateClassCodeRepository(sc)
        return dct

    def _updateClassCodeRepository(self, dct):
        """Take a flattened dict of class IDs and store any code
        associated with those IDs, so that we can later compare it to
        an object's code in order to determine if it has been changed.
        """
        cds = [(kk, vv["code"]) for kk, vv in list(dct.items()) if vv["code"]]
        for cd in cds:
            self._classCodeDict.update({cd[0]: cd[1]})

    def _getClassMethod(self, clsID, mthd):
        """Given a class ID and a method name, returns the code for that
        classID/method combination (if any) from self._classCodeDict.
        """
        cd = self._classCodeDict.get(clsID, {})
        return cd.get(mthd, "")

    def _findSizerInClassDict(self, clsd):
        """Recursively search until a child is found with sizer information.
        If no such child is found, return False.
        """
        ret = False
        atts = clsd.get("attributes", {})
        szinf = atts.get("sizerInfo", "")
        if szinf != "":
            ret = True
        else:
            kids = clsd.get("children", [])
            for kid in kids:
                ret = self._findSizerInClassDict(kid)
                if ret:
                    break
        return ret

    def addMRUPath(self, pth):
        """Convenience method for other classes that hides the details of
        MRUs from them. All we need is the path.
        """
        self.Application.addToMRU(_("Open Recent"), os.path.realpath(pth), self.onMRUSelection)

    def onMRUSelection(self, evt):
        """The user selected an MRU menu item. Translate that prompt to the
        actual path, and open that design.
        """
        # The prompt will have a number prepended to the actual path,
        # separated by a space.
        pth = evt.prompt.split(" ", 1)[-1]
        openDesigns = [frm for frm in self.getDesignerWindows() if frm._classFile == pth]
        if openDesigns:
            openDesigns[0].bringToFront()
        else:
            self.openClass(pth)

    def openClass(self, pth):
        """Called when the user selects the 'Open' menu and selects
        a saved XML file. We need to open the file, and confirm that it is
        indeed a valid class file. If so, we then re-construct the class in
        a new ClassDesigner window.
        """
        # Set the flag so that components know what process we're in.
        self.openingClassXML = True
        # Clear any existing superclass info
        self._superClassInfo = {}
        # Make sure that we have the actual path to the file
        pth = libutils.resolvePathAndUpdate(pth)
        # Add to the MRU list
        self.addMRUPath(pth)
        # Translate the file path into a class dictionary.
        clsd = self._importClassXML(pth)
        importStatements = clsd.pop("importStatements", "")
        if not importStatements:
            # If stored in a single file, 'importStatements' will be in the outermost 'code' dict.
            importStatements = clsd.get("code", {}).pop("importStatements", "")
        # See if the class name requires a separate import
        nm = clsd["name"]
        try:
            imp, clsname = nm.rsplit(".", 1)
            imptSt = "from %(imp)s import %(clsname)s" % locals()
            exec(imptSt, locals())
            clsd["fullname"] = nm
            clsd["name"] = clsname
        except ValueError:
            clsd["fullname"] = nm

        # See if it is a full form-based class, or an individual component.
        isFormClass = clsd["name"] in (
            "dForm",
            "dFormMain",
            "dDockForm",
            "dDialog",
            "dOkCancelDialog",
            "Wizard",
        )
        if isFormClass:
            atts = clsd["attributes"]
            del atts["designerClass"]
            nm = clsd["name"]
            atts["UseSizers"] = self._findSizerInClassDict(clsd)
        else:
            atts = {"UseSizers": self._findSizerInClassDict(clsd)}
            nm = "ClassDesignerForm"

        isDlg = clsd["name"] in ("dDialog", "dOkCancelDialog", "Wizard")
        isWiz = clsd["name"] in ("Wizard",)
        if isDlg:
            self._selectedClass = {
                "dDialog": dDialog,
                "dOkCancelDialog": dOkCancelDialog,
                "Wizard": Wizard,
            }[clsd["name"]]
        else:
            self._selectedClass = dForm

        # Convert any paths in the atts
        try:
            self._basePath = atts["HomeDirectory"]
        except KeyError:
            if os.path.isfile(pth):
                self._basePath = os.path.dirname(os.path.abspath(pth))
            else:
                self._basePath = pth
        libutils.resolveAttributePathing(atts, self._basePath)
        # Read in any .cnxml connection defs.
        currdir = os.path.dirname(pth)
        self._initDB(currdir)
        if os.path.split(currdir)[-1].lower() == "ui":
            # Standard directory structure; process the parent directory
            self._initDB(os.path.dirname(currdir))
        # We need to remove the menu bar class for now, since it isn't used at design time.
        mbf = self._extractKey(atts, "MenuBarFile")
        # 'CxnFile' has been removed as a property, but some old cdxml files may still reference it.
        self._extractKey(atts, "CxnFile")
        if self._reuseMainForm(useSizers=atts.get("UseSizers", False)):
            # Original form hasn't changed, so just use it.
            frm = self.MainForm
            frm.setPropertiesFromAtts(atts)
        else:
            # For now, just create a standard dForm mixed-in ClassDesigner
            # form as the base.
            frmClass = self.getFormClass(filepath=pth)
            if isWiz:
                self._extractKey(atts, "PageCount")
            frm = frmClass(None, Name=nm, SaveRestorePosition=False, attProperties=atts)
            # The overall size is stored in the out child object's atts
            sz = self._extractKey(clsd["attributes"], "FormSize")
            if sz:
                # It's a string
                sz = eval(sz)
                frm.Size = sz
            if isWiz:
                self._recreateWizardPages(frm, clsd["children"])
                # Clear the children dict
                clsd["children"] = []
            frm._setupPanels(fromNew=False)
        frm.HomeDirectory = self._basePath
        self._classImportDict[frm] = importStatements
        lp = frm.initLayoutPanel
        if isFormClass and frm.UseSizers and not isWiz:
            # Remove the LayoutPanel that was added
            lp.ControllingSizer.remove(lp, True)
            self._srcObj = frm.mainPanel
        else:
            self._srcObj = lp
            if not isFormClass:
                # Set the Caption of the form to the class name
                fname = os.path.split(pth)[1]
                frm.Caption = os.path.splitext(fname)[0]
        frm.Controller = self
        self.CurrentForm = frm
        frm._classFile = os.path.realpath(pth)
        frm._formMode = isFormClass
        if isFormClass:
            # See if there is any code associated with the form
            code = clsd.get("code", "")
            if code:
                self._codeDict[frm] = {}
                # Each method will be a separate dict
                for mthd, cd in list(code.items()):
                    cd = cd.replace("\n]", "]")
                    self._codeDict[frm][mthd] = cd
            # Do the same for the properties
            propDefs = clsd.get("properties", {})
            # Restore any prop definitions.
            if propDefs:
                self._classPropDict[frm] = propDefs
            # Set the child objects
            kids = clsd["children"]
        else:
            # Add the class to the form
            kids = clsd
            if frm.UseSizers:
                self._extractKey(clsd["attributes"], "Top")
                self._extractKey(clsd["attributes"], "Left")
                self._extractKey(clsd["attributes"], "Height")
                self._extractKey(clsd["attributes"], "Width")
        # Add the child objects recursively
        obj = self.recreateChildren(frm.mainPanel, kids, None, False)
        # Clear the superclass info
        self._superClassInfo = {}
        self._basePath = None
        if isFormClass and obj:
            self.select(obj)
        else:
            self.select(frm)
        # Clear the process flag
        self.openingClassXML = False
        # Show it!
        frm.Centered = True
        frm.Visible = True
        if mbf:
            frm.MenuBarFile = mbf
        # Save the initial state
        ui.callAfter(frm.saveState)

        return frm

    def extractSuperClassInfo(self, pth):
        converter = DesignerClassConverter()
        try:
            superClassDict = converter.dictFromStoredText(pth)
        except:
            raise IOError(_("The file '%s' does not appear to be a valid class file.") % pth)
        # Traverse the dct, looking for superclass information
        sup = converter.flattenClassDict(superClassDict)
        # Store the base code so that we can determine if instances have
        # modified it.
        self._updateClassCodeRepository(sup)
        # Add it to the current class definitions
        self._superClassInfo.update(sup)

    def inherit(self, dct):
        sc = self._superClassInfo
        if sc:
            # We need to modify the info to incorporate the superclass info
            DesignerClassConverter.addInheritedInfo(dct, sc)
        return dct

    def _recreateLayoutPanel(self):
        # Panel has already been created by the sizer's slots;
        # just set any sizer item props.
        classID = self._recreateValsDict["classID"]
        sizerInfoDict = self._recreateValsDict["sizerInfoDict"]
        kids = self._recreateValsDict["kids"]
        pnl = self._srcObj
        sz = pnl.ControllingSizer
        itm = pnl.ControllingSizerItem
        sz.setItemProps(itm, sizerInfoDict)
        if classID:
            pnl.classID = classID
        if kids:
            self.recreateChildren(pnl, kids, None, False)

    def _recreateLayoutSpacerPanel(self):
        atts = self._recreateValsDict["atts"]
        classID = self._recreateValsDict["classID"]
        sizerInfoDict = self._recreateValsDict["sizerInfoDict"]
        spc = int(atts.get("Spacing", "20"))
        pnl = self._srcObj
        prnt = pnl.Parent
        pos = pnl.getPositionInSizer()
        sz = pnl.ControllingSizer
        sz.remove(pnl)
        ui.callAfter(pnl.release)
        obj = LayoutSpacerPanel(prnt, Spacing=spc)
        if isinstance(sz, dGridSizer):
            itm = sz.append(obj, row=pos[0], col=pos[1])
        else:
            itm = sz.insert(pos, obj)
        sz.setItemProps(itm, sizerInfoDict)
        if classID:
            obj.classID = classID
        return obj

    def _recreateLayoutSizer(self):
        atts = self._recreateValsDict["atts"]
        parent = self._recreateValsDict["parent"]
        sizerInfoDict = self._recreateValsDict["sizerInfoDict"]
        clsname = self._recreateValsDict["clsname"]
        classID = self._recreateValsDict["classID"]
        fromSizer = self._recreateValsDict["fromSizer"]
        kids = self._recreateValsDict["kids"]
        ornt = self._extractKey(atts, "Orientation", "h")
        slots = int(self._extractKey(atts, "SlotCount", "1"))
        useBox, boxCaption = None, None
        if clsname == "LayoutBorderSizer":
            useBox = True
            boxCaption = self._extractKey(atts, "Caption", None)
        sz, pnl = self.addSizer(
            "box", orient=ornt, slots=slots, useBox=useBox, boxCaption=boxCaption
        )
        szCont = sz.ControllingSizer
        itm = sz.ControllingSizerItem
        is2D = isinstance(szCont, dGridSizer)
        defaults = {True: szItemDefaults[2], False: szItemDefaults[1]}[is2D]
        defAtts = {}
        for key, val in list(defaults.items()):
            defAtts["Sizer_%s" % key] = val
        defAtts.update(dictStringify(atts))
        atts = defAtts
        if isinstance(sz.Parent, dSlidePanel):
            # Main sizer for a slide panel; don't do anything
            pass
        else:
            sz.setPropertiesFromAtts(atts)
        if classID:
            sz.classID = classID
        if not fromSizer:
            parent.Sizer = sz
        if szCont is not None and itm is not None:
            szCont.setItemProps(itm, sizerInfoDict)
        if kids:
            # We need to set the value of _srcObj to the individual
            # LayoutPanel in the sizer. The number of kids should
            # match the number of slots created when the sizer
            # was created.
            childWindowList = sz.ChildWindows[:]
            for pos, kid in enumerate(kids):
                # Set the LayoutPanel to the 'source' object
                pnl = self._srcObj = childWindowList[pos]
                # Pass the 'kid' as a list, since that's what
                # recreateChildren() expects.
                self.recreateChildren(parent, [kid], sz, True)
        return sz

    def _recreateLayoutGridSizer(self):
        atts = self._recreateValsDict["atts"]
        sizerInfoDict = self._recreateValsDict["sizerInfoDict"]
        fromSizer = self._recreateValsDict["fromSizer"]
        classID = self._recreateValsDict["classID"]
        parent = self._recreateValsDict["parent"]
        kids = self._recreateValsDict["kids"]
        rows = int(self._extractKey(atts, "Rows", "1"))
        cols = int(self._extractKey(atts, "Columns", "1"))
        sz, pnl = self.addSizer("grid", rows=rows, cols=cols)
        szCont = sz.ControllingSizer
        is2D = isinstance(szCont, dGridSizer)
        defaults = {True: szItemDefaults[2], False: szItemDefaults[1]}[is2D]
        defAtts = {}
        for key, val in list(defaults.items()):
            defAtts["Sizer_%s" % key] = val
        defAtts.update(dictStringify(atts))
        atts = defAtts
        sz.setPropertiesFromAtts(atts)
        if not fromSizer:
            parent.Sizer = sz
        itm = sz.ControllingSizerItem
        if szCont is not None and itm is not None:
            szCont.setItemProps(itm, sizerInfoDict)
        if classID:
            sz.classID = classID
        if kids:
            for kid in kids:
                kidatts = kid["attributes"]
                rowCol = kidatts.get("rowColPos")
                if isinstance(rowCol, tuple):
                    row, col = rowCol
                else:
                    row, col = eval(kidatts.get("rowColPos"))
                # Set the LayoutPanel to the 'source' object
                pnl = self._srcObj = sz.getItemByRowCol(row, col)
                # Pass the 'kid' as a list, since that's what
                # recreateChildren() expects.
                obj = self.recreateChildren(parent, [kid], sz, True)
        return sz

    def _recreateControl(self):
        rv = self._recreateValsDict
        dct = rv["dct"]
        atts = rv["atts"]
        szr = rv["szr"]
        sizerInfoDict = rv["sizerInfoDict"]
        rowColAtts = rv["rowColAtts"]
        cls = rv["cls"]
        clsname = rv["clsname"]
        classID = rv["classID"]
        code = rv["code"]
        kids = rv["kids"]
        if szr:
            if isinstance(szr, LayoutGridSizer):
                if isinstance(rowColAtts, tuple):
                    row, col = rowColAtts
                else:
                    row, col = eval(rowColAtts)
                if row is not None and col is not None:
                    # It has a given position, so use that. Otherwise,
                    # they may be pasting into a grid sizer.
                    self._srcObj = szr.getItemByRowCol(row, col)
            grdsz = isinstance(szr, dGridSizer)
            if grdsz:
                szType = "Grid"
            else:
                szType = szr.Orientation
            # Get the defaults for this class of control.
            defSizerProps = self.getDefaultSizerProps(cls, szType)
        else:
            defSizerProps = {}
        props = rv["props"] = {}
        try:
            imp, clsname = cls.rsplit(".", 1)
            imptSt = "from %(imp)s import %(clsname)s" % locals()
            exec(imptSt, locals())
            dct["fullname"] = cls
            dct["name"] = clsname
            newClass = eval(clsname)
        except ValueError:
            dct["fullname"] = cls
            newClass = getattr(ui, cls)

        # See if it's a class that requires special handling
        rv["newClass"] = newClass
        isGrid = rv["isGrid"] = issubclass(newClass, dGrid)
        isTree = rv["isTree"] = issubclass(newClass, dTreeView)
        isSplitter = rv["isSplitter"] = issubclass(newClass, dSplitter)
        isSlidePanelControl = rv["isSlidePanelControl"] = issubclass(newClass, dSlidePanelControl)
        isPageControl = rv["isPageControl"] = issubclass(newClass, self.pagedControls)
        noTabs = rv["noTabs"] = issubclass(newClass, dPageFrameNoTabs)

        self._preHandleComplexControls()

        # If we are pasting, we can get two objects with the same
        # Name value, so change it to NameBase.
        nm = self._extractKey(atts, "Name", clsname)
        props["NameBase"] = nm
        obj = self.addNewControl(None, newClass, props=props, skipUpdate=True, attProperties=atts)
        ret = obj
        if isSplitter:
            obj.setPropertiesFromAtts({"Orientation": rv["ornt"]})
            if rv["splt"]:
                ui.setAfter(obj, "Split", True)
        try:
            sz = obj.ControllingSizer
            itm = obj.ControllingSizerItem
        except AttributeError:
            sz = None
            itm = None
        if sz is not None and itm is not None:
            defSizerProps.update(sizerInfoDict)
            sz.setItemProps(itm, defSizerProps)
        if classID:
            obj.classID = classID

        for mthd, cd in list(code.items()):
            if not self._codeDict.get(obj):
                self._codeDict[obj] = {}
            cd = cd.replace("\n]", "]")
            self._codeDict[obj][mthd] = cd
        # Restore any prop definitions.
        propDefs = dct.get("properties", {})
        if propDefs:
            self._classPropDict[obj] = propDefs

        if kids:
            if isGrid:
                self._recreateKidsForGrid(obj, kids)
            elif isPageControl:
                self._recreateKidsForPageControl(obj, kids)
            elif isSlidePanelControl:
                self._recreateKidsForSlidePanel(obj, kids)
            elif isSplitter:
                self._recreateKidsForSplitter(obj, kids)
            elif isTree:
                self._recreateKidsForTree(obj, kids)
            else:
                currPnl = self._srcObj
                if isinstance(obj, (dPanel, dScrollPanel)):
                    self._srcObj = obj
                self.recreateChildren(obj, kids, None, False)
                self._srcObj = currPnl
        return ret

    def _recreateKidsForGrid(self, obj, kids):
        noneTyp = type(None)
        colClass = obj.ColumnClass
        # All the kids will be columns, so add 'em here
        for kid in kids:
            kidatts = kid["attributes"]
            col = colClass(obj)
            for kprop, kval in list(kidatts.items()):
                if kprop in ("designerClass", "classID"):
                    continue
                typ = type(getattr(col, kprop))
                if typ is noneTyp:
                    try:
                        kval = eval(kval)
                    except Exception as e:
                        # Leave it as it is
                        pass
                else:
                    if not issubclass(typ, str):
                        if typ is bool and isinstance(kval, str):
                            kval = kval.lower() in ("true", "t", "yes", "y", "1")
                        else:
                            if typ in (list, tuple) and isinstance(kval, str):
                                kval = eval(kval)
                            else:
                                kval = typ(kval)
                setattr(col, kprop, kval)
            notLast = kid is not kids[-1]
            obj.addColumn(col, inBatch=notLast)
        # Make it look nice
        obj.emptyRowsToAdd = 5
        obj.fillGrid(True)

    def _recreateKidsForPageControl(self, obj, kids):
        for pos, kid in enumerate(kids):
            pg = obj.Pages[pos]
            kidatts = kid.get("attributes", {})
            kidClassID = self._extractKey(kidatts, "classID", "")
            if kidClassID:
                pg.classID = kidClassID
            pg.setPropertiesFromAtts(kidatts)
            kidcode = kid.get("code", {})
            if kidcode:
                self._codeDict[pg] = kidcode
            grandkids = kid.get("children", [])
            if grandkids:
                self._srcObj = pg
                self.recreateChildren(pg, grandkids, None, False)

    def _recreateKidsForSlidePanel(self, obj, kids):
        for pos, kid in enumerate(kids):
            pnl = obj.Children[pos]
            kidatts = kid.get("attributes", {})
            try:
                del kidatts["Name"]
            except KeyError:
                pass
            kidClassID = self._extractKey(kidatts, "classID", "")
            if kidClassID:
                pnl.classID = kidClassID
            pnl.setPropertiesFromAtts(kidatts)
            kidcode = kid.get("code", {})
            if kidcode:
                self._codeDict[pnl] = kidcode
            grandkids = kid.get("children", [])
            if grandkids:
                self._srcObj = pnl
                self.recreateChildren(pnl, grandkids, None, False)

    def _recreateKidsForSplitter(self, obj, kids):
        for pos, kid in enumerate(kids):
            pnlClass = ui.__dict__[kid["name"]]
            obj.createPanes(pnlClass, pane=pos + 1, force=True)
            if pos == 0:
                pnl = obj.Panel1
            else:
                pnl = obj.Panel2
            if pnl is None:
                continue
            kidatts = kid.get("attributes", {})
            pnl.setPropertiesFromAtts(kidatts)
            kidcode = kid.get("code", {})
            if kidcode:
                self._codeDict[pnl] = kidcode
            grandkids = kid.get("children", [])
            if grandkids:
                curr = self._srcObj
                self._srcObj = pnl
                self.recreateChildren(pnl, grandkids, None, False)
                self._srcObj = curr

    def _recreateKidsForTree(self, obj, kids):
        def addTreeNode(parent, atts, kidnodes):
            cap = self._extractKey(atts, "Caption", "")
            if parent is None:
                obj.clear()
                nd = obj.setRootNode(cap)
            else:
                nd = parent.appendChild(cap)
            # Remove the name and designerClass atts
            self._extractKey(atts, "name")
            self._extractKey(atts, "designerClass")
            for prop, val in list(atts.items()):
                try:
                    exec("nd.%s = %s" % (prop, val), locals())
                except (SyntaxError, NameError):
                    exec("nd.%s = '%s'" % (prop, val), locals())
            for kidnode in kidnodes:
                kidatts = kidnode.get("attributes", {})
                kidkids = kidnode.get("children", {})
                addTreeNode(nd, kidatts, kidkids)

        # Set the root
        root = kids[0]
        rootAtts = root.get("attributes", {})
        rootKids = root.get("children", {})
        addTreeNode(None, rootAtts, rootKids)

    def _preHandleComplexControls(self):
        rv = self._recreateValsDict
        isGrid = rv["isGrid"]
        isTree = rv["isTree"]
        isSplitter = rv["isSplitter"]
        isSlidePanelControl = rv["isSlidePanelControl"]
        isPageControl = rv["isPageControl"]
        noTabs = rv["noTabs"]
        atts = rv["atts"]
        props = rv["props"]
        if isGrid:
            try:
                # The column entries will create themselves, so
                # we don't want to create them now.
                del atts["ColumnCount"]
            except:
                pass
            props["ColumnCount"] = 0
        elif isPageControl:
            props["PageCount"] = int(atts.get("PageCount", "0"))
            props["TabPosition"] = atts.get("TabPosition", "")
            try:
                del atts["PageCount"]
            except:
                pass
            try:
                del atts["TabPosition"]
            except:
                pass
            if noTabs:
                del props["TabPosition"]
        elif isSlidePanelControl:
            props["PanelCount"] = int(atts.get("PanelCount", "0"))
            try:
                del atts["PanelCount"]
            except:
                pass
        elif isSplitter:
            ornt = rv["ornt"] = self._extractKey(atts, "Orientation", "Vertical")
            splt = rv["splt"] = self._extractKey(atts, "Split", "False")
            props["createPanes"] = False
            atts["Split"] = False

    def recreateChildren(self, parent, chld, szr, fromSizer, debug=0):
        """Recursive routine to re-create the sizer/object structure of
        the class.
        """
        ret = None
        if isinstance(chld, dict):
            # Single child passed
            chld = [chld]
        for dct in chld:
            self._valsDictLIFO.append(self._recreateValsDict)
            rv = self._recreateValsDict = {
                "parent": parent,
                "szr": szr,
                "fromSizer": fromSizer,
                "dct": dct,
            }
            atts = dct["attributes"]
            # Convert any paths in the atts
            libutils.resolveAttributePathing(atts, self._basePath, True)
            clsname = self._extractKey(atts, "designerClass", "")
            # See if this is a saved class inserted into another design
            isCustomClass = False
            customClassPath = None
            if "classID" in atts:
                cid = atts["classID"]
                if cid and (not "-" in cid):
                    # This is a custom class; make sure that the relative path is correct
                    if not os.path.exists(clsname):
                        clsname = libutils.locateRelativeTo(self._basePath, clsname)
                    isCustomClass = True
                    customClassPath = clsname
                    # Start with the custom class, and then update it with the current stuff
                    self.extractSuperClassInfo(clsname)
            rv["clsname"] = clsname
            # Add any superclass information.
            self.inherit(dct)
            # Need to re-assign the atts from the inherited dct
            atts = rv["atts"] = dct["attributes"]
            cls = rv["cls"] = dct["name"]
            classID = rv["classID"] = self._extractKey(atts, "classID", "")
            kids = rv["kids"] = dct.get("children", None)
            if self._addingClass:
                code = {}
            else:
                code = dct.get("code", {})
            rv["code"] = code
            sizerInfo = rv["sizerInfo"] = self._extractKey(atts, "sizerInfo", "{}")
            if isinstance(sizerInfo, str):
                sizerInfoDict = eval(sizerInfo)
            else:
                sizerInfoDict = sizerInfo
            rv["sizerInfoDict"] = sizerInfoDict

            rowColAtts = rv["rowColAtts"] = self._extractKey(atts, "rowColPos", "(None,None)")
            # Refactored these calls to make this method a little less lengthy.
            if clsname == "LayoutPanel":
                ret = self._recreateLayoutPanel()
            elif clsname == "LayoutSpacerPanel":
                ret = self._recreateLayoutSpacerPanel()
            elif clsname in ("LayoutSizer", "LayoutBorderSizer"):
                ret = self._recreateLayoutSizer()
            elif clsname == "LayoutGridSizer":
                ret = self._recreateLayoutGridSizer()
            else:
                # An actual control!
                ret = self._recreateControl()
            if isCustomClass:
                prop = classFlagProp
                setattr(ret, prop, customClassPath)
            self._recreateValsDict = self._valsDictLIFO.pop()
        return ret

    def _recreateWizardPages(self, frm, kiddict):
        pp = frm.pagePanel
        saveSrc = self._srcObj
        for pgDct in kiddict:
            nm = pgDct["name"]
            code = pgDct.get("code", {})
            propDefs = pgDct.get("properties", {})
            # Remove any unneeded properties
            pgDct.pop("sizerInfo", None)
            pgDct.pop("Width", None)
            pgDct.pop("Height", None)
            try:
                imp, clsname = nm.rsplit(".", 1)
                imptSt = "from %(imp)s import %(clsname)s" % locals()
                exec(imptSt, locals())
                pgDct["fullname"] = nm
                pgDct["name"] = clsname
                cls = eval(clsname)
            except ValueError:
                # Should never happen, so if it does, log it!
                dabo_module.log.error("Invalid wizard page class: %s" % nm)
                ui.stop("Invalid wizard page class: %s" % nm)
                pgDct["fullname"] = nm
                cls = ui.__dict__[nm]
            atts = pgDct["attributes"]
            try:
                del atts["sizerInfo"]
            except KeyError:
                pass
            mixClass = self.getControlClass(cls)
            wizpage = frm.append(mixClass(pp, attProperties=atts))
            #             wizpage.AlwaysResetSizer = True
            for mthd, cd in list(code.items()):
                if not self._codeDict.get(wizpage):
                    self._codeDict[wizpage] = {}
                cd = cd.replace("\n]", "]")
                self._codeDict[wizpage][mthd] = cd
            if propDefs:
                self._classPropDict[wizpage] = propDefs

            # The 'children' entry in the dict will be the sizer, which
            # already exists as part of the page.
            sz = pgDct["children"][0]
            slots = int(sz["attributes"]["SlotCount"])
            kids = sz["children"]
            wizSizer = wizpage.Sizer
            # Need to clear the defaults before adding any controls
            wizSizer.DefaultSpacing = 0
            # The slot count before adding controls should be 4.
            # Add any additional slots.
            newslots = 4 - len(wizSizer.Children)
            if newslots > 0:
                wizSizer.SlotCount += newslots
            self._srcObj = wizpage.Sizer.ChildWindows[-1]
            self.recreateChildren(wizpage, kids, wizpage.Sizer, True, debug=1)
        #             wizpage.iterateCall("layout", resetMin=True)
        self._srcObj = saveSrc

    def onShowSuper(self, classID, mthd):
        """Display the superclass code for the given classID and method."""
        code = self._getClassMethod(classID, mthd)
        if code:
            # Create the dialog
            class SuperCodeDialog(dOkCancelDialog):
                def addControls(self):
                    self.AutoSize = False
                    self.Caption = _("Superclass Code: %s") % mthd
                    #                     self.Size = (400, 500)
                    self.edtSuper = dEditor(self)
                    self.Sizer.append1x(self.edtSuper, border=12)

            dlg = SuperCodeDialog(None, BasePrefKey=self.BasePrefKey + ".SuperCodeDialog")
            dlg.edtSuper.Text = code
            dlg.edtSuper.ReadOnly = True
            dlg.show()
            dlg.release()

    def onDeclareImports(self, evt):
        """Show a dialog that enables the user to edit the import statements
        that will be included with the code when this class is run.
        """
        frm = self.CurrentForm
        txt = self._classImportDict.get(frm)
        if not txt:
            txt = self._classImportDict[frm] = ""

        # Create the dialog
        class ImportEditDialog(dOkCancelDialog):
            def addControls(self):
                self.AutoSize = False
                self.Caption = _("Import Declarations")
                self.Size = (400, 300)
                self.edtImport = dEditor(self, ShowLineNumbers=False, ShowCodeFolding=False)
                self.Sizer.append1x(self.edtImport, border=12)

        dlg = ImportEditDialog(None, BasePrefKey=self.BasePrefKey + ".ImportEditDialog")
        dlg.edtImport.Text = txt
        showDialog = True
        while showDialog:
            dlg.show()
            showDialog = dlg.Accepted
            if showDialog:
                # Check the syntax before storing
                txt = dlg.edtImport.Text
                try:
                    compile(txt.strip().replace("\r\n", "\n"), "", "exec")
                    self._classImportDict[frm] = txt
                    showDialog = dlg.Accepted = False
                except SyntaxError as e:
                    errMsg = _("Syntax Error: %s") % e
                    ui.stop(errMsg, _("Error Compiling Import Declarations"))
        dlg.release()

    def addToImportDict(self, txt):
        """Adds the passed line(s) to the import statements."""
        if isinstance(txt, (list, tuple)):
            for stmnt in txt:
                self.addToImportDict(stmnt)
        else:
            frm = self.CurrentForm
            imp = self._classImportDict.get(frm, "")
            impLines = imp.splitlines()
            if txt not in impLines:
                imp += "\n%s" % txt
            self._classImportDict[frm] = imp

    def getImportDict(self, frm=None):
        """Returns the import statements for the requested form,
        or the current form if no form is specified.
        """
        if frm is None:
            frm = self.CurrentForm
        return self._classImportDict.get(frm, "")

    def setProp(self, obj, prop, val, typ):
        if prop == "Font":
            obj.Font = val
        elif prop == "HeaderFont":
            obj.HeaderFont = val
        else:
            if typ == "multi":
                typ = eval("type(obj.%s)" % prop)
            if typ is bool:
                val = bool(val)
            if isinstance(val, str):
                strVal = val
            else:
                strVal = ustr(val)
            if typ in (str, str) or ((typ is list) and isinstance(val, str)):
                # Escape any single quotes, and then enclose
                # the value in single quotes
                strVal = "u'" + self.escapeQt(strVal) + "'"
            try:
                exec("obj.%s = %s" % (prop, strVal))
            except Exception as e:
                raise PropertyUpdateException(ustr(e))

    def startPropEdit(self):
        self._inPropertyEditing = True

    def endPropEdit(self):
        self._inPropertyEditing = False

    def updatePropVal(self, prop, val, typ):
        """Called whenever the user edits a property. We need to
        update the object accordingly.
        """
        updTreeAll = prop in ("ColumnCount", "SlotCount")
        updTreeName = prop in ("Name", "Orientation", "Caption")
        for obj in self._selection:
            isSzItem = isinstance(obj, (list, LayoutPanel))
            if isSzItem:
                sz = obj.ControllingSizer
                # See if it's a spacer
                if isinstance(obj, LayoutSpacerPanel):
                    if prop.lower() == "spacing":
                        obj.Spacing = val
                    elif not sz.setItemProp(obj.ControllingSizerItem, prop, val):
                        self.setProp(obj, prop, val, typ)
                else:
                    sz.setItemProp(obj.ControllingSizerItem, prop, val)

            elif isinstance(obj, dSizer):
                self.setProp(obj, prop, val, typ)
                updTreeAll = True
            else:
                self.setProp(obj, prop, val, typ)

            fillGrid = False
            if isinstance(obj, dGrid) and prop == "ColumnCount":
                gridObj = obj
                fillGrid = True
            if isinstance(obj, (dColumn, dPage)):
                if isinstance(obj, dColumn):
                    fillGrid = True
                    gridObj = obj.Parent
                ui.callAfter(obj.Parent.update)
            else:
                if hasattr(obj, "update"):
                    obj.update()
            if fillGrid:
                gridObj.emptyRowsToAdd = 5
                gridObj.fillGrid(True)

        self.CurrentForm.layout()
        if updTreeAll:
            self.Tree.updateDisplay(self.CurrentForm)
        elif updTreeName:
            self.Tree.updateNames(self.CurrentForm)
        if prop == "Name":
            # Need to update the object list in the code editor
            self.EditorForm.refreshObjectList(force=True)

    def editSizerSettings(self, obj):
        """Display a dialog that will allow the user to edit all the sizer
        settings in one place.
        """

        class SizerEditDlg(dOkCancelDialog):
            def __init__(self, fillFunc, *args, **kwargs):
                self._fillFunc = fillFunc
                self.alignControls = []
                self.expandControl = None
                super(SizerEditDlg, self).__init__(*args, **kwargs)
                # Set the expand enable/disable
                self.onExpandChange()

            def addControls(self):
                if self._fillFunc:
                    self._fillFunc(self)

            def onExpandChange(self, evt=None):
                if self.expandControl is not None:
                    enab = not self.expandControl.Value
                    for ctl in self.alignControls:
                        ctl.Enabled = enab

        isSpacer = isinstance(obj, LayoutSpacerPanel)
        isSlot = isinstance(obj, LayoutPanel)
        isSizer = isinstance(obj, dSizerMixin)
        csz = obj.ControllingSizer
        cszIt = obj.ControllingSizerItem
        prefix = "Sizer_"
        hasSizer = csz is not None
        if hasSizer:
            if isSlot:
                prefix = ""
                szProps = list(csz.ItemDesignerProps.keys())
            else:
                szProps = [prop for prop in obj.DesignerProps if prop.startswith(prefix)]
            szProps.sort()
        else:
            szProps = []
        if isSpacer:
            szProps.append("Spacing")
        if isSizer:
            selfProps = [prop for prop in obj.DesignerProps if not prop.startswith(prefix)]
        else:
            selfProps = []

        propDict = dict.fromkeys(szProps)
        for prop in szProps:
            if isSlot and not (prop == "Spacing"):
                propDict[prop] = csz.getItemProp(cszIt, prop)
            else:
                propDict[prop] = obj.__getattribute__(prop)

        selfPropDict = dict.fromkeys(selfProps)
        for prop in selfProps:
            selfPropDict[prop] = obj.__getattribute__(prop)

        if csz:
            isInGrid = isinstance(csz, dGridSizer)
            isInVert = csz.Orientation.lower()[0] == "v"
            isInHoriz = csz.Orientation.lower()[0] == "h"
        else:
            isInGrid = isInVert = isInHoriz = False

        def fillDlg(dlg):
            """Adds the appropriate controls to the dialog."""
            hasBoth = szProps and selfProps
            if hasBoth:
                hsz = dSizer("h")
                dlg.Sizer.append(hsz, "x", border=5)
            for propSource in (szProps, selfProps):
                if not propSource:
                    continue
                isAddingSelfProps = propSource == selfProps
                dct = (propDict, selfPropDict)[isAddingSelfProps]
                sz = dGridSizer(MaxCols=2, HGap=8, VGap=5)
                if hasBoth:
                    if isAddingSelfProps:
                        # Add a separator between sections if there are props
                        # in both lists.
                        hsz.appendSpacer(6)

                    bx = dBorderSizer(dlg)
                    if propSource == szProps:
                        bx.Caption = _("Controlling Sizer Properties")
                    else:
                        bx.Caption = _("Properties for This Sizer")
                    bx.append(sz, border=20)
                    hsz.append(bx, "x", border=5)
                else:
                    # Just one section, so add the grid to the dialog's sizer
                    dlg.Sizer.append(sz, border=20)

                for prop in propSource:
                    lowprop = prop.lower()
                    if lowprop.endswith("bordersides"):
                        # Too complicated; skip it.
                        continue
                    val = dct[prop]
                    # Set up custom value controls for some props.
                    if lowprop.endswith("align"):
                        if isInHoriz and lowprop.endswith("halign"):
                            # Not needed
                            continue
                        elif isInVert and lowprop.endswith("valign"):
                            # Not needed
                            continue
                        ctl = dDropdownList(dlg)
                        if lowprop.endswith("halign"):
                            ctl.Choices = ["Left", "Center", "Right"]
                        else:
                            ctl.Choices = ["Top", "Middle", "Bottom"]
                        ctl.StringValue = val
                    elif lowprop == "orientation":
                        ctl = dDropdownList(dlg)
                        ctl.Choices = ["Horizontal", "Vertical"]
                        ctl.StringValue = val
                    elif isinstance(val, bool):
                        ctl = dCheckBox(dlg, Value=val)
                    elif isinstance(val, int):
                        ctl = dSpinner(dlg, Value=val, Max=999999, Min=0)
                        if val == 0:
                            ctl.Value = 1
                            ctl.Value = 0
                    else:
                        ctl = dTextBox(dlg, Value=val)
                    # Create the label
                    lbl = dLabel(dlg, Caption=prop.replace(prefix, ""))

                    # TOOLTIP
                    #                    ctl.ToolTipText =
                    # Add 'em to the grid sizer
                    sz.append(lbl, halign="Right")
                    sz.append(ctl)
                    # Bind it
                    # -                    ctl.DataSource = "self.Controller._sizerObj"
                    ctl.DataSource = obj
                    if isSlot and not (prop == "Spacing"):
                        ctl.DataField = "Sizer_%s" % prop
                    else:
                        ctl.DataField = prop

                    # Create dynamic bindings for the Expand control
                    bareLowprop = prop.replace(prefix, "").lower()
                    if bareLowprop == "expand":
                        ctl.bindEvent(events.Hit, dlg.onExpandChange)
                        dlg.expandControl = ctl
                    elif bareLowprop.endswith("align"):
                        dlg.alignControls.append(ctl)
                dlg.update()

        # OK, we've defined the code for creating the dialog on the fly.
        # Now let's run it. If they click OK, the values will already be set
        # by the data binding. If they cancel, we have to revert them to
        # the values in propDict.
        self._sizerObj = obj
        dlg = SizerEditDlg(fillDlg, BasePrefKey=self.BasePrefKey + ".SizerEditDlg")
        dlg.Caption = _("Sizer Settings")
        self.CurrentForm.bringToFront()
        # This is used to determine if anything has changed in
        # the dialog, so we know whether to update or not.
        self._szDlg = dlg
        self._szDlgVals = self._getSzDlgVals()
        tmr = ui.callEvery(800, self.updInBackground)
        dlg.show()
        tmr.stop()
        tmr.release()
        if dlg.Accepted:
            ui.callAfterInterval(100, self.updateLayout)
        else:
            # revert!
            prefix = ""
            if isSlot:
                prefix = "Sizer_"
            for prop, val in list(propDict.items()):
                propName = prefix + prop
                obj.__setattr__(propName, val)
            for prop, val in list(selfPropDict.items()):
                propName = prefix + prop
                obj.__setattr__(propName, val)
            self.CurrentForm.layout()

        dlg.release()
        self._szDlg = None
        self._szDlgVals = {}
        self._sizerObj = None
        self.CurrentForm.bringToFront()

    def _getSzDlgVals(self):
        ret = {}
        for ctl in self._szDlg.Children:
            if hasattr(ctl, "Value"):
                df = ctl.DataField
                if df:
                    ret[df] = ctl.Value
        return ret

    def updInBackground(self):
        currVals = self._getSzDlgVals()
        if currVals != self._szDlgVals:
            self._szDlgVals = currVals
            self.CurrentForm.layout()

    def _setSlotProp(self, val):
        print("VAL", val, self._sizerObj)

    def _getSel(self):
        """Convenience method used only for debugging. Don't
        count on this method remaining in the code!!!!
        """
        return self._selection[0]

    def getDefaultValues(self, srcObj):
        """Given an object's class, returns a dict containing its
        DesignerProps as keys, and the default value for each as values.
        """
        cls = srcObj.__class__
        ret = self._classDefaultVals.get(cls, {})
        if not ret:
            frm = None
            cleanup = ""
            if issubclass(cls, (dSizer, dGridSizer)):
                obj = cls()
            elif issubclass(cls, (dBorderSizer,)):
                frm = dForm(None, Visible=False, NameBase="BORD")
                obj = cls(frm)
            elif issubclass(cls, (dForm, dDialog)):
                cf = self.CurrentForm
                obj = cls(None)
                obj.Controller = None
                self.CurrentForm = cf
                ui.callAfterInterval(100, self.updateLayout)
            else:
                frm = dForm(None, Visible=False, NameBase="DEFA")
                # We need to handle all the dependent class types
                if issubclass(cls, dPage) and isinstance(srcObj.Parent, self.pagedControls):
                    pgf = srcObj.Parent
                    pp = pgf.PageCount
                    pgf.PageCount += 1
                    obj = pgf.Pages[-1]
                    cleanup = "pgf.PageCount = %s" % pp
                if issubclass(cls, dSlidePanel) and isinstance(srcObj.Parent, dSlidePanelControl):
                    spc = srcObj.Parent
                    pp = spc.PanelCount
                    spc.PanelCount += 1
                    obj = spc.Panels[-1]
                    cleanup = "spc.PanelCount = %s" % pp
                elif issubclass(cls, dColumn):
                    grd = srcObj.Parent
                    cc = grd.ColumnCount
                    grd.ColumnCount += 1
                    obj = grd.Columns[-1]
                    cleanup = "grd.ColumnCount = %s" % cc
                elif issubclass(cls, dTreeView.getBaseNodeClass()):
                    tree = dTreeView(frm, NodeClass=cls)
                    obj = tree.appendNode(None, "")
                else:
                    obj = cls(frm)
            for prop in obj.DesignerProps:
                ret[prop] = getattr(obj, prop)
            self._classDefaultVals[cls] = ret
            if cleanup:
                exec(cleanup, locals())
            if not issubclass(cls, (dPage, dSlidePanel)):
                # Pages will be released by their parent.
                obj.release()
            if frm:
                frm.release()
        return ret

    def onEditCut(self, evt):
        handled = False
        if self.ActiveForm == self.CurrentForm:
            # A designer form is topmost
            if self._selection:
                self._selection[0].onCut(evt)
                handled = True
        else:
            # Normal cut operation
            super(ClassDesigner, self).onEditCut(evt)

    def onEditCopy(self, evt):
        handled = False
        if self.ActiveForm == self.CurrentForm:
            # A designer form is topmost
            if self._selection:
                self._selection[0].onCopy(evt)
                handled = True
        else:
            # Normal cut operation
            super(ClassDesigner, self).onEditCopy(evt)

    def onEditPaste(self, evt):
        handled = False
        if self.ActiveForm == self.CurrentForm:
            # A designer form is topmost
            pnl = self.getActivePanel()
            if not self.UseSizers:
                if pnl is None:
                    pnl = self.CurrentForm.mainPanel
                else:
                    try:
                        pnl = pnl.Parent
                    except:
                        pnl = self.CurrentForm.mainPanel

            if isinstance(pnl, LayoutPanel):
                pnl.onPaste(evt)
                handled = True
            else:
                try:
                    pnl.onPaste(evt)
                except:
                    print("Cannot paste in ", pnl)
        else:
            # Normal cut operation
            super(ClassDesigner, self).onEditPaste(evt)

    def pasteObject(self, pnl, pos=None):
        """If there is a control's dict on the clipboard, re-create the control
        where the panel is located.
        """
        if self._clipboard:
            if pos is None:
                pos = self._srcPos
            clip = copy.deepcopy(self._clipboard)
            self._srcObj = pnl
            cs = pnl.ControllingSizer
            try:
                self._basePath = pnl.Form._classFile
            except:
                self._basePath = os.getcwd()
            obj = self.recreateChildren(pnl, clip, cs, fromSizer=bool(cs))
            self._basePath = None
            if not self.UseSizers:
                if pos is not None:
                    obj.Position = pos
            self.select(obj)
            ui.callAfterInterval(100, self.updateLayout)

    def copyObject(self, obj):
        """Place a copy of the passed control on the clipboard"""
        dct = obj.getDesignerDict()
        # We can't use the Name property, since it may conflict
        # with the original control. So remove any trailing digits
        # and assign the result to the NameBase property, and
        # delete the Name property.
        atts = dct["attributes"]
        # Convert any paths in the atts
        try:
            pth = obj.Form._classFile
        except:
            pth = None
        libutils.resolveAttributePathing(atts, pth)
        nm = obj.Name
        while nm[-1].isdigit():
            nm = nm[:-1]
        dct["attributes"]["NameBase"] = nm
        obj._extractKey(dct["attributes"], "Name")
        # Put the result on the clipboard
        self._clipboard = dct

    def escapeQt(self, s):
        sl = "\\"
        qt = "'"
        return s.replace(sl, sl + sl).replace(qt, sl + qt)

    def updateLayout(self):
        """Called whenever the sizer layout is changed."""
        # Make sure that the selected objects are still 'live'
        for ct in self._selection:
            try:
                junk = ct.Name
            except Exception:
                self._selection.remove(ct)
        if self.UseSizers:
            cf = self.CurrentForm
            if not cf:
                return
            sz = cf.mainPanel.Sizer
            if sz is None or sz.SlotCount == 0:
                # They deleted the main sizer; replace it if needed
                if isinstance(cf, (Wizard, dDockForm)) or hasattr(cf, "CenterPanel"):
                    pass
                else:
                    cf.mainPanel.Sizer = LayoutSizer("v")
                    cf.initLayoutPanel = LayoutPanel(cf.mainPanel)
        self.Tree.updateDisplay(self.CurrentForm)
        self.Tree.select(self._selection)
        self.PemForm.select(self._selection)
        self.EditorForm.select(self._selection)
        ui.callAfterInterval(200, self.CurrentForm.layout)
        ui.callAfterInterval(200, self.CurrentForm.refresh)
        ui.callAfterInterval(200, self.ControlPalette.update)
        ui.callAfterInterval(200, self.SizerPalette.update)

    def flushCodeEditor(self):
        """Forces the content of the editor to update the code repository."""
        self.EditorForm.updateText()

    def updateCodeEditor(self):
        """Forces the code repository to update the contents of the editor."""
        self.EditorForm.refreshCode()

    def onToggleSaveType(self, evt):
        newSetting = not self.getUserSetting("saveCodeInXML", False)
        self.setUserSetting("saveCodeInXML", newSetting)

    def onEditTextFile(self, evt):
        fpath = ui.getFile("py", "txt", "*")
        if fpath:
            self.TextEditorForm.openFile(fpath)
            self.TextEditorForm.show()

    def onSaveDesign(self, evt):
        self.wrapSave(self.CurrentForm.onSaveDesign, evt)

    def onSaveAsDesign(self, evt):
        self.wrapSave(self.CurrentForm.onSaveAsDesign, evt)

    def onSaveClassDesign(self, evt):
        self.wrapSave(self.CurrentForm.onSaveClassDesign, evt)

    def onRunDesign(self, evt):
        self.flushCodeEditor()
        currbiz = self.biz
        full = os.path.join(os.getcwd(), self.CurrentForm._classFile)
        self.updateNamespace(full)
        try:
            self.CurrentForm.onRunDesign(evt)
        except AttributeError as e:
            ui.stop(_("Attribute Error: %s") % ustr(e), _("Attribute Error"))
        except Exception as e:
            msg = ustr(e)
            if hasattr(e, "text"):
                txt = e.text.strip()
            else:
                txt = _("<unspecified>")
            ui.stop(
                _("Compilation Error: %(msg)s\nCode: %(txt)s") % locals(),
                _("Compilation Error"),
            )
        self.biz = currbiz

    def onOpenDesign(self, evt):
        ff = ui.getFile("cdxml")
        if ff:
            self.openClass(ff)
            ui.callAfterInterval(100, self.updateLayout)

    def onNewDesign(self, evt, pth=None):
        pcs = self.pagedControls

        class NewClassPicker(dOkCancelDialog):
            def addControls(self):
                self.fileToOpen = None

                def onOpenSaved(evt):
                    f = ui.getFile("cdxml")
                    if f:
                        self.fileToOpen = f
                        self._onOK(None)

                # Give the option of opening an existing class.
                self.openButton = dButton(self, Caption=_("Open Saved Class"), OnHit=onOpenSaved)

                self.Sizer.append(self.openButton, halign="center")
                self.Sizer.appendSpacer(20)
                # jfcs 5/20/20 halign= "center" no longer ignored by 4.1
                # self.Sizer.append(dLine(self), "x", border=5, halign="center")
                self.Sizer.append(dLine(self), "x", border=5)

                # Create a dropdown list containing all the choices.
                # NOTE: This would be an excellent candidate for usage ordering.
                nameClassPairs = (
                    ("Form", dForm),
                    ("MDI MainForm", dFormMain),
                    ("DockForm", dDockForm),
                    ("Panel", dPanel),
                    ("ScrollPanel", dScrollPanel),
                    ("SlidePanel", dSlidePanelControl),
                    ("Plain Dialog", dDialog),
                    ("OK/Cancel Dialog", dOkCancelDialog),
                    ("Wizard", Wizard),
                    ("WizardPage", WizardPage),
                    ("PageFrame", dPageFrame),
                    ("PageList", dPageList),
                    ("PageSelect", dPageSelect),
                    ("PageStyled", dPageStyled),
                    ("PageNoTabs", dPageFrameNoTabs),
                    ("Box", dBox),
                    ("Bitmap", dBitmap),
                    ("BitmapButton", dBitmapButton),
                    ("Button", dButton),
                    ("CheckBox", dCheckBox),
                    ("ComboBox", dComboBox),
                    ("DateTextBox", dDateTextBox),
                    ("DropdownList", dDropdownList),
                    ("EditBox", dEditBox),
                    ("Editor", dEditor),
                    ("Gauge", dGauge),
                    ("Grid", dGrid),
                    ("HtmlBox", dHtmlBox),
                    ("Image", dImage),
                    ("Label", dLabel),
                    ("LED", dLed),
                    ("Line", dLine),
                    ("ListBox", dListBox),
                    ("ListControl", dListControl),
                    ("CheckList", dCheckList),
                    ("MaskedTextBox", dMaskedTextBox),
                    ("Page", dPage),
                    ("RadioList", dRadioList),
                    ("Shell", dShell),
                    ("Slider", dSlider),
                    ("Spinner", dSpinner),
                    ("Splitter", dSplitter),
                    ("TextBox", dTextBox),
                    ("ToggleButton", dToggleButton),
                    ("TreeView", dTreeView),
                )
                names = [pair[0] for pair in nameClassPairs]
                classes = [pair[1] for pair in nameClassPairs]
                try:
                    maskedPos = classes.index(dMaskedTextBox) + 1
                    classes.insert(maskedPos, dMediaControl)
                    names.insert(maskedPos, "Media Control")
                except AttributeError:
                    # dMediaControl was not imported; some earlier wx versions don't include this
                    pass
                self.dd = dDropdownList(self, Choices=names, Keys=classes, ValueMode="key")
                self.dd.StringValue = "Form"
                self.dd.bindEvent(events.Hit, self.onClassSel)
                self.Sizer.appendSpacer(25)
                lbl = dLabel(self, Caption=_("Select the class to create:"), FontBold=True)
                self.Sizer.append(lbl, halign="left")
                self.Sizer.appendSpacer(3)
                self.Sizer.append(self.dd, 1, halign="Center")
                self.Sizer.appendSpacer(10)

                self.szChk = dCheckBox(
                    self, Value=True, Caption=_("Use Sizers"), OnHit=self.onSzChk
                )
                self.Sizer.append(self.szChk, halign="Center")
                self.Sizer.appendSpacer(6)
                self.baseChk = dCheckBox(self, Value=True, Caption=_("Add Base Panel"))
                self.Sizer.append(self.baseChk, halign="Center")
                self.Sizer.appendSpacer(25)

            def onClassSel(self, evt):
                # This should be the key value, which is a class name
                cls = self.dd.KeyValue
                sizerClasses = (
                    dForm,
                    dFormMain,
                    dDockForm,
                    dPanel,
                    dScrollPanel,
                    dDialog,
                    dOkCancelDialog,
                    Wizard,
                    WizardPage,
                    dPage,
                    dSplitter,
                ) + pcs
                self.szChk.Visible = cls in sizerClasses
                self.baseChk.Visible = cls in (dForm, dFormMain, dDialog) and self.szChk.Value

            def onSzChk(self, evt):
                self.baseChk.Visible = self.szChk.Value

        dlg = NewClassPicker(
            self.CurrentForm,
            Caption=_("Open / Create Class"),
            BasePrefKey=self.BasePrefKey + ".NewClassPicker",
        )
        dlg.show()
        if not dlg.Accepted:
            dlg.release()
            return
        if dlg.fileToOpen:
            return self.openClass(dlg.fileToOpen)
        newClass = self._selectedClass = dlg.dd.Value
        if newClass is dDockForm:
            ui.exclaim(
                _("Sorry, the Dock Form class does not currently work in the Class Designer."),
                title=_("Class not implemented"),
            )
            return
        isDialog = issubclass(newClass, dDialog)
        isWizard = issubclass(newClass, Wizard)
        isFormClass = issubclass(newClass, (dForm, dFormMain, dDialog, Wizard))
        useSizers = dlg.szChk.Visible and dlg.szChk.Value
        addBasePanel = dlg.baseChk.Visible and dlg.baseChk.Value
        dlg.release()

        if (
            useSizers
            and not isDialog
            and self._reuseMainForm()
            and self.MainForm.UseSizers == useSizers
        ):
            # Original form hasn't changed, so just use it.
            frm = self.MainForm
        else:
            frmClass = self.getFormClass()
            frm = frmClass(parent=None, SaveRestorePosition=False, UseSizers=useSizers)
            frm._setupPanels(addBasePanel=addBasePanel)
        frm.UseSizers = useSizers
        frm.Controller = self
        self.CurrentForm = frm
        frm._formMode = isFormClass
        if not isFormClass:
            obj = self.addNewControl(frm.initLayoutPanel, newClass)
            frm.Caption = _("Class Designer: %s") % obj.Name
        if pth:
            frm._classFile = os.path.realpath(pth)
        frm.Visible = True
        ui.callAfter(frm.bringToFront)
        ui.callAfter(frm.saveState)
        return frm

    def wrapSave(self, func, *args, **kwargs):
        """Call the desired save method, and catch any error that is raised,
        displaying it to the user. If no error occurs, return True; otherwise,
        return False.
        """
        try:
            func(*args, **kwargs)
            return True
        except IOError as e:
            ui.stop(_("Save failed; reason: %s") % e)
            return False
        except Exception as e:
            ui.stop(_("Save failed; reason: %s") % e)
            raise e

    def onSaveRunnable(self, evt):
        if not self.wrapSave(self.CurrentForm.onSaveDesign, evt):
            return
        nm = self.CurrentForm.getClassFile()
        fpath, fname = os.path.split(nm)
        if isinstance(self.CurrentForm, dDialog):
            tmpl = self.miniDialogAppTemplate()
        else:
            tmpl = self.miniAppTemplate()
        code = tmpl % fname
        out = os.path.splitext(nm)[0] + ".py"
        try:
            codecs.open(out, "w", encoding="utf-8").write(code)
            ui.info(
                _("You can run your form by running the file\n%s") % out,
                title=_("Runnable App Saved"),
            )
        except IOError as e:
            ui.stop(_("Save failed; reason: %s") % e)

    def onRevert(self, evt):
        """Re-load the current design, losing any changes."""
        cf = self.CurrentForm
        pth = cf.getClassFile()
        if not pth:
            return
        cf.lockDisplay()
        newForm = self.openClass(pth)
        newForm.Position = cf.Position
        newForm.Size = cf.Size
        cf.unlockDisplay()
        ui.callAfter(cf.release)
        newForm.bringToFront()

    def onFileExit(self, evt):
        # If a design is being tested, don't exit the whole app,
        # just close that window.
        af = self.ActiveForm
        if af and af.TempForm:
            af.close()
            return
        else:
            # We're not running the demo, so quit the app
            super(ClassDesigner, self).onFileExit(evt)

    def onGridCellSelected(self, evt):
        if self.openingClassXML:
            # Not finished creating the controls yet...
            return
        colNum = evt.col
        gd = evt.EventObject
        if (colNum > -1) and (colNum < gd.ColumnCount):
            col = gd.Columns[colNum]
            self.select(col)

    def onGridHeaderSelected(self, evt):
        if self.openingClassXML:
            # Not finished creating the controls yet...
            return
        gd = evt.EventObject
        colNum = gd.getColNumByX(evt.mousePosition[0])
        if colNum != -1:
            col = gd.Columns[colNum]
            gd.CurrentColumn = colNum
            self.select(col)

    def getClassEvents(self, cls):
        return self._classEvents.get(cls, [])

    def getClassMethods(self, cls):
        evts = self._classEvents.get(cls, [])
        mthds = self._classMethods.get(cls, [])
        ret = evts + mthds
        ret.sort()
        return ret

    def menuUpdate(self, evt, mb):
        mn = evt.menuObject
        if mn is mb.getMenu("base_view"):
            prmDict = {False: (_("Hide"), _("Show")), True: (_("Show"), _("Hide"))}
            for item in mn.Children:
                if not hasattr(item, "Caption"):
                    # probably a separator
                    continue
                cap = item.Caption
                doReplace = False
                if _("Prop Sheet") in cap:
                    old, new = prmDict[self.PemForm.Visible]
                    doReplace = True
                if _("Code Editor") in cap:
                    old, new = prmDict[self.EditorForm.Visible]
                    doReplace = True
                elif _("Tool Palette") in cap:
                    old, new = prmDict[self.ControlPalette.Visible]
                    doReplace = True
                elif _("Sizer Palette") in cap:
                    old, new = prmDict[self.SizerPalette.Visible]
                    doReplace = True

                if doReplace:
                    item.Caption = cap.replace(old, new)

    def onShowProp(self, evt):
        pf = self.PemForm
        ui.callAfter(pf.showPropPage)

    def onShowObjTree(self, evt):
        pf = self.PemForm
        ui.callAfter(pf.showTreePage)

    def onShowMethods(self, evt):
        pf = self.PemForm
        ui.callAfter(pf.showMethodsPage)

    def onPriorObj(self, evt):
        self.moveInTree("prior")

    def onNextObj(self, evt):
        self.moveInTree("next")

    def moveInTree(self, drct):
        if self._inPropertyEditing:
            # Can't navigate while there is a pending change
            return
        if drct == "next":
            obj = self.Tree.nextObj()
        else:
            obj = self.Tree.priorObj()
        # Make sure that it is a live object
        if obj is not None:
            try:
                self.select(obj)
            except:
                pass

    def onTogglePropSheet(self, evt=None):
        self.togglePropSheet(self.barShowPropSheet)

    def onToggleEditor(self, evt=None):
        self.toggleEditor(self.barShowEditor)

    def onTogglePalette(self, evt=None):
        self.togglePalette(self.barShowPalette)

    def onToggleSizerPalette(self, evt=None):
        self.toggleSizerPalette(self.barShowSizerPalette)

    def togglePropSheet(self, menubar):
        # Ensure that the object is still alive
        junk = self.PemForm
        self._menuToggle(self.PemForm, menubar)

    def toggleEditor(self, menubar):
        # Ensure that the object is still alive
        junk = self.EditorForm
        self._menuToggle(self._editorForm, menubar)

    def togglePalette(self, menubar):
        # Ensure that the object is still alive
        junk = self.ControlPalette
        self._menuToggle(self.ControlPalette, menubar)

    def toggleSizerPalette(self, menubar):
        # Ensure that the object is still alive
        junk = self.SizerPalette
        self._menuToggle(self.SizerPalette, menubar)

    def _menuToggle(self, itm, bar):
        try:
            newVis = not itm.Visible
        except Exception:
            newVis = True
        itm.Visible = newVis

    def editCode(self, mthd=None, obj=None):
        ed = self.EditorForm
        ed.Visible = True
        if obj is None:
            obj = self._selection[0]
        ed.edit(obj, mthd)
        ui.callAfter(ed.bringToFront)

    def deleteObjectProperty(self, prop):
        """Removes a custom property from the object definition."""
        obj = self._selection[0]
        allprops = self._classPropDict.get(obj, {})
        propDict = allprops.get(prop, {})
        # This should delete the code for the property.
        data = {}
        data["getter"] = data["setter"] = data["deller"] = data["comment"] = None
        self.createPropertyCode(obj, prop, data=data, oldData=propDict)
        # Now delete the property definition
        try:
            del self._classPropDict[obj][prop]
        except Exception as e:
            dabo_module.log.error(
                _("Could not delete custom property '%(prop)s': %(e)s") % locals()
            )

    def editObjectProperty(self, prop):
        """Run the editor for the selected custom class property. If
        the passed prop is None, create a new property.
        """
        newPropCaption = _("NewProperty")
        adding = prop is None
        obj = self._selection[0]
        allprops = self._classPropDict.get(obj, {})
        propDict = allprops.get(prop, {})
        if adding or not propDict:
            # Initialize the props. Set the 'deller' to None, to let the
            # called dialog know that it should start off disabled.
            propDict["propName"] = newPropCaption
            propDict["comment"] = ""
            propDict["defaultValue"] = ""
            propDict["defaultType"] = ""
            propDict["getter"] = ""
            propDict["setter"] = ""
            propDict["deller"] = None
        else:
            for mthd in ("getter", "setter", "deller"):
                if propDict[mthd] == "None":
                    propDict[mthd] = None
        dlgProp = ClassDesignerCustomPropertyDialog()
        dlgProp.setData(propDict)
        dlgProp.show()
        data = None
        if dlgProp.Accepted:
            data = dlgProp.getData()
        dlgProp.release()
        if data:
            if data["propName"]:
                if adding:
                    prop = data["propName"]
                try:
                    self._classPropDict[obj]
                except KeyError:
                    self._classPropDict[obj] = {}
                # Make sure that there are no single quotes in the comment
                self._classPropDict[obj][prop] = data
                self.createPropertyCode(obj, prop, data, oldData=propDict)
            else:
                # No prop name; delete the property
                try:
                    del self._classPropDict[obj][prop]
                except:
                    pass

    #                 self.createPropertyCode(obj, prop,

    def createPropertyCode(self, obj, prop, data, oldData=None):
        """After a custom property is modified, make sure that the
        required code is in place to support the property.
        """
        cd = self._codeDict.get(obj, {})
        getMethod = data["getter"]
        setMethod = data["setter"]
        delMethod = data["deller"]
        comment = data["comment"]
        propertyAtt = prop[0].lower() + prop[1:]

        # Add the get/set/del methods, if needed
        if getMethod is None:
            if oldData:
                oldMethod = oldData["getter"]
                try:
                    del cd[oldMethod]
                except:
                    pass
        else:
            getCodeText = cd.get(getMethod, "")
            if not getCodeText:
                # Create the skeleton of the method
                getCode = [
                    """def %s(self):
    try:
        return self._%s
    except AttributeError:
        return None"""
                    % (getMethod, propertyAtt)
                ]
                getCodeText = os.linesep.join(getCode)
            cd[getMethod] = getCodeText

        if setMethod is None:
            if oldData:
                oldMethod = oldData["setter"]
                try:
                    del cd[oldMethod]
                except:
                    pass
        else:
            setCodeText = cd.get(setMethod, "")
            if not setCodeText:
                # Create the skeleton of the method
                setCode = [
                    "def %s(self, val):" % setMethod,
                    "\tself._%s = val" % propertyAtt,
                ]
                setCodeText = os.linesep.join(setCode)
            cd[setMethod] = setCodeText

        if delMethod is None:
            if oldData:
                oldMethod = oldData["deller"]
                try:
                    del cd[oldMethod]
                except:
                    pass
        else:
            delCodeText = cd.get(delMethod, "")
            if not delCodeText:
                # Create the skeleton of the method
                delCode = ["def %s(self):" % delMethod, "\treturn"]
                delCodeText = os.linesep.join(delCode)
            cd[delMethod] = delCodeText
        # Update the main dict
        self._codeDict[obj] = cd
        # Refresh the Editor form
        self.EditorForm.refreshStatus()

    def getObjectHierarchy(self):
        return self.CurrentForm.getObjectHierarchy()

    def getDesignerWindows(self, frm=None):
        """Returns a list of the currently open designer surface windows."""
        return [
            win
            for win in self.uiForms
            if isinstance(win, ClassDesignerFormMixin) and win is not frm
        ]

    def designerFormClosing(self, frm):
        """Checks to see if there are no more available
        ClassDesigner windows. If not, terminate the app.
        """
        if isinstance(frm, (dDialog, dOkCancelDialog)):
            try:
                # May need to explicitly release these.
                frm.release()
            except:
                pass
        desWindows = self.getDesignerWindows(frm)
        if not desWindows:
            # No more designer windows left, so exit the app
            ui.callAfter(self.onFileExit, None)
        else:
            # Make sure that the selection is not part of the closing window
            select = self.Selection
            badsel = []
            for sel in select:
                if (sel is frm) or (hasattr(self, "Form") and (sel.Form is frm)):
                    badsel.append(sel)
            self.deselect(badsel)

    def deselect(self, objs):
        """Convenient shortcut for calling select() with remove=True."""
        self.select(objs, remove=True)

    def select(self, objs, shift=False, remove=False):
        """Called when an object or objects are selected. If the
        shift parameter is True, the currently selected objects
        remain selected.
        """
        if not isinstance(objs, list):
            objs = [objs]
        oldsel = self._selection[:]
        if remove:
            for obj in objs:
                try:
                    self._selection.remove(obj)
                except ValueError:
                    # Object is no longer in the list
                    pass
                try:
                    obj.Selected = False
                except AttributeError:
                    pass
        else:
            if not shift and (objs == self._selection):
                # No change
                return
            if shift:
                for obj in objs:
                    newsel = not obj in oldsel
                    if newsel:
                        self._selection.append(obj)
                    else:
                        self._selection.remove(obj)
            else:
                for obj in oldsel:
                    try:
                        obj.Selected = False
                    except AttributeError:
                        pass
                self._selection = []
                for obj in objs:
                    if obj is not None:
                        self._selection.append(obj)
        if len(self._selection) > 0:
            self._srcObj = self._selection[0]
        else:
            self._srcObj = self.CurrentForm
        self.CurrentForm.select(self._selection)
        self.PemForm.select(self._selection)
        self.Tree.select(self._selection)
        if self.EditorForm:
            self.EditorForm.select(self._selection)
        self.SizerPalette.select(self._selection)

    def treeSelect(self):
        """Called by the tree when a new selection has been made
        by the user.
        """
        ui.callAfter(self.afterTreeSelect)

    def afterTreeSelect(self):
        self.Tree._inAppSelection = True
        selObj = self.Tree.getSelection()
        self.select(selObj)
        # Ensure that if it is an object on a page,
        # that that page is active
        self.CurrentForm.ensureVisible(selObj)
        self.Tree._inAppSelection = False

    def getMainLayoutPanel(self, obj):
        """Called when a Page receives an add/delete event"""
        ret = None
        # See if it has an activePanel set
        if hasattr(obj, "activePanel"):
            ret = obj.activePanel
        if ret is None:
            if self.UseSizers:
                # Grab the first LayoutPanel
                lps = [ch for ch in obj.Children if isinstance(ch, LayoutPanel)]
                try:
                    ret = lps[0]
                except:
                    dabo_module.log.error(
                        _("Problem adding to a page: no ClassDesigner information.")
                    )
            else:
                ret = obj.mainPanel
        return ret

    def getActivePanel(self, pnl=None):
        """Returns a reference to the currently-selected panel"""
        if pnl is None:
            pnl = self._srcObj
        if pnl is None:
            pnl = self._selection[0]
        # Handle the odd behavior of pages and when adding
        # controls programmatically.
        if self.UseSizers and isinstance(pnl, (dPage, dForm, dFormMain)):
            pnl = self.getMainLayoutPanel(pnl)
            try:
                pnl.Sizer.release(releaseContents=True)
            except AttributeError:
                # No sizer, so ignore
                pass
        elif pnl is None and not self.UseSizers:
            pnl = self.CurrentForm.ActiveContainer
        return pnl

    def getTreeContextMenu(self, obj):
        """Accepts the object represented in the object tree, and returns
        the appropriate context menu, or None if no context menu is
        appropriate.
        """
        self._contextObj = obj
        try:
            ret = obj.createContextMenu()
        except Exception as e:
            print("NO ON CONTEXT", e)
            ret = None
        return ret

    def onSwitchOrientation(self, evt):
        """Called when the user selects a command to switch the sizer's Orientation."""
        obj = self._contextObj
        self._contextObj = None
        try:
            if obj.Orientation == "Horizontal":
                obj.Orientation = "Vertical"
            elif obj.Orientation == "Vertical":
                obj.Orientation = "Horizontal"
            ui.callAfterInterval(100, self.updateLayout)
        except:
            pass

    def onTreeSwitchSizerType(self, evt):
        """Switches between a non-border and a bordered sizer."""
        fromSz = self._contextObj
        ornt = fromSz.Orientation
        parent = fromSz.Parent
        setParentSizer = (fromSz.Parent is not None) and (fromSz.Parent.Sizer is fromSz)
        isInSizer = fromSz.ControllingSizer is not None
        if isInSizer:
            csz = fromSz.ControllingSizer
            pos = fromSz.getPositionInSizer()
            szProps = csz.getItemProps(fromSz)

        if isinstance(fromSz, dBorderSizer):
            toSz = LayoutSizer()
        else:
            toSz = LayoutBorderSizer(box=dBox(parent))
        toSz.Orientation = ornt
        memberItems = fromSz.Children
        members = [fromSz.getItem(mem) for mem in memberItems]
        memberProps = dict.fromkeys(members)
        for member in members:
            memberProps[member] = fromSz.getItemProps(member)
        for member in members[::-1]:
            fromSz.remove(member)

        # Delete the old sizer. We can use the onTreeDelete method, since
        # the _contextObject is the same.
        self.onTreeDelete(evt)
        if setParentSizer:
            parent.Sizer = toSz
        if isInSizer:
            itm = csz.insert(pos, toSz)
            csz.setItemProps(itm, szProps)
        for member in members:
            itm = toSz.append(member)
            toSz.setItemProps(itm, memberProps[member])
        ui.callAfterInterval(100, self.updateLayout)

    def onTreeEditSizer(self, evt):
        self.editSizerSettings(self._contextObj)

    def onTreeCut(self, evt):
        obj = self._contextObj
        self.copyObject(obj)
        self.onTreeDelete(evt)

    def onTreeCopy(self, evt):
        obj = self._contextObj
        self.copyObject(obj)

    def onTreePaste(self, evt):
        obj = self._contextObj
        self.pasteObject(obj)

    def onTreeDelete(self, evt):
        obj = self._contextObj
        isSizer = isinstance(obj, dSizerMixin)
        if isSizer:
            obj.Form.removeFromOutlinedSizers(obj)
        if hasattr(obj, "onDelete"):
            obj.onDelete(evt)
            return
        csz = obj.ControllingSizer
        if csz:
            # I can't remember the use case for passing False, but I'm
            # leaving this here in case it comes back up.
            refill = not isinstance(obj, LayoutPanel)
            csz.delete(obj, refill=refill)
        elif isSizer:
            try:
                if obj.Parent.Sizer is obj:
                    obj.Parent.Sizer = None
            except:
                pass
            obj.release(True)
            ui.callAfterInterval(100, self.updateLayout)
        else:
            obj.release()
            ui.callAfterInterval(100, self.updateLayout)

    def getDefaultSizerProps(self, cls, szType):
        """Given a class to be added to the design surface, returns
        a dict containing the sizer defaults for that class.
        # NOTE: this will eventually be made user-configurable.
        """
        return DesignerUtils.getDefaultSizerProps(cls, szType)

    def _afterAddNewControlSplitter(self, obj, attProperties):
        # Add the panels
        pnlClass = self.getControlClass(obj.PanelClass)
        obj.createPanes(cls=pnlClass)
        if attProperties is None or ("Split" not in attProperties):
            obj.Split = True
        try:
            obj.Panel1.Sizer = LayoutSizer("v")
            LayoutPanel(obj.Panel1)
        except AttributeError:
            pass
        try:
            obj.Panel2.Sizer = LayoutSizer("v")
            LayoutPanel(obj.Panel2)
        except AttributeError:
            pass

    def _afterAddNewControlWizardPage(self, obj):
        if not attProperties:
            # Being added as a new page; need to add the child panel
            LayoutPanel(obj)
            # Set a default title
            cap = ui.getString(
                _("Enter the page Caption:"),
                caption=_("Wizard Page Caption"),
                defaultValue=_("Title"),
            )
            if not cap:
                cap = default = _("Title")
            obj.Caption = cap

    def _afterAddNewControlPaged(self, obj, pcount, classFlagProp, pgCls, useSizers):
        pgCls = obj.PageClass
        if isinstance(pgCls, str):
            # Saved class; let the control handle it
            obj.PageCount = pcount
            # This is the key that marks it as a class, and not a base object.
            prop = classFlagProp
            for pg in obj.Pages:
                pg.__setattr__(prop, pgCls)
            pg0panel = obj.Pages[0]
        else:
            pgCtlCls = self.getControlClass(pgCls)
            obj.PageClass = pgCtlCls
            obj.PageCount = pcount
            pg0panel = None
            if useSizers:
                for pg in obj.Pages[::-1]:
                    if not pg.Sizer or not isinstance(
                        pg.Sizer, (LayoutSizer, LayoutBorderSizer, LayoutGridSizer)
                    ):
                        pg.Sizer = LayoutSizer("v")
                        pg0panel = LayoutPanel(pg)
        return pg0panel

    def _afterAddNewControlSlidePanel(self, obj, classFlagProp, pcount, useSizers):
        pnlCls = obj.PanelClass
        if isinstance(pnlCls, str):
            # Saved class; let the control handle it
            obj.PanelCount = pcount
            # This is the key that marks it as a class, and not a base object.
            prop = classFlagProp
            for pnl in obj.Panels:
                pnl.Expanded = False
                pnl.__setattr__(prop, pnlCls)
            pnl0 = obj.Panels[0]
        else:
            pnlCtlCls = self.getControlClass(pnlCls)
            basePanelCls = self.getControlClass(dPanel)
            obj.PanelClass = pnlCtlCls
            obj.PanelCount = pcount
            pnl0 = None
            for pnl in obj.Panels[::-1]:
                pnl.Expanded = False
                if useSizers:
                    sz = pnl.Sizer = LayoutSizer("v")
                    sz.Parent = pnl
                    pnl0 = LayoutPanel(pnl)
        return pnl0

    def addNewControl(self, pnl, cls, props=None, attProperties=None, skipUpdate=False):
        """We need to replace the layout panel with an instance of
        the specified class. First, though, we need to grab all of the
        information from the sizer/ sizer item that controls the
        panel.
        """
        pnl = self.getActivePanel(pnl)
        if pnl is None:
            # Nothing to add to!
            return
        useSizers = self.CurrentForm.UseSizers
        if useSizers and hasattr(pnl, "isDesignerControl"):
            # Cannot add to a control, since the control will be released
            return
        if props is None:
            props = {}
        if useSizers:
            sz = pnl.ControllingSizer
            szit = pnl.ControllingSizerItem
            if szit is None:
                # Something is wrong; write it to the log and return
                dabo_module.log.error(
                    _(
                        "Attempted to add an object of class %(cls)s to parent %(pnl)s, but parent has no sizer information."
                    )
                    % locals()
                )
                return

            grdsz = isinstance(szit, dSizer.GridSizerItem)
            if grdsz:
                szType = "Grid"
            else:
                szType = sz.Orientation
            # Get the defaults for this class of control.
            itmProps = self.getDefaultSizerProps(cls, szType)
            #             if self.openingClassXML:
            #                 # Any existing panel is an artifact of the construction process,
            #                 # so we can ignore its properties.
            #                 itmDefaultProps = currItemProps = {}
            #             else:
            # Get the current props for the layout panel.
            currItemProps = sz.getItemProps(szit)
            # We need to see which ones have changed. Those
            # will override the defaults for the class.
            itmDefaultProps = pnl._defaultSizerProps
            changedDefaults = currItemProps.copy()
            for key, val in list(itmDefaultProps.items()):
                if changedDefaults.get(key, None) == val:
                    changedDefaults.pop(key)
            # Now get the defaults that are used to determine saved values
            if grdsz:
                savDefs = szItemDefaults[2].copy()
            else:
                savDefs = szItemDefaults[1].copy()
            savDefs.update(changedDefaults)
            # Now update the item props
            #            itmProps.update(savDefs)
            itmProps.update(changedDefaults)
            if grdsz:
                oldrow, oldcol = sz.getGridPos(pnl)
            else:
                pos = pnl.getPositionInSizer()
            parent = pnl.Parent
        else:
            sz = szit = None
            parent = pnl

        isPageControl = issubclass(cls, self.pagedControls)
        isTree = issubclass(cls, dTreeView)
        isGrid = issubclass(cls, dGrid)
        isSlidePanelControl = issubclass(cls, dSlidePanelControl)
        isRadioList = issubclass(cls, dRadioList)
        if isPageControl:
            noTabs = issubclass(cls, dPageFrameNoTabs)
            pgCls = None
            defaultPgClsDisplay = _("<default>")
            if not useSizers:
                props["PageSizerClass"] = None

            if not props.get("PageCount", 0):
                dlg = PageInfoDialog(
                    self.CurrentForm,
                    NoTabs=noTabs,
                    BasePrefKey=self.BasePrefKey + ".PageInfoDialog",
                )
                dlg.AutoSize = False
                dlg.Centered = True
                dlg.show()
                if not dlg.Accepted:
                    # User canceled
                    dlg.release()
                    return
                try:
                    newPgs = dlg.pageCount
                    tabPos = dlg.tabPositions[dlg.tabPosSelection]
                except:
                    newPgs = 3
                    tabPos = "Top"
                try:
                    if dlg.pageClass == defaultPgClsDisplay:
                        pgCls = ""
                    else:
                        pgCls = dlg.pageClass
                except:
                    pgCls = ""
                if not pgCls:
                    pgCls = dPage

                dlg.release()
                props["PageCount"] = newPgs
                props["PageClass"] = pgCls
                if not noTabs:
                    props["TabPosition"] = tabPos
            else:
                if not props.get("TabPosition") and not noTabs:
                    props["TabPosition"] = "Top"

        if isTree:
            # Make sure it adds customized nodes.
            props["NodeClass"] = self.getControlClass(dTreeView.getBaseNodeClass())

        if isGrid:
            # Make sure it adds customized columns.
            props["ColumnClass"] = self.getControlClass(dColumn)
            newCols = None
            try:
                props["ColumnCount"]
            except KeyError:
                try:
                    newCols = int(ui.getString(_("How many columns?"), _("New Grid Control"), "3"))
                except ValueError:
                    newCols = 3

        if isSlidePanelControl:
            # Make sure it has some panels.
            newPanels = None
            cnt = props.get("PanelCount", 0)
            if not cnt:
                try:
                    newPanels = int(
                        ui.getString(_("How many panels?"), _("New Slide Container"), "3")
                    )
                except ValueError:
                    newPanels = 3
                props["PanelCount"] = newPanels

        if useSizers:
            # Need to notify the tree that an update to a node will be
            # happening. Get the affected node
            nd = self.Tree.getNodeFor(pnl)
            sz.remove(pnl)
            ui.callAfter(pnl.release)

        if issubclass(cls, dSplitter):
            # We need to disable the initial splitting. This will be done
            # after the control is created.
            soi = self._extractKey((props, attProperties), "splitOnInit")
            props["splitOnInit"] = False

        isSavedClass = self._extractKey(attProperties, "savedClass") == "True"
        classID = self._extractKey(attProperties, "classID")
        attNmBase = propNmBase = ""
        if attProperties is not None:
            attNmBase = attProperties.get("NameBase", "")
        if props is not None:
            propNmBase = props.get("NameBase", "")

        # Delay the creation of pages
        if isPageControl:
            pcount = props["PageCount"]
            props["PageCount"] = 0

        # Delay the creation of pages
        if isSlidePanelControl:
            pcount = props["PanelCount"]
            props["PanelCount"] = 0

        # Make sure that the RadioList's components are Designer-aware
        if isRadioList:
            props["SizerClass"] = LayoutBorderSizer
            props["ButtonClass"] = self.getControlClass(dRadioList.getBaseButtonClass())

        # Here's where the control is actually created!
        mixedClass = self.getControlClass(cls)
        obj = mixedClass(parent, properties=props, attProperties=attProperties)
        if isTree:
            obj.addDummyData()
        if attNmBase and attNmBase != "controlMix":
            obj.NameBase = attNmBase
        elif propNmBase and propNmBase != "controlMix":
            obj.NameBase = propNmBase

        if useSizers:
            if grdsz:
                sz.append(obj, row=oldrow, col=oldcol)
            else:
                sz.insert(pos, obj)
        else:
            if self._srcPos is not None:
                # Get the top left corner of the object's Parent.
                parentPos = obj.Parent.formCoordinates((0, 0))
                # Translate the _srcPos, which is relative to the form, to a position
                # that is relative to the object's Parent.
                obj.Position = (
                    self._srcPos[0] - parentPos[0],
                    self._srcPos[1] - parentPos[1],
                )
                self._srcPos = None

        if issubclass(cls, dSplitter):
            self._afterAddNewControlSplitter(obj, attProperties)
        elif issubclass(cls, WizardPage):
            self._afterAddNewControlWizardPage(obj)
        elif isPageControl:
            pg0panel = self._afterAddNewControlPaged(obj, pcount, classFlagProp, pgCls, useSizers)
        elif isSlidePanelControl:
            pnl0 = self._afterAddNewControlSlidePanel(obj, classFlagProp, pcount, useSizers)

        if isinstance(obj, dPage) and not isinstance(obj.Parent, self.pagedControls):
            # This is a free standing page being designed. Add the sizer, if required.
            if useSizers:
                obj.Sizer = LayoutSizer("v")
                LayoutPanel(obj)

        if useSizers:
            newitem = obj.ControllingSizerItem
            sz.setItemProps(newitem, itmProps)
        else:
            # If sizes are not explicitly set, set them to the minimum
            if attProperties is None:
                chkWd = chkHt = True
            else:
                chkWd = ("Size" not in attProperties) and ("Width" not in attProperties)
                chkHt = ("Size" not in attProperties) and ("Height" not in attProperties)
            ui.callAfter(self.checkMinSize, obj, chkWd, chkHt)

        try:
            frm = obj.Form
            if frm._formMode:
                ui.callAfterInterval(500, obj.Form.layout)
            else:
                # class mode
                mp = frm.mainPanel
                if obj.Parent is mp:
                    obj.Position = (0, 0)
                    mp.Width, mp.Height = obj.Width + 10, obj.Height + 10
                else:
                    ui.callAfterInterval(500, obj.Form.layout)
        except:
            pass

        # Update the affected tree node
        if useSizers:
            if nd is not None:
                nd.Object = obj
        else:
            self.Tree.updateDisplay(self.CurrentForm)

        if issubclass(cls, dGrid):
            if newCols is not None:
                obj.ColumnCount = newCols
                obj.emptyRowsToAdd = 5
                obj.fillGrid()

        if not skipUpdate:
            if useSizers and isPageControl:
                ui.callAfter(self.select, pg0panel)
            elif useSizers and isSlidePanelControl:
                ui.callAfter(self.select, pnl0)
            else:
                ui.callAfter(self.select, obj)
            try:
                obj.layout()
            except AttributeError:
                # The object does not have a layout() method
                pass
            ui.callAfterInterval(100, self.updateLayout)
        return obj

    def getControlClass(self, base):
        if issubclass(base, cmix):
            # Already mixed-in
            return base
        ret = self._mixedControlClasses.get(base, None)
        if not ret:
            # Create a pref key that is the Designer key plus the name of the control
            prefkey = self.BasePrefKey + "." + ustr(base).split(".")[-1].split("'")[0]

            class controlMix(cmix, base):
                superControl = base
                superMixin = cmix

                def __init__(self, *args, **kwargs):
                    if hasattr(base, "__init__"):
                        base.__init__(*(self,) + args, **kwargs)
                    parent = args[0]
                    cmix.__init__(self, parent, **kwargs)
                    self.NameBase = ustr(self._baseClass).split(".")[-1].split("'")[0]
                    self.BasePrefKey = prefkey

            ret = controlMix
            self._mixedControlClasses[base] = ret
        return ret

    def checkMinSize(self, obj, chkWd, chkHt):
        """If an object is created in a non-sizer environment, make sure
        that if the size is not specified, the object is at least a reasonable
        minimum size.
        """
        if chkWd and (obj.Width < obj.defaultWd):
            obj.Width = obj.defaultWd
        if chkHt and (obj.Height < obj.defaultHt):
            obj.Height = obj.defaultHt

    def addSlotOptions(self, obj, pop, sepBefore=False, sepAfter=False):
        """Takes an object and a context menu, and adds the appropriate options
        depending on its position in the design surface.
        """
        self._contextObj = obj
        try:
            sz = obj.ControllingSizer
        except AttributeError:
            # Some objects, such as grid columns and pages, do not have a ControllingSizer
            return False
        items = []
        if isinstance(sz, (dSizer, dBorderSizer)):
            if sz.Orientation == "Vertical":
                items.append((_("Add Slot Above"), self.onAddSlotBefore))
                items.append((_("Add Slot Below"), self.onAddSlotAfter))
            else:
                items.append((_("Add Slot Left"), self.onAddSlotBefore))
                items.append((_("Add Slot Right"), self.onAddSlotAfter))
            pos = obj.getPositionInSizer()
            if pos > 0:
                if sz.Orientation == "Vertical":
                    direc = _("Up")
                else:
                    direc = _("Left")
                items.append((_("Move %s One Slot") % direc, self.onMoveSlotUp))
            if pos < len(sz.Children) - 1:
                if sz.Orientation == "Vertical":
                    direc = _("Down")
                else:
                    direc = _("Right")
                items.append((_("Move %s One Slot") % direc, self.onMoveSlotDown))
        elif isinstance(sz, dGridSizer):
            pos = sz.getGridPos(obj)
            if pos != (0, 0):
                items.append((_("Move Up One Slot"), self.onMoveSlotUp))
            if not ((sz.MaxDimension == "r") and (pos[0] >= sz.MaxRows)):
                items.append((_("Move Down One Slot"), self.onMoveSlotDown))
            if pos[1] > 0:
                items.append((_("Move Left One Slot"), self.onMoveSlotLeft))
            if not ((sz.MaxDimension == "c") and (pos[1] >= sz.MaxCols)):
                items.append((_("Move Right One Slot"), self.onMoveSlotRight))
        if items:
            if sepBefore:
                pop.appendSeparator()
            for cap, func in items:
                pop.append(cap, OnHit=func)
            if sepAfter:
                pop.appendSeparator()
        return True

    def onAddSlotBefore(self, evt):
        self._addEmptySlot(0)

    def onAddSlotAfter(self, evt):
        self._addEmptySlot(1)

    def _addEmptySlot(self, offset):
        obj = self._contextObj
        self._contextObj = None
        if not obj:
            return
        lp = LayoutPanel(obj.Parent, AutoSizer=False)
        obj.ControllingSizer.insert(obj.getPositionInSizer() + offset, lp, 1, "x")
        ui.callAfterInterval(100, self.updateLayout)

    def onMoveSlotUp(self, evt):
        obj = self._contextObj
        sz = obj.ControllingSizer
        if isinstance(sz, (dSizer, dBorderSizer)):
            self._moveVertically(obj, sz, -1)
        elif isinstance(sz, dGridSizer):
            sz.switchObjects(obj, sz.getNeighbor(obj, "up"))
        ui.callAfterInterval(100, self.updateLayout)

    def onMoveSlotDown(self, evt):
        obj = self._contextObj
        sz = obj.ControllingSizer
        if isinstance(sz, (dSizer, dBorderSizer)):
            self._moveVertically(obj, sz, 1)
        elif isinstance(sz, dGridSizer):
            target = sz.getNeighbor(obj, "down")
            if target is None:
                # We're at the bottom row of the design, so add a row
                sz.Rows += 1
                target = sz.getNeighbor(obj, "down")
            sz.switchObjects(obj, target)
        ui.callAfterInterval(100, self.updateLayout)

    def _moveVertically(self, obj, sz, drct):
        pos = obj.getPositionInSizer()
        props = sz.getItemProps(obj)
        sz.remove(obj)
        sz.insert(pos + drct, obj)
        sz.setItemProps(obj, props)
        sz.layout()

    def onMoveSlotLeft(self, evt):
        obj = self._contextObj
        sz = obj.ControllingSizer
        sz.switchObjects(obj, sz.getNeighbor(obj, "left"))
        ui.callAfterInterval(100, self.updateLayout)

    def onMoveSlotRight(self, evt):
        obj = self._contextObj
        sz = obj.ControllingSizer
        target = sz.getNeighbor(obj, "right")
        if target is None:
            # We're at the rightmost column of the design, so add a col.
            sz.Columns += 1
            target = sz.getNeighbor(obj, "right")
        sz.switchObjects(obj, target)
        ui.callAfterInterval(100, self.updateLayout)

    def getControlMenu(self, srcObj, justSizers=False):
        """Creates the popup menu for selecting child objects"""
        # Store the source object
        self._srcObj = srcObj
        self._srcPos = ui.getFormMousePosition()

        mainpop = dMenu()
        if self.UseSizers:
            pop = dMenu(Caption=_("Sizers"))
            pop.append(_("Add New Vertical Sizer"), OnHit=self.onNewVert)
            pop.append(_("Add New Horizontal Sizer"), OnHit=self.onNewHoriz)
            pop.append(_("Add New Spacer"), OnHit=self.onNewSpacer)
            pop.append(_("Add New Grid Sizer"), OnHit=self.onNewGridSizer)
            mainpop.appendMenu(pop)
        if not justSizers:
            pop = dMenu(Caption=_("Data Controls"))
            pop.append(_("Add CheckBox"), OnHit=self.onNewCheckBox)
            pop.append(_("Add Code Editor"), OnHit=self.onNewEditor)
            pop.append(_("Add ComboBox"), OnHit=self.onNewComboBox)
            pop.append(_("Add DateTextBox"), OnHit=self.onNewDateTextBox)
            pop.append(_("Add DropdownList"), OnHit=self.onNewDropdownList)
            pop.append(_("Add EditBox"), OnHit=self.onNewEditBox)
            pop.append(_("Add Grid"), OnHit=self.onNewGrid)
            pop.append(_("Add HtmlBox"), OnHit=self.onNewHtmlBox)
            pop.append(_("Add ListBox"), OnHit=self.onNewListBox)
            pop.append(_("Add ListControl"), OnHit=self.onNewListControl)
            pop.append(_("Add MaskedTextBox"), OnHit=self.onNewMaskedTextBox)
            pop.append(_("Add CheckList"), OnHit=self.onNewCheckList)
            pop.append(_("Add RadioList"), OnHit=self.onNewRadioList)
            pop.append(_("Add Spinner"), OnHit=self.onNewSpinner)
            pop.append(_("Add TextBox"), OnHit=self.onNewTextBox)
            pop.append(_("Add ToggleButton"), OnHit=self.onNewToggleButton)
            mainpop.appendMenu(pop)
            pop = dMenu(Caption=_("Display Controls"))
            pop.append(_("Add Box"), OnHit=self.onNewBox)
            pop.append(_("Add Bitmap"), OnHit=self.onNewBitmap)
            pop.append(_("Add Image"), OnHit=self.onNewImage)
            pop.append(_("Add Label"), OnHit=self.onNewLabel)
            pop.append(_("Add LED"), OnHit=self.onNewLed)
            pop.append(_("Add Line"), OnHit=self.onNewLine)
            try:
                dMediaControl
                pop.append(_("Add MediaControl"), OnHit=self.onNewMediaControl)
            except AttributeError:
                # dMediaControl was not imported; some earlier wx versions don't include this
                pass
            pop.append(_("Add Panel"), OnHit=self.onNewPanel)
            pop.append(_("Add ScrollPanel"), OnHit=self.onNewScrollPanel)
            pop.append(_("Add SlidePanelControl"), OnHit=self.onNewSlidePanelControl)
            pop.append(_("Add Splitter"), OnHit=self.onNewSplitter)
            mainpop.appendMenu(pop)
            pop = dMenu(Caption=_("Interactive Controls"))
            pop.append(_("Add BitmapButton"), OnHit=self.onNewBitmapButton)
            pop.append(_("Add Button"), OnHit=self.onNewButton)
            pop.append(_("Add Gauge"), OnHit=self.onNewGauge)
            pop.append(_("Add Interactive Shell"), OnHit=self.onNewShell)
            pop.append(_("Add Slider"), OnHit=self.onNewSlider)
            pop.append(_("Add TreeView"), OnHit=self.onNewTreeView)
            mainpop.appendMenu(pop)
            pop = dMenu(Caption=_("Paged Controls"))
            pop.append(_("Add PageFrame"), OnHit=self.onNewPageFrame)
            pop.append(_("Add PageList"), OnHit=self.onNewPageList)
            pop.append(_("Add PageSelect"), OnHit=self.onNewPageSelect)
            pop.append(_("Add PageStyled"), OnHit=self.onNewPageStyled)
            pop.append(_("Add PageNoTabs"), OnHit=self.onNewPageNoTabs)
            mainpop.appendMenu(pop)
            pop = dMenu(Caption=self._customClassCaption)
            pop.append(_("Select..."), OnHit=self.onSelectClass)
            self.onMenuOpenMRU(pop)
            mainpop.appendMenu(pop)
        return mainpop

    def onSelectClass(self, evt):
        """Handles when the user chooses the 'Select...' option
        for custom classes. Prompts the user for a class file, and
        then adds that to the design.
        """
        pth = ui.getFile("cdxml")
        if not pth:
            return
        self.addCustomClass(pth)

    def addCustomClass(self, pathOrEvent):
        """Adds a saved class to a slot in the design. Can be called
        by either the onSelectClass() method, in which case a path
        is passed, or by an MRU selection, in which case a menu event
        is passed.
        """
        if isinstance(pathOrEvent, str):
            pth = pathOrEvent
        else:
            # Picked from an MRU list
            try:
                pth = pathOrEvent.prompt
            except AttributeError:
                # Windows menus are messed up!
                pth = pathOrEvent.EventObject.Caption
            while pth[0] in ("& 0123456789"):
                # Strip out the ordering information
                pth = pth[1:]
        self.addToMRU(self._customClassCaption, pth, self.addCustomClass)
        clsd = self._importClassXML(pth)
        # We need to replace the 'designerClass' attribute so that
        # recreateChildren() knows what to add.

        # If the source object is in a sizer, we need to pass that along
        try:
            szr = self._srcObj.ControllingSizer
        except:
            szr = None
        # OK, add it in...
        self._basePath = self._srcObj.Form._classFile

        isMainPanel = self._extractKey(clsd["attributes"], "mainPanel", "False")
        ac = self._addingClass
        self._addingClass = True
        mainObj = self.recreateChildren(self._srcObj, clsd, szr, fromSizer=(szr is not None))
        self._addingClass = ac
        self._basePath = None
        # This is the key that marks it as a class, and not a base object.
        prop = classFlagProp
        mainObj.__setattr__(prop, pth)
        ui.callAfterInterval(100, self.updateLayout)
        return mainObj

    def setCustomChanges(self, obj, dct):
        """This takes a custom object that has been saved as part
        of another design, and applies the changes saved with it
        to itself and any children.
        """
        atts = dct["attributes"]
        # Convert any paths in the atts
        try:
            pth = obj.Form._classFile
        except:
            pth = None
        libutils.resolveAttributePathing(atts, pth)
        code = dct.get("code", {})
        sizerInfo = self._extractKey(atts, "sizerInfo", "{}")
        if isinstance(sizerInfo, str):
            sizerInfoDict = eval(sizerInfo)
        else:
            sizerInfoDict = sizerInfo
        try:
            sz = obj.ControllingSizer
            sz.setItemProps(obj.ControllingSizerItem, sizerInfoDict)
        except:
            pass

        if code:
            # There is custom code overriding the class code. Use that
            cd = self._codeDict.get(obj, {})
            cd.update(code)
            self._codeDict[obj] = cd

        for att, val in list(atts.items()):
            if att in ("children", "classID", "code-ID", "designerClass", "SlotCount"):
                continue
            elif att == "savedClass":
                obj.savedClass = True
            else:
                try:
                    exec("obj.%s = %s" % (att, val))
                except:
                    # If this is attribute holds strings, we need to quote the value.
                    escVal = val.replace('"', '\\"').replace("'", "\\'")
                    try:
                        exec("obj.%s = '%s'" % (att, escVal))
                    except:
                        raise ValueError(
                            _("Could not set attribute '%(att)s' to value: %(val)s") % locals()
                        )
        # If the item has children, set their atts, too.
        isSizer = isinstance(obj, dSizerMixin)
        if isSizer:
            if obj.Children:
                childList = dct["children"]
                kidList = []
                for kidItem in obj.Children:
                    if kidItem.IsWindow():
                        kidList.append(kidItem.GetWindow())
                    elif kidItem.IsSizer():
                        kidList.append(kidItem.GetSizer())
                    else:
                        # spacer; nothing to do.
                        continue
                for kid in kidList:
                    try:
                        kidID = kid.classID
                    except:
                        # Not a class member
                        continue
                    try:
                        kidDct = [cd for cd in childList if cd["attributes"]["classID"] == kidID][0]
                        self.setCustomChanges(kid, kidDct)
                    except Exception as e:
                        dabo_module.log.error(_("Error locating sizer: %s") % e)
        else:
            if obj.Sizer:
                childList = dct["children"]
                szID = obj.Sizer.classID
                try:
                    szDct = [cd for cd in childList if cd["attributes"]["classID"] == szID][0]
                    self.setCustomChanges(obj.Sizer, szDct)
                except Exception as e:
                    dabo_module.log.error(_("Error locating sizer: %s") % e)
            else:
                if obj.Children:
                    childList = dct["children"]
                    for kid in obj.Children:
                        if not hasattr(kid, "classID"):
                            continue
                        kidID = kid.classID
                        try:
                            kidDct = [
                                cd for cd in childList if cd["attributes"]["classID"] == kidID
                            ][0]
                            self.setCustomChanges(kid, kidDct)
                        except Exception as e:
                            dabo_module.log.error(_("Error locating child object: %s") % e)

    def onNewBox(self, evt):
        ui.callAfter(self.addNewControl, None, dBox)

    def onNewBitmap(self, evt):
        ui.callAfter(self.addNewControl, None, dBitmap)

    def onNewBitmapButton(self, evt):
        ui.callAfter(self.addNewControl, None, dBitmapButton)

    def onNewButton(self, evt):
        ui.callAfter(self.addNewControl, None, dButton)

    def onNewCheckBox(self, evt):
        ui.callAfter(self.addNewControl, None, dCheckBox)

    def onNewComboBox(self, evt):
        ui.callAfter(self.addNewControl, None, dComboBox)

    def onNewDateTextBox(self, evt):
        ui.callAfter(self.addNewControl, None, dDateTextBox)

    def onNewDropdownList(self, evt):
        ui.callAfter(self.addNewControl, None, dDropdownList)

    def onNewEditBox(self, evt):
        ui.callAfter(self.addNewControl, None, dEditBox)

    def onNewEditor(self, evt):
        ui.callAfter(self.addNewControl, None, dEditor)

    def onNewSlidePanelControl(self, evt):
        ui.callAfter(self.addNewControl, None, dSlidePanelControl)

    def onNewGauge(self, evt):
        ui.callAfter(self.addNewControl, None, dGauge)

    def onNewGrid(self, evt):
        ui.callAfter(self.addNewControl, None, dGrid)

    def onNewHtmlBox(self, evt):
        ui.callAfter(self.addNewControl, None, dHtmlBox)

    def onNewImage(self, evt):
        ui.callAfter(self.addNewControl, None, dImage)

    def onNewLabel(self, evt):
        ui.callAfter(self.addNewControl, None, dLabel)

    def onNewLed(self, evt):
        ui.callAfter(self.addNewControl, None, dLed)

    def onNewLine(self, evt):
        ui.callAfter(self.addNewControl, None, dLine)

    def onNewListBox(self, evt):
        ui.callAfter(self.addNewControl, None, dListBox)

    def onNewListControl(self, evt):
        ui.callAfter(self.addNewControl, None, dListControl)

    def onNewMaskedTextBox(self, evt):
        ui.callAfter(self.addNewControl, None, dMaskedTextBox)

    def onNewCheckList(self, evt):
        ui.callAfter(self.addNewControl, None, dCheckList)

    def onNewMediaControl(self, evt):
        try:
            ui.callAfter(self.addNewControl, None, dMediaControl)
        except AttributeError:
            # dMediaControl was not imported; some earlier wx versions don't include this
            pass

    def onNewRadioList(self, evt):
        ui.callAfter(self.addNewControl, None, dRadioList)

    def onNewPanel(self, evt):
        ui.callAfter(self.addNewControl, None, dPanel)

    def onNewPageFrame(self, evt):
        ui.callAfter(self.addNewControl, None, dPageFrame)

    def onNewPageList(self, evt):
        ui.callAfter(self.addNewControl, None, dPageList)

    def onNewPageSelect(self, evt):
        ui.callAfter(self.addNewControl, None, dPageSelect)

    def onNewPageStyled(self, evt):
        ui.callAfter(self.addNewControl, None, dPageStyled)

    def onNewPageNoTabs(self, evt):
        ui.callAfter(self.addNewControl, None, dPageFrameNoTabs)

    def onNewScrollPanel(self, evt):
        ui.callAfter(self.addNewControl, None, dScrollPanel)

    def onNewShell(self, evt):
        ui.callAfter(self.addNewControl, None, dShell)

    def onNewSlider(self, evt):
        ui.callAfter(self.addNewControl, None, dSlider)

    def onNewSpinner(self, evt):
        ui.callAfter(self.addNewControl, None, dSpinner)

    def onNewSplitter(self, evt):
        ui.callAfter(self.addNewControl, None, dSplitter)

    def onNewTextBox(self, evt):
        ui.callAfter(self.addNewControl, None, dTextBox)

    def onNewToggleButton(self, evt):
        ui.callAfter(self.addNewControl, None, dToggleButton)

    def onNewTreeView(self, evt):
        ui.callAfter(self.addNewControl, None, dTreeView)

    def onNewSpacer(self, evt):
        return self.addSizer("spacer")[0]

    def onNewVert(self, evt):
        return self.addSizer("box", orient="v")[0]

    def onNewHoriz(self, evt):
        return self.addSizer("box", orient="h")[0]

    def onNewGridSizer(self, evt=None, pnl=None, rows=None, cols=None):
        return self.addSizer("grid", pnl=pnl, rows=rows, cols=cols)[0]

    def addSizer(
        self,
        szType,
        pnl=None,
        orient="",
        slots=None,
        rows=None,
        cols=None,
        spacing=None,
        useBox=None,
        boxCaption=None,
    ):
        nullReturn = None, None
        controllingSizer, sizerPos, pnlToKill = None, None, None
        isSpacer = szType.lower() == "spacer"
        isOneDim = szType.lower() == "box"
        if pnl is None:
            obj = self._srcObj
        else:
            obj = pnl
        if isinstance(obj, dPage):
            # Get the layout panel
            obj = self.getMainLayoutPanel(obj)
        try:
            sizerAtts = obj.getDesignerDict()["attributes"]["sizerInfo"]
            if sizerAtts.get("Expand") is None:
                sizerAtts["Expand"] = True
            if sizerAtts.get("Proportion") is None:
                sizerAtts["Proportion"] = 1
        except:
            sizerAtts = None
        while isinstance(obj, LayoutPanel):
            if controllingSizer is None:
                controllingSizer = obj.ControllingSizer
                sizerPos = obj.getPositionInSizer()
                pnlToKill = obj
            # Set the controlling sizer info
            obj = obj.Parent

        if isSpacer:
            if spacing is not None:
                spc = spacing
                if isinstance(spc, str):
                    spc = eval(spc)
            else:
                if isinstance(controllingSizer, LayoutGridSizer):
                    rows, cols = 1, 1
                spc = ui.getString(
                    message=_("Spacer Dimension?"),
                    caption=_("New Spacer"),
                    defaultValue="10",
                )
                if isinstance(spc, str):
                    spc = int(spc)
                else:
                    # They canceled
                    return nullReturn

        elif isOneDim:
            if slots is None:
                slots, useBox, boxCaption = self.getSizerInfo()
                if not slots:
                    # User canceled
                    return nullReturn
        else:
            # Grid sizer
            if rows is None or cols is None:
                rows, cols = self.getNumRowCol()
            if rows is None:
                # User canceled
                return nullReturn

        sizerKids = 0
        if controllingSizer:
            sizerKids = len(controllingSizer.Children)

        useExisting = False
        if sizerKids <= 1 and not isSpacer:
            # Make sure that it is the same type of sizer
            if isOneDim:
                if (not useBox and isinstance(controllingSizer, LayoutSizer)) or (
                    useBox and isinstance(controllingSizer, LayoutBorderSizer)
                ):
                    useExisting = True
                    esa = controllingSizer.getDesignerDict(allProps=True)["attributes"]
                    for key in list(self._defBoxSizerAtts.keys()):
                        if not esa[key] == self._defBoxSizerAtts[key]:
                            useExisting = False
                            break
            elif not isOneDim and isinstance(controllingSizer, LayoutGridSizer):
                useExisting = True
                esa = controllingSizer.getDesignerDict(allProps=True)["attributes"]
                for key in list(self._defGridSizerAtts.keys()):
                    if not esa[key] == self._defGridSizerAtts[key]:
                        useExisting = False
                        break

        if useExisting:
            # Basic sizer with nothing added yet.
            newSizer = controllingSizer
            if isOneDim:
                controllingSizer.Orientation = orient
                if useBox:
                    controllingSizer.Box.Caption = boxCaption
                for ii in range(slots - 1):
                    lp = LayoutPanel(obj, AutoSizer=False)
                    itm = controllingSizer.append1x(lp)
                    lp._defaultSizerProps = newSizer.getItemProps(itm)
            else:
                # First, release the panel
                if controllingSizer:
                    controllingSizer.remove(pnlToKill)
                ui.callAfter(pnlToKill.release)
                # If the controllingSizer is controlled by another
                # sizer, remove it and replace it with a grid sizer.
                # If there is no controlling sizer, set the Parent
                # object's sizer to the grid sizer.
                newSizer = LayoutGridSizer(MaxCols=cols)
                newSizer.Rows, newSizer.Columns = rows, cols
                for win in newSizer.ChildWindows:
                    win._defaultSizerProps = newSizer.getItemProps(win)
                if controllingSizer.ControllingSizer is not None:
                    cscs = controllingSizer.ControllingSizer
                    pos = controllingSizer.getPositionInSizer()
                    cscs.remove(controllingSizer)
                    cscs.insert(pos, newSizer)
                else:
                    controllingSizer.Parent.Sizer = newSizer
        else:
            if isSpacer:
                inGrid = isinstance(controllingSizer, LayoutGridSizer)
                newSizer = LayoutSpacerPanel(
                    obj, Spacing=spc, orient=controllingSizer.Orientation, inGrid=inGrid
                )
            elif isOneDim:
                if useBox:
                    newSizer = LayoutBorderSizer(
                        box=dBox(obj), caption=boxCaption, orientation=orient
                    )
                else:
                    newSizer = LayoutSizer(orient)
            else:
                newSizer = LayoutGridSizer(MaxCols=cols)

            if controllingSizer is not None:
                controllingSizer.remove(pnlToKill)
                ui.callAfter(pnlToKill.release)
                if isinstance(sizerPos, tuple):
                    rr, cc = sizerPos
                    oldItem = controllingSizer.getItemByRowCol(rr, cc)
                    if oldItem:
                        controllingSizer.remove(oldItem)
                    szItem = controllingSizer.append(newSizer, row=rr, col=cc)
                else:
                    szItem = controllingSizer.insert(sizerPos, newSizer)
            else:
                obj.Sizer = newSizer

            if isOneDim:
                if slots:
                    for ii in range(slots):
                        lp = LayoutPanel(obj, AutoSizer=False)
                        itm = newSizer.append1x(lp)
                        lp._defaultSizerProps = newSizer.getItemProps(itm)
            elif isSpacer:
                pass
            else:
                newSizer.Rows, newSizer.Columns = rows, cols
                newSizer.setFullExpand()
                for win in newSizer.ChildWindows:
                    win._defaultSizerProps = newSizer.getItemProps(win)

        try:
            itm = newSizer.ControllingSizerItem
        except:
            itm = None
        if itm:
            if isinstance(newSizer.Parent, dSlidePanel):
                # This is the main sizer
                itm = None
        if itm:
            if sizerAtts:
                if isSpacer:
                    sizerAtts["Proportion"] = 0
                    sizerAtts["Halign"] = "center"
                    sizerAtts["Valign"] = "middle"
                if not hasattr(itm, "ControllingSizer"):
                    itm.ControllingSizer = itm.GetUserData()
                newSizer.ControllingSizer.setItemProps(itm, sizerAtts)
        try:
            ui.callAfterInterval(obj.Form.layout, 500)
        except:
            try:
                ui.callAfterInterval(obj.layout, 500)
            except:
                pass
        ui.callAfterInterval(100, self.updateLayout)
        return newSizer, obj

    def getSizerInfo(self):
        defaultSlotCount = 3

        class BoxSizerInfo(dOkCancelDialog):
            def addControls(self):
                self.Modal = True
                self.Caption = _("Sizer Information")
                self.Sizer.DefaultSpacing = 10
                hsz = dSizer("h")
                lbl = dLabel(self, Caption=_("Number of Slots:"))
                txt = dSpinner(self, RegID="slotcount", Value=defaultSlotCount, Min=1)
                hsz.append(lbl, halign="right")
                hsz.appendSpacer(4)
                hsz.append(txt, 1, halign="left")
                self.Sizer.append(hsz, halign="center")

                chk = dCheckBox(self, RegID="chkBox", Caption=_("Add Sizer Box?"))
                self.Sizer.append(chk, halign="center")

                self.boxCaptionSizer = hsz = dSizer("h")
                lbl = dLabel(self, Caption=_("Box Caption:"))
                txt = dTextBox(self, RegID="boxcaption", SelectOnEntry=True)
                hsz.append(lbl, halign="right")
                hsz.appendSpacer(4)
                hsz.append(txt, 1, halign="left")
                self.Sizer.append(hsz, halign="center")
                self.boxcaption.Enabled = False

            def onHit_chkBox(self, evt):
                self.boxcaption.Enabled = self.chkBox.Value
                self.layout()

        dlg = BoxSizerInfo(self.CurrentForm, BasePrefKey=self.BasePrefKey + ".BoxSizerInfo")
        dlg.show()
        ret = (None, None, None)
        if dlg.Accepted:
            ret = (dlg.slotcount.Value, dlg.chkBox.Value, dlg.boxcaption.Value)
        dlg.release()
        return ret

    def getNumRowCol(self):
        """Get the number of rows and columns for a new grid sizer"""

        class RowColDialog(dOkCancelDialog):
            _hideInTree = True

            def addControls(self):
                #                self.AutoSize = False
                sz = self.Sizer
                sz.appendSpacer(20)
                self.spnRows = dSpinner(self, Min=1, Max=99, Value=4)
                self.spnCols = dSpinner(self, Min=1, Max=99, Value=2)
                lbl = dLabel(self, Caption=_("Number of Rows?"), Alignment="center")
                plat = self.Application.Platform
                if plat == "GTK":
                    lbl.Width = 200
                sz.append(lbl, halign="center")
                sz.append(self.spnRows, halign="center")
                sz.appendSpacer(8)
                lbl = dLabel(self, Caption=_("Number of Columns?"), Alignment="center")
                if plat == "GTK":
                    lbl.Width = 200
                sz.append(lbl, halign="center")
                sz.append(self.spnCols, halign="center")
                sz.appendSpacer(25)
                self.layout()
                #                ui.callAfter(self.fitToSizer)
                ui.callAfter(self.spnRows.setFocus)

            def getRows(self):
                return self.spnRows.Value

            def getCols(self):
                return self.spnCols.Value

        dlg = RowColDialog(
            self.CurrentForm,
            Caption=_("Grid Sizer Dimensions"),
            BasePrefKey=self.BasePrefKey + ".RowColDialog",
        )
        dlg.Centered = True
        dlg.show()
        ret = (None, None)
        if dlg.Accepted:
            ret = (dlg.getRows(), dlg.getCols())
        dlg.release()
        del dlg
        return ret

    def getCodeForObject(self, obj, create=False):
        """Returns a dict of method names (keys) and the code for those methods.
        If no code exists for the given object and create=False, None is returned. If
        create=True, an empty key for that object is created and returned.
        """
        ret = self._codeDict.get(obj)
        if ret is None and create:
            ret = self._codeDict[obj] = {}
        return ret

    def getCodeDict(self):
        return self._codeDict

    def getPropDictForObject(self, obj):
        return self._classPropDict.get(obj, {})

    def onPaletteClick(self, evt):
        if self.UseSizers:
            self.onAddControl(evt)
            ui.callAfter(self.ControlPalette.clear)
        # Seems to be needed in Windows to prevent double events
        evt.stop()

    def onAddControl(self, evt):
        """Called when the user clicks on a palette button or selects
        from the Controls menu.
        """
        ctlCap = evt.EventObject.Caption
        obj = self._srcObj
        if isinstance(obj, (LayoutPanel, dPanel)):
            funcDict = {
                _("Vert. Sizer"): self.onNewVert,
                _("Horiz. Sizer"): self.onNewHoriz,
                _("Grid Sizer"): self.onNewGridSizer,
                _("Box"): self.onNewBox,
                _("Bitmap"): self.onNewBitmap,
                _("BitmapButton"): self.onNewBitmapButton,
                _("Button"): self.onNewButton,
                _("CheckBox"): self.onNewCheckBox,
                _("CodeEditor"): self.onNewEditor,
                _("ComboBox"): self.onNewComboBox,
                _("DateTextBox"): self.onNewDateTextBox,
                _("DropdownList"): self.onNewDropdownList,
                _("EditBox"): self.onNewEditBox,
                _("Gauge"): self.onNewGauge,
                _("Grid"): self.onNewGrid,
                _("Image"): self.onNewImage,
                _("Label"): self.onNewLabel,
                _("Line"): self.onNewLine,
                _("ListBox"): self.onNewListBox,
                _("ListControl"): self.onNewListControl,
                _("MaskedTextBox"): self.onNewMaskedTextBox,
                _("CheckList"): self.onNewCheckList,
                _("MediaControl"): self.onNewMediaControl,
                _("RadioList"): self.onNewRadioList,
                _("Panel"): self.onNewPanel,
                _("ScrollPanel"): self.onNewScrollPanel,
                _("PageFrame"): self.onNewPageFrame,
                _("PageList"): self.onNewPageList,
                _("PageSelect"): self.onNewPageSelect,
                _("PageStyled"): self.onNewPageStyled,
                _("PageNoTabs"): self.onNewPageNoTabs,
                _("SlidePanelControl"): self.onNewSlidePanelControl,
                _("Slider"): self.onNewSlider,
                _("Spinner"): self.onNewSpinner,
                _("Splitter"): self.onNewSplitter,
                _("TextBox"): self.onNewTextBox,
                _("ToggleButton"): self.onNewToggleButton,
                _("TreeView"): self.onNewTreeView,
            }
            func = funcDict[ctlCap]
            func(evt)

    def isUsingSizers(self):
        return self.UseSizers

    def shouldEnableAddControl(self):
        """This is the method used for the Control menu's items as their
        DynamicEnabled property.
        """
        return isinstance(self._srcObj, LayoutPanel)

    def shouldEnableSaveAsClass(self):
        """This is the method used for the SaveAsClass menu items as its
        DynamicEnabled property.
        """
        ret = len(self._selection) != 0
        if ret:
            ret = not isinstance(self._selection[0], (LayoutPanel, LayoutSpacerPanel))
        return ret

    def shouldEnableAlignControls(self):
        return (not self.UseSizers) and len(self.Selection) > 1

    def shouldEnableAlignMenu(self):
        return not self.UseSizers

    def onAlignTopEdge(self, evt):
        self.CurrentForm.alignControls(evt, "Top")

    def onAlignBottomEdge(self, evt):
        self.CurrentForm.alignControls(evt, "Bottom")

    def onAlignLeftEdge(self, evt):
        self.CurrentForm.alignControls(evt, "Left")

    def onAlignRightEdge(self, evt):
        self.CurrentForm.alignControls(evt, "Right")

    def onBringToFront(self, evt):
        for ctl in self.Selection:
            ctl.bringToFront()

    def onSendToBack(self, evt):
        for ctl in self.Selection:
            ctl.sendToBack()

    def shouldEnableZOrdering(self):
        return len(self.Selection) > 0

    def addDrawnClass(self, cls, parent, pos1, pos2):
        if not self.Selection:
            self.Selection = [self.CurrentForm]
        obj = self.addNewControl(parent, cls)
        h1, v1 = pos1
        h2, v2 = pos2
        obj.Left = min(h1, h2)
        obj.Width = abs(h2 - h1)
        obj.Top = min(v1, v2)
        obj.Height = abs(v2 - v1)
        self.ControlPalette.clear()
        self.select(obj)

    def addQuickLayout(self, layoutInfo):
        pnl = self.getActivePanel()
        if pnl is None:
            # We need to provide a way for them to select the
            # panel they want it added to. Perhaps storing the
            # info temporarily, and then adding the controls
            # after they've made their selection.
            return

        typ = layoutInfo["layoutType"].lower()
        flds = layoutInfo["fields"]
        table = layoutInfo["table"]
        spacing = layoutInfo["spacing"]
        colSpacing = layoutInfo["colspacing"]
        outBorder = layoutInfo["border"]
        lblAlign = layoutInfo["labelAlignment"]
        useColons = layoutInfo["useColons"]
        # Update the outBorder value before adding the controls.
        pnl.Sizer_Border = outBorder

        if typ == "grid":
            colInfo = {}
            order = 0
            for fld in flds:
                inf = layoutInfo["fldInfo"][fld]
                coldata = {}
                coldata["Width"] = inf["width"]
                coldata["Caption"] = inf["caption"]
                coldata["DataField"] = fld
                coldata["Order"] = order
                order += 10
                colInfo[fld] = coldata

            grd = self.addNewControl(pnl, dGrid, props={"ColumnCount": 0}, skipUpdate=True)

            grd.ColumnCount = len(flds)
            grd.DataSource = table
            for pos, fld in enumerate(flds):
                col = grd.Columns[pos]
                coldata = colInfo[fld]
                col.Width = coldata["Width"]
                col.Caption = coldata["Caption"]
                col.DataField = coldata["DataField"]
                col.Order = coldata["Order"]
            grd.DataSource = layoutInfo["table"]
            grd.emptyRowsToAdd = 5
            grd.fillGrid()

        elif typ.startswith("column;"):
            useGrid = typ.endswith("labels on left")
            colonSep = ""
            if useColons:
                colonSep = ":"
            # Collections of the added labels/controls. Used
            # for final alignment in non-sizer cases.
            lbls = []
            ctls = []
            if self.UseSizers:
                if useGrid:
                    sz, pnl = self.addSizer("grid", pnl=pnl, rows=0, cols=2)
                else:
                    sz, pnl = self.addSizer("box", orient="v", pnl=pnl, slots=0)
                if useGrid:
                    sz.VGap = spacing
                    sz.HGap = colSpacing
            else:
                # No sizers. Lay them out from the context menu position.
                (xpos, ypos) = (xorig, yorig) = self._srcPos
                if outBorder:
                    xpos += outBorder
                    ypos += outBorder
                    xorig += outBorder
                    yorig += outBorder

            lblClass = self.getControlClass(dLabel)
            for fld in flds:
                fldData = layoutInfo["fldInfo"][fld]
                lbl = lblClass(pnl)
                lbls.append(lbl)
                # Need to add this after the fact, so that when the form is saved,
                # the caption is different than the original value.
                lbl.Caption = "%s%s" % (fldData["caption"].rstrip(":"), colonSep)
                ctlClass = self.getControlClass(fldData["class"])
                ctl = ctlClass(pnl, DataSource=table, DataField=fld)
                if isinstance(ctl, dTextBox):
                    ctl.Value = ""
                ctls.append(ctl)
                if self.UseSizers:
                    sz.append(lbl, halign=lblAlign)
                    if useGrid:
                        sz.append(ctl, "x", halign="left")
                    else:
                        # Add a border to the bottom of the control
                        sz.append(
                            ctl,
                            "x",
                            halign="left",
                            border=spacing,
                            borderSides="Bottom",
                        )
                else:
                    lbl.Position = (xpos, ypos)
                    if useGrid:
                        xpos += lbl.Width + colSpacing
                    else:
                        ypos += lbl.Height
                    ctl.Position = (xpos, ypos)
                    if useGrid:
                        xpos = xorig
                    ypos += ctl.Height + spacing

            if self.UseSizers:
                if useGrid:
                    sz.Rows = len(flds)
                    sz.Columns = 2
                    sz.setColExpand(True, 1)
                pnl.layout()
            else:
                # Right-align all the controls to the rightmost position
                rpos = max([ctl.Right for ctl in ctls])
                for ctl in ctls:
                    ctl.Right = rpos
                lblAlign = layoutInfo["labelAlignment"]
                if lblAlign == "Center":
                    wd = max([lbl.Width for lbl in lbls])
                    for lbl in lbls:
                        lbl.Left += 0.5 * (wd - lbl.Width)
                elif lblAlign == "Right":
                    rpos = max([lbl.Right for lbl in lbls])
                    for lbl in lbls:
                        lbl.Right = rpos
                else:
                    lpos = max([lbl.Left for lbl in lbls])
                    for lbl in lbls:
                        lbl.Left = lpos
        self._selection = [self.CurrentForm]
        ui.callAfterInterval(100, self.updateLayout)
        ui.callAfterInterval(100, self.EditorForm.refreshStatus)

    # TODO!!!!!!
    def miniAppTemplate(self):
        return """import os
import inspect

from .application import dApp

def main():
    app = dApp()
    curdir = os.getcwd()
    # Get the current location's path
    fname = inspect.getfile(main)
    pth = os.path.split(fname)[0]
    if pth:
        # Switch to that path
        os.chdir(pth)
    app.MainFormClass = "%s"
    app.start()

    # Return to the original location
    os.chdir(curdir)


if __name__ == '__main__':
    main()
"""

    def miniDialogAppTemplate(self):
        return """import os
import inspect

from .applicationp import dApp

def main():
    app = dApp()
    curdir = os.getcwd()
    # Get the current location's path
    fname = inspect.getfile(main)
    pth = os.path.split(fname)[0]
    if pth:
        # Switch to that path
        os.chdir(pth)

    dlg = ui.createForm("%s")
    dlg.show()
    dlg.release()
    app.start()

    # Return to the original location
    os.chdir(curdir)


if __name__ == '__main__':
    main()
"""

    def _getClipboard(self):
        return self._clipboard

    def _getPalette(self):
        noPalette = self._palette is None
        if not noPalette:
            # Make sure it's still a live object
            if not self._palette:
                noPalette = True
        if noPalette:

            class PaletteForm(dToolForm):
                def afterSetMenuBar(self):
                    class_designer_menu.mkDesignerMenu(self)

                def onMenuOpen(self, evt):
                    self.Controller.menuUpdate(evt, self.MenuBar)

                def onButtonToggle(self, evt):
                    obj = evt.EventObject
                    if obj.Value:
                        # Toggle the others off
                        for btn in [bb for bb in self.mainPanel.Children if not bb is obj]:
                            btn.Value = False

                def clear(self):
                    """Set all buttons to False."""
                    for btn in self.mainPanel.Children:
                        if btn.Value:
                            btn.Value = False

                def _getController(self):
                    try:
                        return self._controller
                    except AttributeError:
                        self._controller = self.Application
                        return self._controller

                def _setController(self, val):
                    if self._constructed():
                        self._controller = val
                    else:
                        self._properties["Controller"] = val

                def _getSelectedClass(self):
                    try:
                        ret = [btn.ControlClass for btn in self.mainPanel.Children if btn.Value][0]
                    except:
                        ret = None
                    return ret

                Controller = property(
                    _getController,
                    _setController,
                    None,
                    _("Object to which this one reports events  (object (varies))"),
                )

                SelectedClass = property(
                    _getSelectedClass,
                    None,
                    None,
                    _("Class that is currently selected, or None  (class)"),
                )

            cp = self._palette = PaletteForm(
                None,
                Caption=_("Control Palette"),
                BasePrefKey=self.BasePrefKey + ".PaletteForm",
            )
            self._palette.Controller = self
            cp.Sizer = dSizer()
            mp = cp.mainPanel = dPanel(cp)
            cp.Sizer.append1x(mp)

            # Until we get good graphics, just use regular buttons with
            # captions instead of icons.
            class PaletteButton(dToggleButton):
                def beforeInit(self):
                    self._controlClass = None

                def afterInit(self):
                    self.BasePrefKey = self.Parent.BasePrefKey + ".PaletteButton"
                    if self.Application.Platform == "Win":
                        self.FontSize = 8
                    else:
                        self.FontSize = 9
                    self.Height = 24
                    self.BezelWidth = 2
                    self.bindEvent(events.Hit, self.Form.onButtonToggle)

                def _getControlClass(self):
                    return self._controlClass

                def _setControlClass(self, val):
                    if self._constructed():
                        self._controlClass = val
                    else:
                        self._properties["ControlClass"] = val

                ControlClass = property(
                    _getControlClass,
                    _setControlClass,
                    None,
                    _("Class that this button represents  (class)"),
                )

            spacing = 3
            sz = mp.Sizer = dGridSizer(MaxCols=5, HGap=spacing, VGap=spacing)

            # Add the sizer buttons
            sz.append(10)
            btn = PaletteButton(mp, Caption=_("Vert. Sizer"), ControlClass=dSizer)
            btn.DynamicEnabled = self.isUsingSizers
            btn.bindEvent(events.Hit, self.onPaletteClick)
            sz.append(btn)
            btn = PaletteButton(mp, Caption=_("Horiz. Sizer"), ControlClass=dSizer)
            btn.DynamicEnabled = self.isUsingSizers
            btn.bindEvent(events.Hit, self.onPaletteClick)
            sz.append(btn)
            btn = PaletteButton(mp, Caption=_("Grid Sizer"), ControlClass=dGridSizer)
            btn.DynamicEnabled = self.isUsingSizers
            btn.bindEvent(events.Hit, self.onPaletteClick)
            sz.append(btn)
            sz.append(10)

            # Now add the control buttons
            ctls = (
                (_("Box"), dBox),
                (_("Bitmap"), dBitmap),
                (_("BitmapButton"), dBitmapButton),
                (_("Button"), dButton),
                (_("CheckBox"), dCheckBox),
                (_("CodeEditor"), dEditor),
                (_("ComboBox"), dComboBox),
                (_("DateTextBox"), dDateTextBox),
                (_("DropdownList"), dDropdownList),
                (_("EditBox"), dEditBox),
                (_("SlidePanelControl"), dSlidePanelControl),
                (_("Gauge"), dGauge),
                (_("Grid"), dGrid),
                (_("HtmlBox"), dHtmlBox),
                (_("Image"), dImage),
                (_("Label"), dLabel),
                (_("Line"), dLine),
                (_("LED"), dLed),
                (_("ListBox"), dListBox),
                (_("ListControl"), dListControl),
                (_("MaskedTextBox"), dMaskedTextBox),
                (_("CheckList"), dCheckList),
                (_("Panel"), dPanel),
                (_("ScrollPanel"), dScrollPanel),
                (_("PageFrame"), dPageFrame),
                (_("PageList"), dPageList),
                (_("PageSelect"), dPageSelect),
                (_("PageStyled"), dPageStyled),
                (_("PageNoTabs"), dPageFrameNoTabs),
                (_("RadioList"), dRadioList),
                (_("Shell"), dShell),
                (_("Slider"), dSlider),
                (_("Spinner"), dSpinner),
                (_("Splitter"), dSplitter),
                (_("TextBox"), dTextBox),
                (_("ToggleButton"), dToggleButton),
                (_("TreeView"), dTreeView),
            )
            try:
                ctls += ((_("MediaControl"), dMediaControl),)
            except AttributeError:
                # dMediaControl was not imported; some earlier wx versions don't include this
                pass
            for cap, cls in ctls:
                btn = PaletteButton(mp, Caption=cap, ControlClass=cls)
                btn.bindEvent(events.Hit, self.onPaletteClick)
                sz.append(btn)
            cp.layout()
            cp.Fit()
        return self._palette

    def _getCurrentForm(self):
        return self._currentForm

    def _setCurrentForm(self, val):
        self._currentForm = val

    def _getEditorForm(self):
        noEdt = self._editorForm is None
        if not noEdt:
            # Make sure it's still a live object
            try:
                junk = self._editorForm.Visible
            except Exception:
                noEdt = True
        if noEdt:
            self._editorForm = EditorForm(None, MenuBarClass=dBaseMenuBar)
            self._editorForm.Controller = self
        return self._editorForm

    def _getPemForm(self):
        noPem = self._pemForm is None
        if not noPem:
            # Make sure it's still a live object
            try:
                junk = self._pemForm.Visible
            except Exception:
                noPem = True
        if noPem:
            pf = self._pemForm = PemForm(None)
            pf.restoreSizeAndPosition()
            pf.Controller = self
            ui.callAfterInterval(100, self.updateLayout)
        return self._pemForm

    def _getPropSht(self):
        self._propSheet = self.PemForm.PropSheet
        return self._propSheet

    def _getSelectedClass(self):
        return self.ControlPalette.SelectedClass

    def _getSelection(self):
        return self._selection

    def _setSelection(self, val):
        # use the code in the select() method
        self.select(val)

    def _getSizerPalette(self):
        noPalette = self._sizerPalette is None
        if not noPalette:
            # Make sure it's still a live object
            if not self._sizerPalette:
                noPalette = True
        if noPalette:
            defSz = (300, 800)
            sp = self._sizerPalette = SizerPaletteForm(
                None,
                Caption=_("Sizer Settings"),
                BasePrefKey=self.BasePrefKey + ".SizerPaletteForm",
                Controller=self,
                Size=defSz,
            )
        ui.callAfter(self._sizerPalette.select, self.Selection)
        return self._sizerPalette

    def _getTextEditorForm(self):
        noEdt = self._textEditorForm is None
        if not noEdt:
            # Make sure it's still a live object
            try:
                junk = self._textEditorForm.Visible
            except Exception:
                noEdt = True
        if noEdt:
            self._textEditorForm = TextEditorForm(None)
            self._textEditorForm.Controller = self
        return self._textEditorForm

    def _getTree(self):
        return self.PemForm.Tree

    def _getUseSizers(self):
        if self.CurrentForm:
            return self.CurrentForm.UseSizers
        else:
            return True

    Clipboard = property(
        _getClipboard,
        None,
        None,
        _("Holds dict of controls that have been copied.  (dict)"),
    )

    ControlPalette = property(
        _getPalette, None, None, _("Reference to the Control Palette  (dToolForm)")
    )

    CurrentForm = property(
        _getCurrentForm,
        _setCurrentForm,
        None,
        _("Currently active designer surface  (DesForm)"),
    )

    EditorForm = property(
        _getEditorForm,
        None,
        None,
        _("Reference to the code editing form  (EditorForm)"),
    )

    PemForm = property(
        _getPemForm,
        None,
        None,
        _(
            """Reference to the form that contains the PropSheet,
            TreeSheet and Method list (PemForm)"""
        ),
    )

    PropSheet = property(_getPropSht, None, None, _("Reference to the Property Sheet (PropSheet)"))

    SelectedClass = property(
        _getSelectedClass,
        None,
        None,
        _("Class that is currently selected, or None  (class)"),
    )

    Selection = property(
        _getSelection,
        _setSelection,
        None,
        _("List of currently-selected objects  (list)"),
    )

    SizerPalette = property(
        _getSizerPalette,
        None,
        None,
        _("Reference to the sizer setting palette (read-only) (dToolForm)"),
    )

    TextEditorForm = property(
        _getTextEditorForm,
        None,
        None,
        _("Reference to the text file editing form  (TextEditorForm)"),
    )

    Tree = property(_getTree, None, None, _("Reference to the Layout Tree form (TreeSheet)"))

    UseSizers = property(
        _getUseSizers,
        None,
        None,
        _("Does the MainForm use sizers for its layout?  (bool)"),
    )


if __name__ == "__main__":
    clsDes = ClassDesigner(sys.argv[1:])
