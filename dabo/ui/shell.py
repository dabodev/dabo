# -*- coding: utf-8 -*-
import builtins
import time

import wx
import wx.py
import wx.stc as stc
from wx.py import pseudo

from .. import db, events, ui
from ..dLocalize import _
from . import (
    dBaseMenuBar,
    dButton,
    dControlMixin,
    dEditBox,
    dEditor,
    dKeys,
    dLabel,
    dListBox,
    dMenu,
    dPageFrame,
    dPanel,
    dSizer,
    dSplitForm,
    makeDynamicProperty,
)


class _LookupPanel(dPanel):
    """Used for the command history search"""

    def afterInit(self):
        self._history = None
        self._displayedHistory = None
        self.currentSearch = ""
        self.needRefilter = False
        self.lblSearch = dLabel(self)
        self.lstMatch = dListBox(
            self,
            ValueMode="string",
            Choices=[],
            MultipleSelect=True,
            OnMouseLeftDoubleClick=self.selectCmd,
            OnKeyChar=self.onListKey,
        )
        self.Sizer = dSizer("v", DefaultBorder=4)
        self.Sizer.append(self.lblSearch, halign="center")
        self.Sizer.append(self.lstMatch, "x", 1)
        self.Width = 400
        self.layout()

    def clear(self):
        """Reset to original state."""
        self.ok = False
        self.currentSearch = self.lblSearch.Caption = ""
        self.refilter()

    def onListKey(self, evt):
        """Process keypresses in the command list control"""
        kc = evt.keyCode
        char = evt.keyChar
        if kc in (dKeys.key_Return, dKeys.key_Numpad_enter):
            self.closeDialog(True)
            return
        elif kc == dKeys.key_Escape:
            self.closeDialog(False)
        if kc in list(dKeys.arrowKeys.values()) or char is None:
            # ignore
            return
        if kc == dKeys.key_Back:
            self.currentSearch = self.currentSearch[:-1]
        else:
            self.currentSearch += char
        self.lblSearch.Caption = self.currentSearch
        self.layout()
        self.needRefilter = True
        evt.stop()

    def closeDialog(self, ok):
        """Hide the dialog, and set the ok/cancel flag"""
        self.ok = ok
        self.Form.hide()

    def getCmd(self):
        return self.lstMatch.Value

    def selectCmd(self, evt):
        self.closeDialog(True)

    def onIdle(self, evt):
        """For performance, don't filter on every keypress. Wait until idle."""
        if self.needRefilter:
            self.needRefilter = False
            self.refilter()

    def refilter(self):
        """Display only those commands that contain the search string"""
        self.DisplayedHistory = self.History.filterByExpression(
            " '%s' in cmd.lower() " % self.currentSearch.lower()
        )
        lst = self.lstMatch
        sel = lst.Value
        lst.Choices = [rec["cmd"] for rec in self.DisplayedHistory]
        if sel:
            try:
                lst.Value = sel
            except ValueError:
                self._selectLast()
        else:
            self._selectLast()
        self._selectLast()

    def _selectFirst(self):
        """Select the first item in the list, if available."""
        if len(self.lstMatch.Choices):
            self.lstMatch.PositionValue = 0

    def _selectLast(self):
        """Select the first item in the list, if available."""
        num = len(self.lstMatch.Choices)
        if num:
            self.lstMatch.PositionValue = num - 1

    # Property definitions
    @property
    def DisplayedHistory(self):
        """Filtered copy of the History  (dDataSet)"""
        if self._displayedHistory is None:
            self._displayedHistory = self.History
        return self._displayedHistory

    @DisplayedHistory.setter
    def DisplayedHistory(self, val):
        if self._constructed():
            self._displayedHistory = val
        else:
            self._properties["DisplayedHistory"] = val

    @property
    def History(self):
        """Dataset containing the command history  (dDataSet)"""
        if self._history is None:
            self._history = db.dDataSet()
        return self._history

    @History.setter
    def History(self, val):
        if self._constructed():
            self._history = self._displayedHistory = val
            try:
                self.lstMatch.Choices = [rec["cmd"] for rec in self.DisplayedHistory]
                self._selectLast()
            except AttributeError:
                pass
        else:
            self._properties["History"] = val


class dShell(dControlMixin, wx.py.shell.Shell):
    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._isConstructed = False
        # Set some reasonable font defaults.
        self.plat = self.Application.Platform
        if self.plat == "GTK":
            self._fontFace = "Monospace"
            self._fontSize = 10
        elif self.plat == "Mac":
            self._fontFace = "Monaco"
            self._fontSize = 12
        elif self.plat == "Win":
            self._fontFace = "Courier New"
            self._fontSize = 10
        self._baseClass = dShell
        preClass = wx.py.shell.Shell
        dControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

    @ui.deadCheck
    def ScrollToLine(self, lnum):
        """Need to check for the case where the control is released, as the wx-level
        shell makes a CallAfter for ScrollToLine().
        """
        super().ScrollToLine(lnum)

    def processLine(self):
        """
        This is part of the underlying class. We need to add the command that
        gets processed into our internal stack.
        """
        edt = self.CanEdit()
        super().processLine()
        if edt:
            # push the latest command into the stack
            try:
                self.Form.addToHistory()
            except AttributeError:
                # Not running in dShellForm
                pass

    def push(self, command, silent=False):
        """Need to raise an event when the interpreter executes a command."""
        super().push(command, silent=silent)
        if not self.more:
            self.raiseEvent(events.ShellCommandRun)

    def getAutoCompleteList(self, cmd):
        return self.interp.getAutoCompleteList(
            cmd,
            includeMagic=self.autoCompleteIncludeMagic,
            includeSingle=self.autoCompleteIncludeSingle,
            includeDouble=self.autoCompleteIncludeDouble,
        )

    def setDefaultFont(self, fontFace, fontSize):
        # Global default styles for all languages
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, "face:%s,size:%d" % (fontFace, fontSize))
        self.StyleClearAll()  # Reset all to be like the default

        # Global default styles for all languages
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, "face:%s,size:%d" % (self._fontFace, fontSize))
        self.StyleSetSpec(
            stc.STC_STYLE_LINENUMBER,
            "back:#C0C0C0,face:%s,size:%d" % (self._fontFace, 8),
        )
        self.StyleSetSpec(stc.STC_STYLE_CONTROLCHAR, "face:%s" % fontFace)
        self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT, "fore:#000000,back:#00FF00,bold")
        self.StyleSetSpec(stc.STC_STYLE_BRACEBAD, "fore:#000000,back:#FF0000,bold")

    def setPyFont(self, fontFace, fontSize):
        # Python-specific styles
        self.StyleSetSpec(stc.STC_P_DEFAULT, "fore:#000000,face:%s,size:%d" % (fontFace, fontSize))
        # Comments
        self.StyleSetSpec(
            stc.STC_P_COMMENTLINE,
            "fore:#007F00,face:%s,size:%d,italic" % (fontFace, fontSize),
        )
        # Number
        self.StyleSetSpec(stc.STC_P_NUMBER, "fore:#007F7F,size:%d" % fontSize)
        # String
        self.StyleSetSpec(stc.STC_P_STRING, "fore:#7F007F,face:%s,size:%d" % (fontFace, fontSize))
        # Single quoted string
        self.StyleSetSpec(
            stc.STC_P_CHARACTER, "fore:#7F007F,face:%s,size:%d" % (fontFace, fontSize)
        )
        # Keyword
        self.StyleSetSpec(stc.STC_P_WORD, "fore:#00007F,bold,size:%d" % fontSize)
        # Triple quotes
        self.StyleSetSpec(stc.STC_P_TRIPLE, "fore:#7F0000,size:%d,italic" % fontSize)
        # Triple double quotes
        self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:#7F0000,size:%d,italic" % fontSize)
        # Class name definition
        self.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:#0000FF,bold,underline,size:%d" % fontSize)
        # Function or method name definition
        self.StyleSetSpec(stc.STC_P_DEFNAME, "fore:#007F7F,bold,size:%d" % fontSize)
        # Operators
        self.StyleSetSpec(stc.STC_P_OPERATOR, "bold,size:%d" % fontSize)
        # Identifiers
        self.StyleSetSpec(
            stc.STC_P_IDENTIFIER, "fore:#000000,face:%s,size:%d" % (fontFace, fontSize)
        )
        # Comment-blocks
        self.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "fore:#7F7F7F,size:%d,italic" % fontSize)
        # End of line where string is not closed
        self.StyleSetSpec(
            stc.STC_P_STRINGEOL,
            "fore:#000000,face:%s,back:#E0C0E0,eol,size:%d" % (fontFace, fontSize),
        )

    def OnKeyDown(self, evt):
        """Override on the Mac, as the navigation defaults are different than on Win/Lin"""
        if self.plat != "Mac":
            return super().OnKeyDown(evt)
        key = evt.GetKeyCode()
        # If the auto-complete window is up let it do its thing.
        if self.AutoCompActive():
            evt.Skip()
            return

        # Prevent modification of previously submitted
        # commands/responses.
        controlDown = evt.ControlDown()
        altDown = evt.AltDown()
        shiftDown = evt.ShiftDown()
        cmdDown = evt.CmdDown()
        currpos = self.GetCurrentPos()
        endpos = self.GetTextLength()
        selecting = self.GetSelectionStart() != self.GetSelectionEnd()
        if cmdDown and (key == wx.WXK_LEFT):
            # Equivalent to Home
            home = self.promptPosEnd
            if currpos > home:
                self.SetCurrentPos(home)
                if not selecting and not shiftDown:
                    self.SetAnchor(home)
                    self.EnsureCaretVisible()
            return
        if cmdDown and (key == wx.WXK_RIGHT):
            # Equivalent to End
            linepos = self.GetLineEndPosition(self.GetCurrentLine())
            if shiftDown:
                start = currpos
            else:
                start = linepos
            self.SetSelection(start, linepos)
            return
        elif cmdDown and (key == wx.WXK_UP):
            # Equivalent to Ctrl-Home
            if shiftDown:
                end = currpos
            else:
                end = 0
            self.SetSelection(0, end)
            return
        elif cmdDown and (key == wx.WXK_DOWN):
            # Equivalent to Ctrl-End
            if shiftDown:
                start = currpos
            else:
                start = endpos
            self.SetSelection(start, endpos)
            return
        return super().OnKeyDown(evt)

    # Property definitions
    @property
    def FontFace(self):
        """Name of the font face used in the shell  (str)"""
        return self._fontFace

    @FontFace.setter
    def FontFace(self, val):
        if self._constructed():
            self._fontFace = val
            self.setDefaultFont(self._fontFace, self._fontSize)
            self.setPyFont(self._fontFace, self._fontSize)
            self.Application.setUserSetting("shell.fontface", self._fontFace)
        else:
            self._properties["FontFace"] = val

    @property
    def FontSize(self):
        """Size of the font used in the shell  (int)"""
        return self._fontSize

    @FontSize.setter
    def FontSize(self, val):
        if self._constructed():
            self._fontSize = val
            self.setDefaultFont(self._fontFace, self._fontSize)
            self.setPyFont(self._fontFace, self._fontSize)
            self.Application.setUserSetting("shell.fontsize", self._fontSize)
        else:
            self._properties["FontSize"] = val


ui.dShell = dShell


class dShellForm(dSplitForm):
    def _onDestroy(self, evt):
        self._clearOldHistory()
        builtins.input = self._oldInput

    def _beforeInit(self, pre):
        # Class to use for creating the interactive shell
        self._shellClass = dShell
        self._sashPct = 80
        super()._beforeInit(pre)

    def _afterInit(self):
        super()._afterInit()
        self.cmdHistKey = self.PreferenceManager.command_history
        self._historyPanel = None
        self._lastCmd = None

        # PyShell sets the input function to a function of PyShell,
        # but doesn't set it back on destroy, resulting in errors later
        # on if something other than PyShell asks for input (pdb, for
        # example).
        self._oldInput = builtins.input
        self.bindEvent(events.Destroy, self._onDestroy)

        splt = self.Splitter
        splt.MinimumPanelSize = 80
        splt.unbindEvent()
        self.Orientation = "H"
        self.unsplit()
        self._splitState = False
        self.MainSplitter.bindEvent(events.SashDoubleClick, self.sashDoubleClick)
        self.MainSplitter.bindEvent(events.SashPositionChanged, self.sashPosChanged)

        cp = self.CmdPanel = self.Panel1
        op = self.OutPanel = self.Panel2
        cp.unbindEvent(events.ContextMenu)
        op.unbindEvent(events.ContextMenu)

        cp.Sizer = dSizer()
        op.Sizer = dSizer()
        pgf = self.pgfCodeShell = dPageFrame(cp, PageCount=2)
        self.pgShell = pgf.Pages[0]
        self.pgCode = pgf.Pages[1]
        self.pgShell.Caption = _("Shell")
        self.pgCode.Caption = _("Code")
        cp.Sizer.append1x(pgf)

        self.shell = self.ShellClass(self.pgShell, DroppedTextHandler=self, DroppedFileHandler=self)
        self.pgShell.Sizer.append1x(self.shell, border=4)
        # Configure the shell's behavior
        self.shell.AutoCompSetIgnoreCase(True)
        self.shell.AutoCompSetAutoHide(False)  ## don't hide when the typed string no longer matches
        self.shell.AutoCompStops(" ")  ## characters that will stop the autocomplete
        self.shell.AutoCompSetFillUps(".(")
        # This lets you go all the way back to the '.' without losing the AutoComplete
        self.shell.AutoCompSetCancelAtStart(False)
        self.shell.Bind(wx.EVT_RIGHT_UP, self.onShellRight)
        self.shell.Bind(wx.EVT_CONTEXT_MENU, self.onShellContext)

        # Create the Code control
        codeControl = dEditor(
            self.pgCode,
            RegID="edtCode",
            Language="python",
            OnKeyDown=self.onCodeKeyDown,
            DroppedTextHandler=self,
            DroppedFileHandler=self,
        )
        self.pgCode.Sizer.append1x(codeControl, border=4)
        # This adds the interpreter's local namespace to the editor for code completion, etc.
        codeControl.locals = self.shell.interp.locals
        lbl = dLabel(
            self.pgCode,
            ForeColor="blue",
            WordWrap=True,
            Caption=_(
                """Ctrl-Enter to run the code (or click the button to the right).
Ctrl-Up/Down to scroll through history."""
            ),
        )
        lbl.FontSize -= 3
        runButton = dButton(self.pgCode, Caption=_("Run"), OnHit=self.onRunCode)
        hsz = dSizer("h")
        hsz.appendSpacer(20)
        hsz.append(lbl)
        hsz.append1x(dPanel(self.pgCode))
        hsz.append(runButton, valign="middle")
        hsz.appendSpacer(20)
        self.pgCode.Sizer.append(hsz, "x")
        # Stack to hold code history
        self._codeStack = []
        self._codeStackPos = 0

        # Restore the history
        self.restoreHistory()
        # Bring up history search
        self.bindKey("Ctrl+R", self.onHistoryPop)
        # Show/hide the code editing pane
        self.bindKey("Ctrl+E", self.onToggleCodePane)

        # Force the focus to the editor when the code page is activated.
        def _delayedSetFocus(evt):
            ui.callAfter(self.edtCode.setFocus)

        self.pgCode.bindEvent(events.PageEnter, _delayedSetFocus)

        # create the output control
        outControl = dEditBox(op, RegID="edtOut", ReadOnly=True)
        op.Sizer.append1x(outControl)
        outControl.bindEvent(events.MouseRightDown, self.onOutputRightDown)

        self._stdOut = self.shell.interp.stdout
        self._stdErr = self.shell.interp.stderr
        self._pseudoOut = pseudo.PseudoFileOut(write=self.appendOut)
        self._pseudoErr = pseudo.PseudoFileOut(write=self.appendOut)
        self.SplitState = True

        # Make 'self' refer to the calling form, or this form if no calling form.
        # Make 'bo' refer to the primary bizobj of the calling form, if any.
        if self.Parent is None:
            ns = self
        else:
            ns = self.Parent
            bo = getattr(ns, "PrimaryBizobj", None)
            if bo:
                self.shell.interp.locals["bo"] = bo
        self.shell.interp.locals["self"] = ns

        self.Caption = _("dShellForm: self is %s") % ns.Name
        self.updateStatusText(_("Use this shell to interact with the runtime environment"))
        self.MenuBar = dBaseMenuBar()
        self.fillMenu()
        self.shell.SetFocus()

    def appendOut(self, tx):
        ed = self.edtOut
        ed.Value += tx
        endpos = ed.GetLastPosition()
        # Either of these commands should scroll the edit box
        # to the bottom, but neither do (at least on OS X) when
        # called directly or via callAfter().
        ui.callAfter(ed.ShowPosition, endpos)
        ui.callAfter(ed.SetSelection, endpos, endpos)

    def addToHistory(self, cmd=None):
        if cmd is None:
            cmd = self.shell.history[0]
        chk = self.cmdHistKey
        if cmd == self._lastCmd:
            # Don't add again
            return
        # Delete any old instances of this command
        chk.deleteByValue(cmd)
        self._lastCmd = cmd
        stamp = "%s" % int(round(time.time() * 100, 0))
        self.cmdHistKey.setValue(stamp, cmd)

    def _loadHistory(self):
        ck = self.cmdHistKey
        cmds = []
        for k in ck.getPrefKeys():
            cmds.append({"stamp": k, "cmd": ck.get(k)})
        dsu = db.dDataSet(cmds)
        if dsu:
            ds = dsu.sort("stamp", "asc")
            return ds
        else:
            return dsu

    def onToggleCodePane(self, evt):
        """Toggle between the Code Pane and the Output Pane"""
        self.pgfCodeShell.cyclePages(1)

    def processDroppedFiles(self, filelist):
        """
        This will fire if files are dropped on the code editor. If more than one
        file is dropped, only open the first, and warn the user.
        """
        if len(filelist) > 1:
            ui.exclaim(_("Only one file can be dropped at a time"))
        if self.pgfCodeShell.SelectedPage == self.pgShell:
            self.shell.AddText(filelist[0])
        else:
            with open(filelist[0]) as ff:
                self.edtCode.Value = ff.read()

    def processDroppedText(self, txt):
        """Add the text to the code editor."""
        cc = self.edtCode
        currText = cc.Value
        selStart, selEnd = cc.SelectionPosition
        cc.Value = "%s%s%s" % (currText[:selStart], txt, currText[selEnd:])

    def onHistoryPop(self, evt):
        """
        Let the user type in part of a command, and retrieve the matching commands
        from their history.
        """
        ds = self._loadHistory()
        hp = self._HistoryPanel
        hp.History = ds
        fp = self.FloatingPanel
        # We want it centered, so set Owner to None
        fp.Owner = None
        hp.clear()
        fp.show()
        if hp.ok:
            cmds = hp.getCmd()
            for num, cmd in enumerate(cmds):
                # For all but the first, we need to process the previous command.
                if num:
                    self.shell.processLine()
                try:
                    pos = self.shell.history.index(cmd)
                except ValueError:
                    # Not in the list
                    return
                self.shell.replaceFromHistory(pos - self.shell.historyIndex)

    def restoreHistory(self):
        """
        Get the stored history from previous sessions, and set the shell's
        internal command history list to it.
        """
        ds = self._loadHistory()
        self.shell.history = [rec["cmd"] for rec in ds]

    def _clearOldHistory(self):
        """For performance reasons, only save up to 500 commands."""
        numToSave = 500
        ck = self.cmdHistKey
        ds = self._loadHistory()
        if len(ds) <= numToSave:
            return
        cutoff = ds[numToSave]["stamp"]
        bad = []
        for rec in ds:
            if rec["stamp"] <= cutoff:
                bad.append(rec["stamp"])
        for bs in bad:
            ck.deletePref(bs)

    def onRunCode(self, evt, addReturn=True):
        code = self.edtCode.Value.rstrip()
        if not code:
            return
        # See if this is already in the stack
        try:
            self._codeStackPos = self._codeStack.index(code)
        except ValueError:
            self._codeStack.append(code)
            self._codeStackPos = len(self._codeStack)
        self.edtCode.Value = ""
        self.shell.Execute(code)
        # If the last line is indented, run a blank line to complete the block
        if code.splitlines()[-1][0] in " \t":
            self.shell.run("", prompt=False)
        self.addToHistory()
        self.pgfCodeShell.SelectedPage = self.pgShell

    def onCodeKeyDown(self, evt):
        if not evt.controlDown:
            return
        keyCode = evt.keyCode
        if keyCode == 13:
            evt.stop()
            self.onRunCode(None, addReturn=True)
        elif keyCode in (dKeys.key_Up, dKeys.key_Down):
            direction = {dKeys.key_Up: -1, dKeys.key_Down: 1}[keyCode]
            self.moveCodeStack(direction)

    def moveCodeStack(self, direction):
        size = len(self._codeStack)
        pos = self._codeStackPos
        newpos = max(0, pos + direction)
        if newpos == size:
            # at the end; clear the code
            self._codeStackPos = size - 1
            self.edtCode.Value = ""
        else:
            code = self._codeStack[newpos]
            self._codeStackPos = newpos
            self.edtCode.Value = code

    def onOutputRightDown(self, evt):
        pop = dMenu()
        itm = pop.append(_("Clear Output"), OnHit=self.onClearOutput)
        if self.edtOut.SelectionLength:
            pop.append(_("Copy"), OnHit=self.Application.onEditCopy)
        self.showContextMenu(pop)
        evt.stop()

    def onClearOutput(self, evt):
        print("ON CLEAR CALLED! " * 22)
        ed = self.edtOut
        ed.Value = ""

    def onShellContext(self, evt):
        pop = dMenu()
        if self.SplitState:
            pmpt = _("Unsplit")
        else:
            pmpt = _("Split")
        pop.append(pmpt, OnHit=self.onSplitContext)
        self.showContextMenu(pop)
        evt.StopPropagation()

    def onShellRight(self, evt):
        pop = dMenu()
        if self.SplitState:
            pmpt = _("Unsplit")
        else:
            pmpt = _("Split")
        pop.append(pmpt, OnHit=self.onSplitContext)
        self.showContextMenu(pop)
        evt.StopPropagation()

    def onSplitContext(self, evt):
        self.SplitState = not self.SplitState
        evt.stop()

    def onResize(self, evt):
        self.SashPosition = self._sashPct * self.Height

    def sashDoubleClick(self, evt):
        # We don't want the window to unsplit
        evt.stop()

    def sashPosChanged(self, evt):
        self._sashPct = float(self.SashPosition) / self.Height

    def fillMenu(self):
        viewMenu = self.MenuBar.getMenu("base_view")
        if viewMenu.Children:
            viewMenu.appendSeparator()
        viewMenu.append(
            _("Zoom &In"),
            HotKey="Ctrl+=",
            OnHit=self.onViewZoomIn,
            ItemID="view_zoomin",
            bmp="zoomIn",
            help=_("Zoom In"),
        )
        viewMenu.append(
            _("&Normal Zoom"),
            HotKey="Ctrl+/",
            OnHit=self.onViewZoomNormal,
            ItemID="view_zoomnormal",
            bmp="zoomNormal",
            help=_("Normal Zoom"),
        )
        viewMenu.append(
            _("Zoom &Out"),
            HotKey="Ctrl+-",
            OnHit=self.onViewZoomOut,
            ItemID="view_zoomout",
            bmp="zoomOut",
            help=_("Zoom Out"),
        )
        viewMenu.append(
            _("&Toggle Code Pane"),
            HotKey="Ctrl+E",
            OnHit=self.onToggleCodePane,
            ItemID="view_togglecode",
            bmp="",
            help=_("Show/hide Code Pane"),
        )
        editMenu = self.MenuBar.getMenu("base_edit")
        if editMenu.Children:
            editMenu.appendSeparator()
        editMenu.append(
            _("nClear O&utput"),
            HotKey="Ctrl+Back",
            ItemID="edit_clearoutput",
            OnHit=self.onClearOutput,
            help=_("Clear Output Window"),
        )

    def onViewZoomIn(self, evt):
        self.shell.SetZoom(self.shell.GetZoom() + 1)

    def onViewZoomNormal(self, evt):
        self.shell.SetZoom(0)

    def onViewZoomOut(self, evt):
        self.shell.SetZoom(self.shell.GetZoom() - 1)

    @classmethod
    def getBaseShellClass(cls):
        return dShell

    # Property definitions
    @property
    def FontFace(self):
        """Name of the font face used in the shell  (str)"""
        return self.shell.FontFace

    @FontFace.setter
    def FontFace(self, val):
        if self._constructed():
            self.shell.FontFace = val
        else:
            self._properties["FontFace"] = val

    @property
    def FontSize(self):
        """Size of the font used in the shell  (int)"""
        return self.shell.FontSize

    @FontSize.setter
    def FontSize(self, val):
        if self._constructed():
            self.shell.FontSize = val
        else:
            self._properties["FontSize"] = val

    @property
    def HistoryPanel(self):
        """Popup to display the command history  (read-only) (dDialog)"""
        fp = self.FloatingPanel
        try:
            create = self._historyPanel is None
        except AttributeError:
            create = True
        if create:
            fp.clear()
            pnl = self._historyPanel = _LookupPanel(fp)
            pnl.Height = max(200, self.Height - 100)
            fp.Sizer.append(pnl)
            fp.fitToSizer()
        return self._historyPanel

    @property
    def ShellClass(self):
        return self._shellClass

    @ShellClass.setter
    def ShellClass(self, val):
        """Class to use for the interactive shell  (dShell)"""
        if self._constructed():
            self._shellClass = val
        else:
            self._properties["ShellClass"] = val

    @property
    def SplitState(self):
        """
        Controls whether the output is in a separate pane (default) or intermixed with the commands.
        (bool)
        """
        return self._splitState

    @SplitState.setter
    def SplitState(self, val):
        if self._splitState != val:
            self._splitState = val
            if val:
                self.split()
                self.shell.interp.stdout = self._pseudoOut
                self.shell.interp.stderr = self._pseudoErr
            else:
                self.unsplit()
                self.shell.interp.stdout = self._stdOut
                self.shell.interp.stderr = self._stdErr

    DynamicSplitState = makeDynamicProperty(SplitState)


ui.dShellForm = dShellForm


def main():
    from ..application import dApp

    app = dApp(BasePrefKey="ui.dShellForm")
    app.MainFormClass = dShellForm
    app.setup()
    app.start()


if __name__ == "__main__":
    main()
