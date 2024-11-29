#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import os.path
import keyword
import code
import inspect
import operator

use_subprocess = True
try:
    import subprocess
except ImportError:
    use_subprocess = False

from .. import ui
from ..application import dApp
from .. import events
from ..dLocalize import _
from ..lib.reportUtils import getTempFile
from ..ui import dBaseMenuBar
from ..ui import dBitmapButton
from ..ui import dDropdownList
from ..ui import dEditBox
from ..ui import dEditor
from ..ui import dForm
from ..ui import dImage
from ..ui import dLabel
from ..ui import dMenu
from ..ui import dOkCancelDialog
from ..ui import dPage
from ..ui import dPageFrame
from ..ui import dPanel
from ..ui import dSizer
from ..ui import dSplitter
from ..ui import dTextBox


class EditPageSplitter(dSplitter):
    def __init__(self, *args, **kwargs):
        kwargs["createPanes"] = True
        super(EditPageSplitter, self).__init__(*args, **kwargs)
        self.ShowPanelSplitMenu = False

    def initProperties(self):
        self.Width = 250
        self.Height = 200
        self.MinimumPanelSize = 20

    def onSashDoubleClick(self, evt):
        evt.stop()

    def onContextMenu(self, evt):
        evt.stop()

    def onSashPositionChanged(self, evt):
        self.Parent.updateSashPos()


class EditorEditor(dEditor):
    def addDroppedText(self, txt):
        curr = self.Value
        ss, se = self.SelectionStart, self.SelectionEnd
        self.Value = "%s%s%s" % (curr[:ss], txt, curr[se:])
        self.SelectionStart = ss
        self.SelectionEnd = ss + len(txt)

    def _getTextSource(self):
        return self.Form.getTextSource()


class EditorPage(dPage):
    def initProperties(self):
        self.p = None
        self.outputText = ""
        self._outputSashExtra = self.Application.getUserSetting("editorform.outputSashExtra", 100)

    def afterInit(self):
        self.splitter = EditPageSplitter(self, Orientation="h")
        self.splitter.SashPosition = self.Height - self._outputSashExtra

        self.splitter.Panel1.Sizer = dSizer()
        self.splitter.Panel2.Sizer = dSizer()

        self.editor = EditorEditor(self.splitter.Panel1)
        self.editor.UseBookmarks = True
        self.editor.page = self
        self.output = dEditBox(self.splitter.Panel2)
        self.output.ReadOnly = True

        self.splitter.Panel1.Sizer.append1x(self.editor)
        self.splitter.Panel2.Sizer.append1x(self.output)

        self.Sizer = dSizer()
        self.Sizer.append1x(self.splitter)

        self.updateTimer = ui.callEvery(1000, self.outputUpdate)

        self.layout()

        self.editor.setFocus()
        self.editor.bindEvent(events.TitleChanged, self.onTitleChanged)
        self.editor.bindEvent(events.MouseRightClick, self.Form.onEditorRightClick)
        # Set up the file drop target
        self.editor.DroppedFileHandler = self.Form
        # Set up the text drop target
        ### NOTE: currently we can only have text or file drops, not both
        self.editor.DroppedTextHandler = self.Form
        # Update Hide/Show of output. Default to hidden
        self.showOutput(self.Application.getUserSetting("visibleOutput", False))
        # Set the initial title
        ui.callAfter(self.onTitleChanged, None)
        # It's weird without this, self.splitter._constructed is not true
        ui.callAfter(self.splitter._setOrientation, "h")
        ui.callAfter(self.updateSashPos)

    def onResize(self, evt):
        self.splitter.SashPosition = self.Height - self._outputSashExtra

    def updateSashPos(self):
        if self.splitter.SashPosition > 0:
            self._outputSashExtra = self.Height - self.splitter.SashPosition
        self.Application.setUserSetting("editorform.outputSashExtra", self._outputSashExtra)

    def outputUpdate(self):
        if self and self.p:
            # need a nonblocking way of getting stdout and stderr
            self.outputText = self.outputText + self.p.stdout.read() + self.p.stderr.read()
            if not self.p.poll() is None:
                self.p = None
            self.output.Value = self.outputText

    def showOutput(self, show):
        self.splitter.Split = show

    def onTitleChanged(self, evt):
        title = self.editor._title
        self.Caption = title
        self.Form.onTitleChanged(evt)

    def onPageEnter(self, evt):
        self.editor.setFocus()

    def onPageLeave(self, evt):
        self.editor.setInactive()

    def onDestroy(self, evt):
        ui.callAfter(self.Form.onTitleChanged, evt)

    def _getPathInfo(self):
        try:
            ret = self.editor._fileName
        except:
            ret = ""
        return ret

    PathInfo = property(_getPathInfo, None, None, _("Path to the file being edited  (str)"))


class EditorPageFrame(dPageFrame):
    def beforeInit(self):
        self.PageClass = EditorPage

    def getTextSource(self):
        txt = []
        for pg in self.Pages:
            txt.append(pg.editor.Value)
        return " ".join(txt)

    def checkChanges(self, closing=False):
        """Cycle through the pages, and if any contain unsaved changes,
        ask the user if they should be saved. If they cancel, immediately
        stop and return False. If they say yes, save the contents. Unless
        they cancel, close each page.
        """
        ret = True
        for pg in self.Pages[::-1]:
            ed = pg.editor
            ret = ed.checkChangesAndContinue()
            if not ret:
                break
            elif closing:
                self.PageCount -= 1
        return ret

    def findEditor(self, pth, selectIt=False):
        """Returns the editor that is editing the specified file. If there
        is no matching editor, returns None. If selectIt is True, makes that
        editor the active editor.
        """
        ret = None
        for pg in self.Pages:
            if pg.editor._fileName == pth:
                ret = pg.editor
                if selectIt:
                    self.SelectedPage = pg
        return ret

    def editFile(self, pth, selectIt=False):
        ret = self.findEditor(pth, selectIt)
        if ret is None:
            # Create a new page
            pg = self.getBlankPage(True)
            try:
                fileTarget = pg.editor.openFile(pth)
                if fileTarget:
                    self.SelectedPage = pg
                    ret = pg
            except Exception as e:
                dabo.log.error(_("Error opening file '%(pth)s': %(e)s") % locals())
                ui.callAfter(self.removePage, pg)
                ret = None
        return ret

    def getBlankPage(self, create=False):
        """Returns the first page that is not associated with a file,
        and which has not been modified. If no such page exists, and
        the 'create' parameter is True, a new blank page is created
        and returned. Otherwise, returns None.
        """
        ret = None
        for pg in self.Pages:
            ed = pg.editor
            if ed._title.strip() == ed._newFileName.strip():
                ret = pg
                break
        if ret is None and create:
            self.PageCount += 1
            ret = self.Pages[-1]
        return ret

    def closeEditor(self, ed=None, checkChanges=True):
        if ed is None:
            ed = self.SelectedPage.editor
        if checkChanges:
            ret = ed.checkChangesAndContinue()
        else:
            ret = True
        if ret is not False:
            self.removePage(ed.page)
        return ret

    def newEditor(self):
        ret = self.getBlankPage(True)
        self.SelectedPage = ret
        return ret

    def selectByCaption(self, cap):
        pgs = [pg for pg in self.Pages if pg.Caption == cap]
        if pgs:
            pg = pgs[0]
        else:
            dabo.log.error(_("No matching page for %s") % cap)
            return
        self.SelectedPage = pg
        pg.editor.setFocus()

    def edFocus(self):
        self.SelectedPage.editor.setFocus()

    def _getCurrentEditor(self):
        try:
            return self.SelectedPage.editor
        except:
            return None

    def _getTitle(self):
        sp = self.SelectedPage
        try:
            ret = sp.PathInfo
            if sp.editor.Modified:
                ret += " *"
        except:
            ret = ""
        return ret

    CurrentEditor = property(
        _getCurrentEditor,
        None,
        None,
        _("References the currently active editor  (dEditor)"),
    )

    Title = property(_getTitle, None, None, _("Title of the active page  (str)"))


class EditorForm(dForm):
    def __init__(self, *args, **kwargs):
        super(EditorForm, self).__init__(*args, **kwargs)

    def afterInit(self):
        # Set up the file drop target
        self.DroppedFileHandler = self
        pnl = dPanel(self)
        self.Sizer.append1x(pnl)
        pnl.Sizer = dSizer("v")
        self._lastPath = self.Application.getUserSetting("lastPath", os.getcwd())
        super(EditorForm, self).afterInit()
        self.Caption = _("Dabo Editor")
        self.funcButton = dImage(
            pnl,
            ScaleMode="Clip",
            Size=(22, 22),
            ToolTipText=_("Show list of functions"),
        )
        # self.funcButton.Picture = ui.imageFromData(funcButtonData())
        self.funcButton.bindEvent(events.MouseLeftDown, self.onFuncButton)
        self.bmkButton = dImage(
            pnl, ScaleMode="Clip", Size=(22, 22), ToolTipText=_("Manage Bookmarks")
        )
        # self.bmkButton.Picture = ui.imageFromData(bmkButtonData())
        self.bmkButton.bindEvent(events.MouseLeftDown, self.onBmkButton)

        self.prntButton = dBitmapButton(pnl, Size=(22, 22), ToolTipText=_("Print..."))
        self.prntButton.Picture = "print"
        self.prntButton.bindEvent(events.Hit, self.onPrint)

        self.lexSelector = dDropdownList(pnl, ValueMode="String")
        self.lexSelector.bindEvent(events.Hit, self.onLexSelect)

        btnSizer = dSizer("H", DefaultSpacing=4)
        btnSizer.append(self.funcButton)
        btnSizer.append(self.bmkButton)
        btnSizer.append(self.prntButton)
        btnSizer.appendSpacer(10, proportion=1)
        lbl = dLabel(pnl, Caption=_("Language:"))
        if not self.Application.Platform.lower() == "win":
            lbl.FontSize -= 2
            self.lexSelector.FontSize -= 2
        btnSizer.append(lbl, valign="middle")
        btnSizer.append(self.lexSelector, valign="middle")

        pnl.Sizer.append(btnSizer, "x", border=4)

        self.pgfEditor = EditorPageFrame(pnl, TabPosition="Top")
        self.pgfEditor.bindEvent(events.PageChanged, self.onEditorPageChanged)
        pnl.Sizer.append1x(self.pgfEditor)
        self.layout()
        self.fillMenu()
        ui.callAfter(self.showPage, 0)

    def showPage(self, pg):
        """Shows the specified page, if it exists."""
        try:
            self.pgfEditor.SelectedPage = pg
            self.pgfEditor.edFocus()
        except:
            pass

    def onPrint(self, evt):
        self.CurrentEditor.onPrint()

    def onActivate(self, evt):
        """Check the files to see if any have been updated on disk."""
        self.checkForUpdatedFiles()

    def checkForUpdatedFiles(self):
        """If any file being edited has not been modified, and there is a more recent version
        on disk, update the file with the version on disk.
        """
        for pg in self.pgfEditor.Pages:
            ed = pg.editor
            if not ed.isChanged() and ed.checkForDiskUpdate():
                selpos = ed.SelectionPosition
                ed.openFile(ed._fileName)
                ed.SelectionPosition = selpos

    def onLexSelect(self, evt):
        self.CurrentEditor.Language = self.lexSelector.Value

    def onFuncButton(self, evt):
        evt.stop()
        flist = self.CurrentEditor.getFunctionList()
        pop = dMenu()
        if flist:
            for nm, pos, iscls in flist:
                prompt = nm
                if not iscls:
                    prompt = " - %s" % nm
                itm = pop.append(prompt, OnHit=self.onFunctionPop)
                itm.textPosition = pos
        else:
            pop.append(_("- no functions found -"))
        self.showContextMenu(pop)
        del pop

    def onFunctionPop(self, evt):
        ed = self.CurrentEditor
        pos = evt.menuItem.textPosition
        currLine = ed.LineNumber
        newLine = ed.getLineFromPosition(pos)
        if newLine > currLine:
            ed.moveToEnd()
        ed.ensureLineVisible(newLine)
        ed.LineNumber = newLine
        nextLinePos = ed.getPositionFromLine(newLine + 1)
        ed.SelectionPosition = (pos, nextLinePos - 1)

    def onIdle(self, evt):
        ed = self.CurrentEditor
        if ed:
            self.StatusText = "Line: %s, Col: %s" % (ed.LineNumber, ed.Column)

    def getTextSource(self):
        return self.pgfEditor.getTextSource()

    def onEditorRightClick(self, evt):
        ed = self.CurrentEditor
        pos = evt.mousePosition
        pp = ed.getPositionFromXY(pos)
        if pp < 0:
            # They clicked outside of the text area of the line. Find
            # a position just to the right of the margin
            lpos = ed.getMarginWidth()
            pp = ed.getPositionFromXY(lpos, pos[1])
        if pp < 0:
            # This is a totally blank line. Nothing can be done
            return
        ln = ed.getLineFromPosition(pp)
        ed.LineNumber = ln
        self.onBmkButton(evt)

    def onBmkButton(self, evt):
        evt.stop()
        ed = self.CurrentEditor
        bmkList = ed.getBookmarkList()
        pop = dMenu()
        currBmk = ed.getCurrentLineBookmark()
        if not currBmk:
            pop.append(_("Set Bookmark..."), OnHit=self.onSetBmk)
        else:
            pop.append(_("Clear Bookmark..."), OnHit=self.onClearBmk)
        if bmkList:
            pop.append(_("Clear All Bookmarks"), OnHit=self.onClearAllBmk)
            pop.appendSeparator()
            for nm in bmkList:
                itm = pop.append(nm, OnHit=self.onBookmarkPop)
        self.showContextMenu(pop)
        del pop

    def onBookmarkPop(self, evt):
        """Navigate to the chosen bookmark."""
        self.CurrentEditor.findBookmark(evt.prompt)

    def onSetBmk(self, evt):
        """Need to ask the user for a name for this bookmark."""
        nm = ui.getString(message=_("Name for this bookmark:"), caption=_("New Bookmark"))
        if not nm:
            # User canceled
            return
        ed = self.CurrentEditor
        if nm in ed.getBookmarkList():
            msg = (
                _(
                    "There is already a bookmark named '%s'. Creating a new bookmark with the same "
                    "name will delete the old one. Are you sure you want to do this?"
                )
                % nm
            )
            if not ui.areYouSure(
                message=msg,
                title=_("Duplicate Name"),
                defaultNo=True,
                cancelButton=False,
            ):
                return
        self.CurrentEditor.setBookmark(nm)

    def onClearBmk(self, evt):
        """Clear the current bookmark."""
        ed = self.CurrentEditor
        bmk = ed.getCurrentLineBookmark()
        if bmk:
            ed.clearBookmark(bmk)

    def onClearAllBmk(self, evt):
        """Remove all the bookmarks."""
        self.CurrentEditor.clearAllBookmarks()

    def onEditorPageChanged(self, evt):
        self.checkForUpdatedFiles()
        self.onTitleChanged(evt)
        self.setCheckedMenus()
        self.updateLex()

    def updateLex(self):
        if self.CurrentEditor:
            if not self.lexSelector.Choices:
                self.lexSelector.Choices = self.CurrentEditor.getAvailableLanguages()
            self.lexSelector.Value = self.CurrentEditor.Language

    def setCheckedMenus(self):
        ed = self.CurrentEditor
        if ed is None:
            self._autoAutoItem.Checked = self._wrapItem.Checked = False
            self._synColorItem.Checked = self._useTabsItem.Checked = self._lineNumItem = False
        else:
            self._autoAutoItem.Checked = ed.AutoAutoComplete
            self._wrapItem.Checked = ed.WordWrap
            self._synColorItem.Checked = ed.SyntaxColoring
            self._useTabsItem.Checked = ed.UseTabs
            self._lineNumItem.Checked = ed.ShowLineNumbers
            self._whiteSpaceItem.Checked = ed.ShowWhiteSpace
        self._showOutItem.Checked = self.Application.getUserSetting("visibleOutput", False)

    def beforeClose(self, evt):
        ret = self.pgfEditor.checkChanges(closing=True)
        return ret

    def processDroppedFiles(self, filelist):
        """Try to open each file up in an editor tab."""
        self.openRecursively(filelist)

    def processDroppedText(self, txt):
        """Add the text to the current editor."""
        self.CurrentEditor.addDroppedText(txt)

    def openRecursively(self, filelist):
        if isinstance(filelist, str):
            # Individual file passed
            filelist = [filelist]
        for ff in filelist:
            if os.path.isdir(ff):
                for fname in os.listdir(ff):
                    self.openRecursively(os.path.join(ff, fname))
            else:
                if os.path.isfile(ff):
                    self.openFile(ff, justReportErrors=True)

    def onDocumentationHint(self, evt):
        # Eventually, a separate IDE window can optionally display help contents
        # for the object. For now, just print the longdoc to the infolog.
        dabo.log.info(_("Documentation Hint received:\n\n%s") % evt.EventData["longDoc"])

    def onTitleChanged(self, evt):
        if self and self.pgfEditor:
            self.Caption = _("Dabo Editor: %s") % self.pgfEditor.Title

    def _curr_editor_attval(self, att):
        """Returns the value of the specified attribute for self.CurrentEditor
        if it is not None. Otherwise, it returns an empty string.
        """
        if self.CurrentEditor is None:
            return ""
        return getattr(self.CurrentEditor, att)

    def fillMenu(self):
        app = self.Application
        if not self.MenuBar:
            mb = self.MenuBar = dBaseMenuBar()
        else:
            mb = self.MenuBar
        fileMenu = mb.getMenu("base_file")

        editMenu = mb.getMenu("base_edit")
        mb.remove(mb.getMenuIndex("base_view"))
        runMenu = dMenu(Caption=_("&Run"), MenuID="base_run")
        mb.insertMenu(3, runMenu)

        fileMenu.prependSeparator()
        itm = fileMenu.prepend(
            _("Reload from Disk"),
            OnHit=self.onFileReload,
            ItemID="file_reload",
            help=_("Refresh the editor with the current version of the file on disk"),
        )
        itm.DynamicEnabled = self.hasFile

        fileMenu.prependSeparator()
        fileMenu.prepend(
            _("Save &As"),
            HotKey="Ctrl+Shift+S",
            OnHit=self.onFileSaveAs,
            bmp="saveAs",
            ItemID="file_saveas",
            help=_("Save under a different file name"),
        )
        fileMenu.prepend(
            _("&Save"),
            HotKey="Ctrl+S",
            OnHit=self.onFileSave,
            ItemID="file_save",
            DynamicEnabled=lambda: self._curr_editor_attval("Modified"),
            bmp="save",
            help=_("Save file"),
        )
        clsItem = fileMenu.getItem("file_close")
        if clsItem is not None:
            fileMenu.remove(clsItem)
        fileMenu.prepend(
            _("&Close Editor"),
            HotKey="Ctrl+W",
            OnHit=self.onFileClose,
            bmp="close",
            ItemID="file_close_editor",
            help=_("Close file"),
        )
        recentMenu = dMenu(Caption=_("Open Recent"), MenuID="file_open_recent", MRU=True)
        fileMenu.prependMenu(recentMenu)
        fileMenu.prepend(
            _("&Open"),
            HotKey="Ctrl+O",
            OnHit=self.onFileOpen,
            bmp="open",
            ItemID="file_open",
            help=_("Open file"),
        )
        fileMenu.prepend(
            _("&New"),
            HotKey="Ctrl+N",
            OnHit=self.onFileNew,
            bmp="new",
            ItemID="file_new",
            help=_("New file"),
        )

        editMenu.appendSeparator()
        editMenu.append(
            _("&Jump to line..."),
            HotKey="Ctrl+J",
            OnHit=self.onEditJumpToLine,
            bmp="",
            ItemID="edit_jump",
            help=_("Jump to line"),
        )
        editMenu.appendSeparator()
        editMenu.append(
            _("Co&mment Line"),
            HotKey="Ctrl+M",
            OnHit=self.onCommentLine,
            bmp="",
            ItemID="edit_comment",
            help=_("Comment out selection"),
        )
        editMenu.append(
            _("&Uncomment Line"),
            HotKey="Ctrl+Shift+M",
            OnHit=self.onUncommentLine,
            bmp="",
            ItemID="edit_uncomment",
            help=_("Uncomme&nt selection"),
        )
        editMenu.append(
            _("&AutoComplete"),
            HotKey="F5",
            OnHit=self.onAutoComplete,
            bmp="",
            ItemID="edit_autocomplete",
            help=_("Auto-complete the current text"),
        )
        editMenu.append(
            _("AutoComplete Length"),
            OnHit=self.onSetAutoCompleteLength,
            bmp="",
            ItemID="edit_autocompletelength",
            help=_("Set the length to trigger the AutoCompletion popup"),
        )
        self._autoAutoItem = editMenu.append(
            _("Automa&tic AutoComplete"),
            OnHit=self.onAutoAutoComp,
            bmp="",
            help=_("Toggle Automatic Autocomplete"),
            ItemID="edit_autoautocomplete",
            menutype="check",
        )
        editMenu.appendSeparator()
        moveMenu = dMenu(Caption=_("Move..."), MenuID="edit_move")
        editMenu.appendMenu(moveMenu)
        moveMenu.append(
            _("Previous Page"),
            HotKey="Alt+Left",
            OnHit=self.onPrevPage,
            DynamicEnabled=lambda: self.pgfEditor.PageCount > 1,
            bmp="",
            ItemID="move_prev",
            help=_("Switch to the tab to the left"),
        )
        moveMenu.append(
            _("Next Page"),
            HotKey="Alt+Right",
            OnHit=self.onNextPage,
            DynamicEnabled=lambda: self.pgfEditor.PageCount > 1,
            bmp="",
            ItemID="move_next",
            help=_("Switch to the tab to the right"),
        )
        moveMenu.append(
            _("Move Page Left"),
            HotKey="Alt+Shift+Left",
            OnHit=self.onMovePageLeft,
            DynamicEnabled=lambda: self.pgfEditor.PageCount > 1,
            bmp="",
            ItemID="move_pageleft",
            help=_("Move this editor tab to the left"),
        )
        moveMenu.append(
            _("Move Page Right"),
            HotKey="Alt+Shift+Right",
            OnHit=self.onMovePageRight,
            DynamicEnabled=lambda: self.pgfEditor.PageCount > 1,
            bmp="",
            ItemID="move_pageright",
            help=_("Move this editor tab to the right"),
        )
        moveMenu.append(
            _("Next Block"),
            HotKey="Ctrl+Shift+K",
            OnHit=self.onMoveUpBlock,
            DynamicEnabled=lambda: self._curr_editor_attval("Language") == "python",
            bmp="",
            ItemID="move_nextblock",
            help=_("Move to the next 'def' or 'class' statement"),
        )
        moveMenu.append(
            _("Previous Block"),
            HotKey="Ctrl+Shift+D",
            OnHit=self.onMoveDownBlock,
            DynamicEnabled=lambda: self._curr_editor_attval("Language") == "python",
            bmp="",
            ItemID="move_prevblock",
            help=_("Move to the previous 'def' or 'class' statement"),
        )

        editMenu.appendSeparator()
        self._wrapItem = editMenu.append(
            _("&Word Wrap"),
            HotKey="Ctrl+Shift+W",
            OnHit=self.onWordWrap,
            bmp="",
            ItemID="edit_wordwrap",
            help=_("Toggle WordWrap"),
            menutype="check",
        )
        self._synColorItem = editMenu.append(
            _("S&yntax Coloring"),
            HotKey="Ctrl+Shift+Y",
            OnHit=self.onSyntaxColoring,
            bmp="",
            ItemID="edit_syntaxcolor",
            help=_("Toggle Syntax Coloring"),
            menutype="check",
        )
        self._useTabsItem = editMenu.append(
            _("&Tabs"),
            HotKey="Ctrl+Shift+T",
            OnHit=self.onUseTabs,
            bmp="",
            ItemID="edit_usetabs",
            help=_("Toggle Tabs"),
            menutype="check",
        )
        self._lineNumItem = editMenu.append(
            _("Show &Line Numbers"),
            HotKey="Ctrl+Shift+L",
            OnHit=self.onLineNumber,
            bmp="",
            ItemID="edit_linenum",
            help=_("Toggle Line Numbers"),
            menutype="check",
        )
        self._whiteSpaceItem = editMenu.append(
            _("Show WhiteSpace"),
            HotKey="Ctrl+Shift+E",
            OnHit=self.onWhiteSpace,
            bmp="",
            ItemID="edit_whiteSpace",
            help=_("Toggle WhiteSpace Visibility"),
            menutype="check",
        )

        runMenu.append(
            _("&Run Script"),
            HotKey="Ctrl+Shift+R",
            OnHit=self.onRunScript,
            bmp="",
            ItemID="run_script",
            help=_("Run Script"),
        )
        self._showOutItem = runMenu.append(
            _("Hide/Show Output"),
            HotKey="Ctrl+Shift+O",
            OnHit=self.onOutput,
            bmp="",
            ItemID="run_output",
            help=_("Toggle the visibility of the Output pane"),
            menutype="check",
        )
        runMenu.append(
            _("Clear Output"),
            OnHit=self.onClearOutput,
            bmp="",
            ItemID="run_clear",
            help=_("Clear the contents of the Output pane"),
        )

        fontMenu = dMenu(Caption=_("Fo&nt"), MenuID="base_font")
        mb.insertMenu(4, fontMenu)
        fontMenu.append(
            _("Set Font Size"),
            OnHit=self.onFontSize,
            ItemID="font_setsize",
            help=_("Set Default Font Size"),
        )
        fontMenu.appendSeparator()
        fontMenu.append(
            _("Zoom &In"),
            HotKey="Ctrl++",
            OnHit=self.onViewZoomIn,
            bmp="zoomIn",
            ItemID="font_zoomin",
            help=_("Zoom In"),
        )
        fontMenu.append(
            _("&Normal Zoom"),
            HotKey="Ctrl+/",
            OnHit=self.onViewZoomNormal,
            bmp="zoomNormal",
            ItemID="font_zoomnormal",
            help=_("Normal Zoom"),
        )
        fontMenu.append(
            _("Zoom &Out"),
            HotKey="Ctrl+-",
            OnHit=self.onViewZoomOut,
            bmp="zoomOut",
            ItemID="font_zoomout",
            help=_("Zoom Out"),
        )
        fixed_width_fonts = ui.getAvailableFonts(fixed_width_only=True)
        all_fonts = ui.getAvailableFonts(fixed_width_only=False)
        fontMenu.appendSeparator()
        fontMenu.append(_("Fixed Width Fonts"), Enabled=False)
        for font in fixed_width_fonts:
            fontMenu.append(
                font,
                OnHit=self.onFontSelection,
                ItemID="font_%s" % font.replace(" ", "_"),
                menutype="Radio",
            )
        fontMenu.appendSeparator()
        fontMenu.append(_("All Fonts"), Enabled=False)
        for font in all_fonts:
            fontMenu.append(
                font,
                OnHit=self.onFontSelection,
                ItemID="font_%s" % font.replace(" ", "_"),
                menutype="Radio",
            )

        vp = mb.getMenuIndex("base_font")
        editorMenu = mb.insert(vp + 1, _("E&ditors"), MenuID="base_editors")
        editorMenu.bindEvent(events.MenuHighlight, self.onMenuOpen)

        # On non-Mac platforms, we may need to move the Help Menu
        # to the end.
        if app.Platform != "Mac":
            hlp = mb.getMenu("base_help")
            if hlp:
                mb.remove(hlp, False)
                mb.appendMenu(hlp)

    def hasFile(self, evt=None):
        """Dynamic method for the Reload From Disk menu."""
        # If there's a file, enable the menu
        return self._curr_editor_attval("_fileName")

    def onFileReload(self, evt):
        """Reload the file from disk."""
        ed = self.CurrentEditor
        fname = ed._fileName
        ed.openFile(fname)

    def onFontSelection(self, evt):
        """The user selected a font face for the editor."""
        face = evt.EventObject.Caption
        if self.CurrentEditor:
            self.CurrentEditor.changeFontFace(face)

    def onFontSize(self, evt):
        """Change the default font size for the editor."""
        if not self.CurrentEditor:
            return
        val = ui.getInt(_("Select new font size"), _("Font Size"), self.CurrentEditor._fontSize)
        if val is not None:
            self.CurrentEditor.changeFontSize(val)

    def onMenuOpen(self, evt):
        """Currently this never fires under Windows."""
        mn = evt.EventObject
        prm = mn.Caption
        if prm.replace("&", "") == _("Editors"):
            mn.clear()
            for pg in self.pgfEditor.Pages:
                prmpt = pg.editor._title
                mn.append(prmpt, OnHit=self.onEditorSelected, help=_("Select %s") % prmpt)
            if len(self.pgfEditor.Pages) > 1:
                mn.appendSeparator()
                mn.append(
                    _("Open in New Window"),
                    OnHit=self.onOpenInNew,
                    help=_("Open this document in a new window"),
                )
        elif prm == _("Font"):
            mn.setCheck(self.CurrentEditor._fontFace)

    def onOpenInNew(self, evt):
        """Open the current doc in a separate Editor window."""
        # Get the current state of the doc
        ed = self.CurrentEditor
        txt = ed.Text
        fname = ed.FilePath
        # Close the editor
        self.pgfEditor.closeEditor(ed, False)
        # Create a new editor form
        frm = EditorForm()
        frm.onFileNew(None)
        frm.openFile(fname)
        newEd = frm.CurrentEditor
        if newEd.Text != txt:
            newEd.Text = txt
        frm.show()
        frm.Position = self.Left + 20, self.Top + 20

    def onEditorSelected(self, evt):
        """Called when a menuitem in the Editors menu is chosen."""
        cap = evt.EventObject.Caption
        self.pgfEditor.selectByCaption(cap)

    def onFileNew(self, evt):
        target = self.pgfEditor.newEditor()
        target.setFocus()

    def onFileOpen(self, evt):
        fileNames = self.CurrentEditor.promptForFileName(
            prompt=_("Open"), path=self._lastPath, multiple=True
        )
        if fileNames is None:
            # They bailed
            return
        for fileName in fileNames:
            self._lastPath = os.path.split(fileName)[0]
            self.Application.setUserSetting("lastPath", self._lastPath)
            self.openFile(fileName)

    @classmethod
    def onMRUSelection(cls, evt):
        """This needs to be a classmethod, since the form
        that originally opens a file path might get closed, and
        if we bound the MRU action to an instance method, it
        would barf. So we make this a classmethod, and pass
        the call to the first EditorForm instance we can find.
        """
        # The prompt will have a number prepended to the actual path,
        # separated by a space.
        pth = evt.prompt.split(" ", 1)[-1]
        # Find the topmost form that is an EditorForm
        app = dabo.dAppRef
        try:
            app.ActiveForm.openFile(pth)
        except:
            # Call the first available EditorForm
            edf = [frm for frm in app.uiForms if isinstance(frm, EditorForm)][0]
            edf.openFile(pth)

    def openFile(self, pth, justReportErrors=False):
        """Open the selected file, if it isn't already open. If it is,
        bring its Editor to the front. If the specified file is not
        able to be opened and justReportErrors is True, a message is
        output to the error log; otherwise, and error is raised.
        """
        try:
            target = self.pgfEditor.editFile(pth, True)
        except Exception as e:
            if justReportErrors:
                dabo.log.error(_("Could not open file: %s") % e)
                target = None
            else:
                raise
        if target:
            # Add to the MRU list
            self.Application.addToMRU(_("Open Recent"), pth, self.onMRUSelection)
        self.updateLex()
        return target

    def onFileSave(self, evt):
        self.CurrentEditor.saveFile()

    def onFileClose(self, evt):
        self.pgfEditor.closeEditor()
        if self.pgfEditor.PageCount == 0:
            self.release()
        evt.stop()

    def onFileSaveAs(self, evt):
        fname = self.CurrentEditor.promptForSaveAs()
        if fname:
            self.CurrentEditor.saveFile(fname, force=True)

    def onEditJumpToLine(self, evt):
        class LineNumberDlg(dOkCancelDialog):
            def addControls(self):
                self.Caption = _("Jump To Line")
                self.lblLine = dLabel(self, Caption=_("Line Number:"))
                self.txtLine = dTextBox(self, SelectOnEntry=True)
                hs = dSizer("h")
                hs.append(self.lblLine, valign="middle")
                hs.append(self.txtLine, valign="middle")
                self.Sizer.append(hs, 1, halign="center")
                self.layout()
                self.txtLine.setFocus()
                self.txtLine.selectAll()

        currEditor = self.CurrentEditor
        dlg = LineNumberDlg(self)
        dlg.txtLine.Value = currEditor.LineNumber
        dlg.txtLine.Min = 1
        dlg.txtLine.Max = currEditor.LineCount
        dlg.Centered = dlg.Modal = True
        dlg.AutoSize = False
        dlg.show()
        if dlg.Accepted:
            currEditor.LineNumber = dlg.txtLine.Value
        dlg.release()

    def onCommentLine(self, evt):
        if self.CurrentEditor:
            self.CurrentEditor.onCommentLine(evt)

    def onUncommentLine(self, evt):
        if self.CurrentEditor:
            self.CurrentEditor.onUncommentLine(evt)

    def onAutoComplete(self, evt):
        self.CurrentEditor.autoComplete()

    def onSetAutoCompleteLength(self, evt):
        ed = self.CurrentEditor
        curr = ed.AutoAutoCompleteMinLen

        newlen = ui.getInt(_("Number of characters?"), _("Set AutoComplete Trigger"), curr)
        if newlen:
            ed.AutoAutoCompleteMinLen = newlen

    def onAutoAutoComp(self, evt):
        ed = self.CurrentEditor
        ed.AutoAutoComplete = not ed.AutoAutoComplete

    def onRunScript(self, evt):
        """Save the script to temp dir, and run it."""
        ed = self.CurrentEditor
        fileDir = os.path.split(ed.FilePath)[0]
        if fileDir:
            os.chdir(fileDir)
        txt = ed.Text
        fname = getTempFile(ext="py")
        ed.saveFile(fname, force=True, isTmp=True)

        # Find out if we will use pythonw or just python:
        if "linux" in sys.platform:
            cmd = "python"
        else:
            cmd = "pythonw"
        if use_subprocess:
            # The Echo hack:
            self.pgfEditor.SelectedPage.outputText = ""
            self.pgfEditor.SelectedPage.p = subprocess.Popen(
                (cmd, fname),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        else:
            # Use the old way
            os.system("%s %s" % (cmd, fname))

    def onViewZoomIn(self, evt):
        ed = self.CurrentEditor
        ed.increaseTextSize()
        self.Application.setUserSetting("editor.zoom", ed.ZoomLevel)

    def onViewZoomNormal(self, evt):
        ed = self.CurrentEditor
        ed.restoreTextSize()
        self.Application.setUserSetting("editor.zoom", ed.ZoomLevel)

    def onViewZoomOut(self, evt):
        ed = self.CurrentEditor
        ed.decreaseTextSize()
        self.Application.setUserSetting("editor.zoom", ed.ZoomLevel)

    def onWordWrap(self, evt):
        ed = self.CurrentEditor
        ed.WordWrap = not ed.WordWrap

    def onSyntaxColoring(self, evt):
        ed = self.CurrentEditor
        ed.SyntaxColoring = not ed.SyntaxColoring

    def onUseTabs(self, evt):
        ed = self.CurrentEditor
        ed.UseTabs = not ed.UseTabs
        ed.BackSpaceUnindents = not ed.UseTabs

    def onLineNumber(self, evt):
        ed = self.CurrentEditor
        ed.ShowLineNumbers = not ed.ShowLineNumbers

    def onWhiteSpace(self, evt):
        ed = self.CurrentEditor
        ed.ShowWhiteSpace = not ed.ShowWhiteSpace

    def onOutput(self, evt):
        show = self.MenuBar.getMenu(_("Run")).isItemChecked(_("Hide/Show Output"))
        self.Application.setUserSetting("visibleOutput", show)
        for pg in self.pgfEditor.Pages:
            pg.showOutput(show)

    def onClearOutput(self, evt):
        self.pgfEditor.SelectedPage.outputText = ""

    def onPrevPage(self, evt):
        self.pgfEditor.cyclePages(-1)
        self.pgfEditor.edFocus()

    def onNextPage(self, evt):
        self.pgfEditor.cyclePages(1)
        self.pgfEditor.edFocus()

    def onMovePageLeft(self, evt):
        """Move the selected page over one to the left in the
        pageframe. If it is already the leftmost, move it to the
        end of the right side.
        """
        pgf = self.pgfEditor
        pg = pgf.SelectedPage
        pos = pgf.Pages.index(pg)
        if pos == 0:
            # First page; move it to the end
            newPos = pgf.PageCount - 1
        else:
            newPos = pos - 1
        pgf.movePage(pos, newPos)

    def onMovePageRight(self, evt):
        """Move the selected page over one to the right in the pageframe. If it is already the
        rightmost, move it to the first position on the left.
        """
        pgf = self.pgfEditor
        pg = pgf.SelectedPage
        pos = pgf.Pages.index(pg)
        if pos == (pgf.PageCount - 1):
            # Last page; move it to the beginning
            newPos = 0
        else:
            newPos = pos + 1
        pgf.movePage(pos, newPos)

    def onMoveDownBlock(self, evt):
        """Move to the next class or method definition."""
        self._moveToBlock("down")

    def onMoveUpBlock(self, evt):
        """Move to the previous class or method definition."""
        self._moveToBlock("up")

    def _moveToBlock(self, direction):
        ed = self.CurrentEditor
        funcs = {"u": (min, operator.gt, 1), "d": (max, operator.lt, 0)}[direction.lower()[0]]
        pos = ed.SelectionPosition[funcs[2]]
        flist = ed.getFunctionList()
        fpos = [f[1] for f in flist if funcs[1](f[1], pos)]
        if fpos:
            newPos = funcs[0](fpos)
            ed.moveToEnd()
            newLine = ed.getLineFromPosition(newPos)
            ed.LineNumber = max(0, newLine - 5)
            nextLinePos = ed.getPositionFromLine(newLine + 1)
            ed.LineNumber = newLine
            ed.SelectionPosition = (newPos, nextLinePos - 1)

    def _getCurrentEditor(self):
        return self.pgfEditor.CurrentEditor

    CurrentEditor = property(
        _getCurrentEditor,
        None,
        None,
        _("References the currently active editor  (dEditor)"),
    )


def funcButtonData():
    # return \
    x = '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x16\x00\x00\x00\x16\x08\x02\
\x00\x00\x00K\xd6\xfbl\x00\x00\x00\x03sBIT\x08\x08\x08\xdb\xe1O\xe0\x00\x00\
\x02\'IDAT8\x8duS1\xae\xea@\x0c\xf4z\x1d\x8at\xd0 $J\xf4Z*()\xa8h\x80\x8e\
\x03 (\xa88\x01\x12\xe2\x08\xdc\x81\x86\x1b\xd0Sr\x01.@G\x81 R\x02\x9b\xec/&\
\xcf\xec\x07=\x17Q\xe4\xb5g\xed\x99\x1d\xb3\xd9l\xe8\x8f0\xc6\x10\x91\xf7>\
\xccx\xef?\xf2BD\x8b\xc5\xa2Z\xad\xea\x81\xd6\x85\xd5aR\x11\x1f\x8f\xc7v\xbb\
\x15"\xba\xdf\xef\xcc\x8cjc\x8c\xd6}\xa3\xe8\xe5\xc6\x18\xe7\\\x92$\xe5\x14\
\xd7\xeb5\xcb2k-\x80P]\x14\x05\x11\x89\x88s\xce{\x8f\xd3\xa2(p\x9a\xe7\xb9s.\
M\xd3\x12"\x8a"\x11\xa9T*\xd6Z\xe7\x9c\xb5\xd6{_\x14\x053\x03\x05p\xc6\x18d\
\x8c1Q\x14=\x9f\xcf7\x84\x88`~f\xb6\xd6\x02\x82\x99\x9b\xcd&v\xbe\\.X\x81\
\x99\xbd\xf7\xd8\x85\x99E\xa4\x84 \xa2J\xa5\x12E\x911\xc6Z\x8b]\xea\xf5:\x11\
\xed\xf7{":\x1e\x8f\xbd^/\xa4&\xcfs\xb4\x10\x91h\x1b\xbe\x1f\x9c\x13Q\xbf\
\xdf\x0fY\x04\n\xe8D\x8b(U\x98*$\x1f\x11r\xacL333\xe7y\xee\xbd\xff\x94\x00=\
\xb5Z\r\xff\x93\xc9D\xa7\xd3\xc7\xa6\xda\x95\x0c\xe2@DDD\xcfn\xb7\x1b \xf6\
\xfb\xfd\xe1pP9\xb4\x13\x95%\x17\xb8V\xe7\xc7\x7f\x18\x83\xc1@\xb5\xd0\xe2\
\xd7\xcb)k\xa2\xe3A\xd1O\x9f\x10i\xb3\x12d\x8c\x11\xb1\xce\xbd\xde\x1eQ!B\
\xd94>\x9e|\x08\xfd^\x04\x0cA\x11f\x8e\xe3X\x89P\x08\n\xac\t\x11\xbd\xf7\xce\
9"*Y\x80\x1c )M\xd3\xd3\xe9\x84\xfe\xd1h\x04\n\xa7\xd3i\xab\xd5\x8a\xe3\xb8\
\xd5j\xcdf30\x8a\xc5E\xa7\x02\x17\xb8\xaa\xddn\xb7\xdb\xed\xf0\xda\xe5ry>\
\x9f\xb3,k4\x1a\xcb\xe5\x12\xf7\x95\x04+\x91\x18\x01\x1b\xf1o \x1fEQ\xb7\xdb\
]\xaf\xd7???\xab\xd5\xaa\xd3\xe9\xc0\rX\xb04\x98\x88 \xab\x14~K3\x1c\x0e/\
\x97\xcbx<\xa6_\x8f\xfdg\xb3\xa2(\xd4\xdd:|\xe8\x17\x80\xce\xe7s5\xbe\xf7>\
\xcfs"\x12\xfc%I\xe2\x9c\xfbxW\xdf\x02\x87\x91e\xd9\xf3\xf9,!v\xbb\xdd_u\xdf\
\xf1m\xe5\x7f\xd0\xdbI\xf9\xcd\xb6\xabn\x00\x00\x00\x00IEND\xaeB`\x82'
    print(x)
    return x


def bmkButtonData():
    # return \
    y = '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x16\x00\x00\x00\x16\x08\x02\
\x00\x00\x00K\xd6\xfbl\x00\x00\x00\x03sBIT\x08\x08\x08\xdb\xe1O\xe0\x00\x00\
\x02\x7fIDAT8\x8duT\xbbJ,A\x10\xad\xee\xae\xdeUaDA\x84\xc5H\x19\xfc\x00A\xff\
BL\x0c\x16\x0c\x84\xf5\x01F\x1bh*\x88\x9f`.F~\x83b&\x08\xfe\x82\x82\xf1dF\
\xce\xa2=\xb7\xbb\xeb\x06gn9w\xbd\xb7\x83a\xa6\xab\xfa\xf4\xa9s\xaa\xc6\\^^\
\xd2\x7f\x961\x86\x88D\xa4\xbb#"S\xfbLD\'\'\'\x8b\x8b\x8b\x1a\xd0\xbcnvwS\
\x11\xeb\xba\xbe\xba\xbab"\xfa\xf8\xf8\xb0\xd6"\xdb\x18\xa3y?Q\xf4rcL\x8cq2\
\x99\xb4,\xde\xdf\xdfC\x08\xce9\x00!;\xe7LD\xcc\x1cc\x14\x11Ds\xce\x88\xa6\
\x94b\x8c___-\x84\xf7\x9e\x99{\xbd\x9es.\xc6\xe8\x9c\x13\x91\x9cs\xd349gf\
\xb6\xd6\xe2f}\xf1\xde7M\xf3\r\xc1\xcc\xe0o\xadu\xce\x01"\xa5\xd4\xef\xf7\
\xb5\x1c"\x02\x11\x11\xc1\xa7\xb5\x96\x99[\x08"\xea\xf5z\xde{c\x8csn0\x18\
\xe4\x9c\xcb\xb2|~~F\xcd\x1b\x1b\x1bUU-,,\xbc\xbc\xbc@\x91\x94\x12\x8e\x10\
\x91\xc51<\xb1\x00\xfa\xf6\xf6\xf6\xf8\xf8HDwwwUU\xb5\xfe1;\xe7\x98\x19\xc4q\
\xd0\xaaT\x08\xa3Z\xef\xfd\xf2\xf2\xf2\xcd\xcd\r3___\xaf\xac\xac\x00\x02i(\
\xd9Z\x9bR\x12\x91i\x0b4\xf5\xe0\xe0\xe0\xfe\xfe\xfe\xe1\xe1\xe1\xe9\xe9\xe9\
\xf8\xf8\xb8\xdbl\xea]\xab \x02\xe0\xa6,\x88h\x7f\x7f\x9f\x99G\xa3QQ\x14\xc3\
\xe1P\xa1q\x0c\x99\xad\x16\x08h\xcf(\xc4\xd2\xd2\xd2\xee\xeen]\xd7{{{EQ(\x8b\
?\r\xf2\xdd\xa9\xac\xf4\xe0\xa8\xd6\xc2\xccgggkkk\xc3\xe1\x10\xe6i\xa61\x86\
\xd9\xc5\xf8\xeb{F\xb4\xa9\xa7F`uu\xf5\xf4\xf4\x94\x88\x9a\xa6\xd1B\xbaz\xa1\
\x90\x16\x1eV!P\xd7u\x08\x01}%"!\x84\xa2(>??\x15\x1d&\x8aH\x8c\xb1\xd5\x02\
\xed\xacR\xcf\xcc\xcc\xcc\xcf\xcf\xa3s\xfa\xfd\xfe\xec\xec\xac1f4\x1a\x95e97\
7W\x96\xe5\xe1\xe1\xa1\xf6\xd17\x0b\xf8\x0cl\xd4\xd5%,"\xe3\xf1\xf8\xf5\xf55\
\x840\x18\x0c\xc6\xe31\xeek\x1dP!AAg,\xe7\x9cR\xca9;\xe7\xbc\xf7[[[\x17\x17\
\x17\xeb\xeb\xeb\xe7\xe7\xe7\x9b\x9b\x9b\x98\x06\xdc\xd4\x0e\x183c\xb7\xab\
\xfc\xd4\xda\xde\xde\xae\xaajggG\xdb\xf4\xaf1\xc3\xb5]\xc1\xa7\x0c\x02\xe8\
\xd1\xd1\x11TC(\xa5DD\x8c\xb7\xc9d\x12c\xecBP\xe7O\xf5\xcf\x15B\x80\xd9,"\
\xb7\xb7\xb7\xff\xcb\xfb\xb9\xa6z\x87\x88~\x03!\x94ZC\xeb\xb8\xaf\xa0\x00\
\x00\x00\x00IEND\xaeB`\x82'
    return y


def main():
    files = sys.argv[1:]
    app = dApp(MainFormClass=EditorForm, BasePrefKey="ide.Editor")
    app.setAppInfo("appName", _("Dabo Editor"))
    app.setAppInfo("appShortName", _("DaboEditor"))
    app.setup()

    frm = app.MainForm
    app._persistentMRUs = {_("Open Recent"): frm.onMRUSelection}

    def _openForms():
        frm.onFileNew(None)
        for file in files:
            frm.openFile(os.path.realpath(file))
        frm.show()

    ui.callAfter(_openForms)
    app.start()


if __name__ == "__main__":
    main()
