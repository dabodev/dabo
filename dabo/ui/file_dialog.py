# -*- coding: utf-8 -*-
import wx

from .. import application
from .. import constants
from .. import settings
from .. import ui
from ..localization import _


class OsDialogMixin(object):
    def _beforeInit(self):
        self._dir = self._fname = self._msg = self._path = self._wildcard = ""
        super()._beforeInit()

    def show(self):
        self._dir = self._fname = self._path = ""
        ret = constants.DLG_CANCEL
        res = self.ShowModal()
        if res == wx.ID_OK:
            ret = constants.DLG_OK
            if self._multiple:
                self._path = self.GetPaths()
            else:
                self._path = self.GetPath()
            if self._exposeFiles:
                self._dir = self.GetDirectory()
                if self._multiple:
                    self._fname = self.GetFilenames()
                else:
                    self._fname = self.GetFilename()
        return ret

    def release(self):
        self.Destroy()

    @property
    def Directory(self):
        """The directory of the selected file or files (str)"""
        return self._dir

    @Directory.setter
    def Directory(self, dir):
        if self._exposeFiles:
            self.SetDirectory(dir)

    @property
    def FileName(self):
        """The name of the selected file (str) or files (tuple of strs)"""
        return self._fname

    @FileName.setter
    def FileName(self, fn):
        if self._exposeFiles:
            self.SetFilename(fn)

    @property
    def Message(self):
        """The prompt displayed to the user.  (str)"""
        return self._msg

    @Message.setter
    def Message(self, msg):
        self.SetMessage(msg)

    @property
    def Path(self):
        """The full path of the selected file (str)  or files (tuple of strs)"""
        return self._path

    @Path.setter
    def Path(self, pth):
        self.SetPath(pth)

    @property
    def Wildcard(self):
        """The wildcard that will limit the files displayed in the dialog.  (str)"""
        return self._wildcard

    @Wildcard.setter
    def Wildcard(self, txt):
        if self._exposeFiles:
            self.SetWildcard(txt)


class dFileDialog(OsDialogMixin, wx.FileDialog):
    """Creates a file dialog, which asks the user to choose a file."""

    _exposeFiles = True

    def __init__(
        self,
        parent=None,
        message=_("Choose a file"),
        defaultPath="",
        defaultFile="",
        wildcard="*.*",
        multiple=False,
        style=wx.FD_OPEN,
    ):
        self._baseClass = dFileDialog
        if multiple:
            # wxPython changed the constant after 2.6
            try:
                multStyle = wx.FD_MULTIPLE
            except AttributeError:
                multStyle = wx.MULTIPLE
            style = style | multStyle

            self._multiple = True
        else:
            self._multiple = False
        if parent is None:
            app = settings.get_application()
            if app and app.ActiveForm:
                parent = app.ActiveForm
        super().__init__(
            parent=parent,
            message=message,
            defaultDir=defaultPath,
            defaultFile=defaultFile,
            wildcard=wildcard,
            style=style,
        )


class dFolderDialog(OsDialogMixin, wx.DirDialog):
    """Creates a folder dialog, which asks the user to choose a folder."""

    _exposeFiles = False

    def __init__(self, parent=None, message=_("Choose a folder"), defaultPath="", wildcard="*.*"):
        self._multiple = False
        self._baseClass = dFolderDialog
        if parent is None:
            parent = settings.get_application().ActiveForm
        super().__init__(
            parent=parent,
            message=message,
            defaultPath=defaultPath,
            style=wx.DD_NEW_DIR_BUTTON,
        )


class dSaveDialog(dFileDialog):
    """Creates a save dialog, which asks the user to specify a file to save to."""

    def __init__(
        self,
        parent=None,
        message=_("Save to:"),
        defaultPath="",
        defaultFile="",
        wildcard="*.*",
        style=wx.FD_SAVE,
    ):
        self._baseClass = dSaveDialog
        if parent is None:
            parent = settings.get_application().ActiveForm
        super().__init__(
            parent=parent,
            message=message,
            defaultPath=defaultPath,
            defaultFile=defaultFile,
            wildcard=wildcard,
            style=style,
        )


ui.dFileDialog = dFileDialog
ui.dFolderDialog = dFolderDialog
ui.dSaveDialog = dSaveDialog


if __name__ == "__main__":
    from . import test

    test.Test().runTest(dFileDialog)
    test.Test().runTest(dFolderDialog)
    test.Test().runTest(dSaveDialog)
