"""
Author: Samuel Dunn
Intent: Have a playground with accessible wx.lib.inspection.InspectionTool for
        triaging issues in dabo.
"""

import wx

from dabo.dLocalize import _
from dabo.ui import dMenu, dMenuBar, dMenuItem


class MenuBar(dMenuBar):
    def _afterInit(self):
        self.dmenu = self.appendMenu(MyDaboMenu(0, self, MenuID="base_whatever"))
        self.dmenu2 = self.appendMenu(MyDaboMenu(1, self, MenuID="base_whatever2"))
        self.emenu = self.appendMenu(EditMenu(self, MenuID="base_edit"))
        self.vmenu = self.appendMenu(ViewMenu(self, MenuID="base_view"))
        super()._afterInit()


class EditMenu(dMenu):
    def _afterInit(self):
        super()._afterInit()
        app = self.Application
        self.Caption = _("&Edit")

        iconPath = "themes/tango/16x16"

        self.append(
            _("&Undo"),
            HotKey="Ctrl+Z",
            OnHit=app.onEditUndo,
            bmp="%s/actions/edit-undo.png" % iconPath,
            ItemID="edit_undo",
            help=_("Undo last action"),
        )

        self.append(
            _("&Redo"),
            HotKey="Ctrl+Shift+Z",
            OnHit=app.onEditRedo,
            bmp="%s/actions/edit-redo.png" % iconPath,
            ItemID="edit_redo",
            help=_("Undo last undo"),
        )

        self.appendSeparator()

        self.append(
            _("Cu&t"),
            HotKey="Ctrl+X",
            OnHit=app.onEditCut,
            bmp="%s/actions/edit-cut.png" % iconPath,
            ItemID="edit_cut",
            help=_("Cut selected text"),
        )

        self.append(
            _("&Copy"),
            HotKey="Ctrl+C",
            OnHit=app.onEditCopy,
            bmp="%s/actions/edit-copy.png" % iconPath,
            ItemID="edit_copy",
            help=_("Copy selected text"),
        )

        self.append(
            _("&Paste"),
            HotKey="Ctrl+V",
            OnHit=app.onEditPaste,
            bmp="%s/actions/edit-paste.png" % iconPath,
            ItemID="edit_paste",
            help=_("Paste text from clipboard"),
        )

        self.append(
            _("Select &All"),
            HotKey="Ctrl+A",
            OnHit=app.onEditSelectAll,
            bmp="%s/actions/edit-select-all.png" % iconPath,
            ItemID="edit_selectall",
            help=_("Select all text"),
        )

        self.appendSeparator()

        # By default, the Find and Replace functions use a single dialog. The
        # commented lines below this enable the plain Find dialog call.
        self.append(
            _("&Find / Replace"),
            HotKey="Ctrl+F",
            OnHit=app.onEditFind,
            bmp="%s/actions/edit-find-replace.png" % iconPath,
            ItemID="edit_findreplace",
            help=_("Find or Replace text in the active window"),
        )

        self.append(
            _("Find A&gain"),
            HotKey="Ctrl+G",
            OnHit=app.onEditFindAgain,
            bmp="",
            ItemID="edit_findagain",
            help=_("Repeat the last search"),
        )

        self.appendSeparator()

        self.append(
            _("Pr&eferences"),
            OnHit=app.onEditPreferences,
            bmp="%s/categories/preferences-system.png" % iconPath,
            ItemID="edit_preferences",
            help=_("Set user preferences"),
            special="pref",
        )


class ViewMenu(dMenu):
    def _afterInit(self):
        super()._afterInit()
        app = self.Application
        _ = lambda a: a
        self.Caption = _("&View")

        self.append(
            _("Increase Font Size"),
            HotKey="Ctrl++",
            ItemID="view_zoomin",
            OnHit=app.fontZoomIn,
            help=_("Increase the font size"),
        )
        self.append(
            _("Decrease Font Size"),
            HotKey="Ctrl+-",
            ItemID="view_zoomout",
            OnHit=app.fontZoomOut,
            help=_("Decrease the font size"),
        )
        self.append(
            _("Normal Font Size"),
            HotKey="Ctrl+/",
            ItemID="view_zoomnormal",
            OnHit=app.fontZoomNormal,
            help=_("Set font size to normal"),
        )

        if app.ShowSizerLinesMenu:
            self.appendSeparator()
            self.Parent.sizerLinesMenuItem = self.append(
                _("Show/Hide Sizer &Lines"),
                HotKey="Ctrl+L",
                OnHit=app.onShowSizerLines,
                menutype="check",
                ItemID="view_showsizerlines",
                help=_("Cool sizer visualizing feature; check it out!"),
            )


class MyDaboMenu(dMenu):
    def __init__(self, pos, *args, **kwargs):
        self.__pos = pos
        super().__init__(*args, **kwargs)

    def _afterInit(self):
        super()._afterInit()

        app = self.Application

        # Set caption:
        self.Caption = f"d&Menu{self.__pos}"

        # dmi = dMenuItem(self, Caption="dMenuItem")
        # self.appendItem(dmi)

        # Try using daboMenu.append ( ... ) like dBaseMenuBar menus do.
        self.appendSeparator()
        self.append("directly appended", help="help text")
        self.append(
            "has OnHit",
            help="help text 2",
            OnHit=lambda *args, **kwargs: print(f"dMenuItem OnHit: args {args}, kwargs {kwargs}"),
        )
        self.append(
            "has bmp",
            help="has bmp",
            bmp="themes/tango/16x16/apps/utilities-terminal.png",
        )
        self.append("no help", bmp="themes/tango/16x16/apps/system-search.png")
        self.append("checkbox item", help="this item has a checkbox", menutype="check")
        self.append("has id", ItemID="menu_hasid")
        self.append("has hotkey", HotKey="Ctrl+-")
        self.appendSeparator()

        self.append(
            _("Close Windo&w"),
            HotKey="Ctrl+W",
            OnHit=app.onWinClose,
            ItemID="file_close",
            help=_("Close the current window"),
        )

        self.append(
            _("&Quit"),
            HotKey="Ctrl+Q",
            id=wx.ID_EXIT,
            OnHit=app.onFileExit,
            bmp="themes/tango/16x16/actions/system-log-out.png",
            ItemID="file_quit",
            help=_("Exit the application"),
        )


def main():
    from wx.lib.inspection import InspectionTool

    import dabo
    from dabo.ui import dForm

    app = dabo.dApp()
    app.MainFormClass = None
    app.setup()

    # Select menu creation style here. The latter line will allow the user to call
    # playground.setupTestMenuBar(form_object) after mainloop construction.

    # form = dForm(None, MenuBarClass=MenuBar)
    form = dForm(None, MenuBarClass=None, ShowMenuBar=False)

    form.show()

    InspectionTool().Show(True)

    app.start()


def setupTestMenuBar(frame):
    from dabo.ui import dMenu, dMenuItem

    mb = MenuBar()

    frame.SetMenuBar(mb)


if __name__ == "__main__":
    main()
