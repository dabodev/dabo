# -*- coding: utf-8 -*-
import os.path

import wx

from .. import events
from .. import ui
from ..base_object import dObject
from ..localization import _
from . import dControlMixin
from . import dMenu
from . import makeDynamicProperty


class dToolBar(dControlMixin, wx.ToolBar):
    """
    Creates a toolbar, which is a menu-like collection of icons.

    You may also add items to a toolbar such as separators and real Dabo
    controls, such as dropdown lists, radio boxes, and text boxes.

    Under Gtk only, the toolbar can be detached into a floating toolbar,
    and reattached by the user at will. wxPython doesn't support this behavior
    for Windows or Mac yet, though.
    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dToolBar
        self._toolbarItemClass = dToolBarItem
        preClass = wx.ToolBar

        style = self._extractKey((kwargs, properties, attProperties), "style", 0)
        # Note: need to set the TB_TEXT flag, in order for that to be toggleable
        #       after instantiation. Because most toolbars will want to have icons
        #       only, there is code in _initProperties to turn it off by default.
        kwargs["style"] = style | wx.TB_TEXT | wx.CLIP_CHILDREN

        # wx doesn't return anything for GetChildren(), but we are giving Dabo
        # that feature, for easy polymorphic referencing of the buttons and
        # controls in a toolbar.
        self._daboChildren = []

        # Need this to load/convert image files to bitmaps
        self._image = wx.NullImage

        dControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

    def _initProperties(self):
        # default to no text captions (this fires before user subclass code and user
        # overriding arguments, so it won't conflict if the user sets ShowCaptions
        # explicitly.
        self.ShowCaptions = False
        self.Dockable = True
        super()._initProperties()

    def _getInitPropertiesList(self):
        additional = [
            "Dockable",
        ]
        original = list(super()._getInitPropertiesList())
        return tuple(original + additional)

    def _realize(self):
        """
        There seems to be a bug in wxPython Mac since 2.8. There is an error
        thrown, but it doesn't seem to affect the behavior of the toolbar, so just
        let it pass.
        """
        try:
            self.Realize()
        except wx._core.PyAssertionError:
            # Only happens on the Mac
            pass

    def appendItem(self, itm):
        """Insert a dToolBarItem at the end of the toolbar."""
        self.AddTool(itm._wxToolBarItem)
        self._daboChildren.append(itm)
        itm._parent = self
        self._realize()
        return itm

    def insertItem(self, pos, itm):
        """Insert a dToolBarItem before the specified position in the toolbar."""
        self.InsertToolItem(pos, itm._wxToolBarItem)
        self._daboChildren.insert(pos, itm)
        itm._parent = self
        self._realize()
        return itm

    def prependItem(self, itm):
        """Insert a dToolBarItem at the beginning of the toolbar."""
        self.insertItem(0, itm)
        return itm

    def appendButton(self, caption, pic, toggle=False, tip="", help="", *args, **kwargs):
        """
        Adds a tool (button) to the toolbar.

        You must pass a caption and an image for the button. The picture can be a
        wx.Bitmap, or a path to an image file of any supported type. If you pass
        toggle=True, the button will exist in an up and down state. Pass the
        function you want to be called when this button is clicked in an
        'OnHit' param.
        """
        return self._appendInsertButton(None, caption, pic, toggle, tip, help, *args, **kwargs)

    def insertButton(self, pos, caption, pic, toggle=False, tip="", help="", *args, **kwargs):
        """
        Inserts a tool (button) to the toolbar at the specified position.

        You must pass a caption and an image for the button. The picture can be a
        wx.Bitmap, or a path to an image file of any supported type. If you pass
        toggle=True, the button will exist in an up and down state. Pass the
        function you want to be called when this button is clicked in an
        'OnHit' param.
        """
        return self._appendInsertButton(pos, caption, pic, toggle, tip, help, *args, **kwargs)

    def prependButton(self, caption, pic, toggle=False, tip="", help="", *args, **kwargs):
        """
        Inserts a tool (button) to the beginning of the toolbar.

        You must pass a caption and an image for the button. The picture can be a
        wx.Bitmap, or a path to an image file of any supported type. If you pass
        toggle=True, the button will exist in an up and down state. Pass the
        function you want to be called when this button is clicked in an
        'OnHit' param.
        """
        return self.insertButton(0, caption, pic, toggle, tip, help, *args, **kwargs)

    def _appendInsertButton(self, pos, caption, pic, toggle, tip, help, *args, **kwargs):
        """Common code for the append|insert|prependButton() functions."""
        if isinstance(pic, str):
            # path was passed
            picBmp = ui.strToBmp(pic)
        else:
            picBmp = pic
        enabled = self._extractKey(kwargs, "Enabled", True)

        wd, ht = picBmp.GetWidth(), picBmp.GetHeight()
        needScale = False

        if (self.MaxWidth > 0) and (wd > self.MaxWidth):
            wd = self.MaxWidth
            needScale = True
        if (self.MaxHeight > 0) and (ht > self.MaxHeight):
            ht = self.MaxHeight
            needScale = True
        if needScale:
            picBmp = self._resizeBmp(picBmp, wd, ht)

        if toggle:
            kind = wx.ITEM_CHECK
        else:
            kind = wx.ITEM_NORMAL
        id_ = wx.ID_ANY
        if pos is None:
            # append
            tool = self.AddTool(id_, caption, picBmp, shortHelp=tip, kind=kind)
        else:
            # insert
            tool = self.InsertTool(
                pos, id_, caption, picBmp, shortHelp=tip, longHelp=help, isToggle=toggle
            )
        tbiClass = self.ToolbarItemClass
        butt = tbiClass(tool, *args, **kwargs)

        try:
            self.ToggleTool(id_, toggle)
        except wx._core.PyAssertionError:
            ## The AssertionError: not implemented occurs on wxMac, even though
            ## ToggleTool() obviously is implemented, because it does work.
            pass
        self._realize()

        # Store the button reference
        if pos is None:
            self._daboChildren.append(butt)
        else:
            self._daboChildren.insert(pos, butt)
        butt._parent = self
        butt.Enabled = enabled

        return butt

    def appendControl(self, control):
        """Adds any Dabo Control to the toolbar."""
        butt = self.AddControl(control)
        butt.Control.SetLabel(control.Caption)
        # butt.SetLabel(control.Caption)
        self._realize()

        # Store the control reference:
        self._daboChildren.append(control)

        return control

    def insertControl(self, pos, control):
        """Inserts any Dabo Control to the toolbar at the specified position."""
        butt = self.InsertControl(pos, control)
        butt.SetLabel(control.Caption)
        self._realize()

        # Store the control reference:
        self._daboChildren.insert(0, control)

        return control

    def prependControl(self, control):
        """Inserts any Dabo Control to the beginning of the toolbar."""
        return self.insertControl(0, control)

    def appendSeparator(self):
        """Inserts a separator at the end of the toolbar."""
        tbiClass = self.ToolbarItemClass
        sep = tbiClass(self.AddSeparator())
        self._daboChildren.append(sep)
        sep._parent = self
        self._realize()
        return sep

    def insertSeparator(self, pos):
        """Inserts a separator before the specified position in the toolbar."""
        tbiClass = self.ToolbarItemClass
        sep = tbiClass(self.InsertSeparator(pos))
        self._daboChildren.insert(pos, sep)
        sep._parent = self
        self._realize()
        return sep

    def prependSeparator(self):
        """Inserts a separator at the beginning of the toolbar."""
        return self.insertSeparator(0)

    def remove(self, idxOrItem, release=True):
        """
        Removes an item from the toolbar. You can either pass a reference to
        the item, or its position in the toolbar. If release is True (the default),
        the item is deleted as well. If release is False, a reference to the  object
        will be returned, and the caller is responsible for deleting it.
        """
        if isinstance(idxOrItem, int):
            idx = idxOrItem
            itm = self.Children[idx]
        else:
            idx = self._getIndexByItem(idxOrItem)
            itm = idxOrItem
        if not self.hasItem(itm):
            # Nothing to do!
            return
        try:
            id_ = itm._id
            self.RemoveTool(id_)
        except AttributeError:
            # A control, not a toolbar tool
            itm.Visible = False
        del self._daboChildren[idx]
        itm._parent = None
        if release:
            itm.Destroy()
        return itm

    def hasItem(self, itm):
        """
        Given a toolbar item, returns True or False depending on whether
        that item is currently in this toolbar.
        """
        return itm in self._daboChildren

    def getItemIndex(self, caption):
        """
        Returns the index of the item with the specified caption.

        If the item isn't found, None is returned.
        """
        for pos, itm in enumerate(self.Children):
            if itm.Caption == caption:
                return pos
        return None

    def getItem(self, caption):
        """
        Returns a reference to the item with the specified caption.

        If the item isn't found, None is returned.
        """
        idx = self.getItemIndex(caption)
        if idx is not None:
            return self.Children[idx]
        return None

    def _resizeBmp(self, bmp, wd, ht):
        img = bmp.ConvertToImage()
        img.Rescale(wd, ht)
        return img.ConvertToBitmap()

    def _updBmpSize(self):
        toolBmpWd, toolBmpHt = self.GetToolBitmapSize()
        if self.MaxWidth:
            toolBmpWd = self.MaxWidth
        if self.MaxHeight:
            toolBmpHt = self.MaxHeight
        self.SetToolBitmapSize((toolBmpWd, toolBmpHt))

    def GetChildren(self):
        ## This overrides the wx default which just returns an empty list.
        return self._daboChildren

    def _recreateItem(self, itm):
        """
        Recreate the passed dToolBarItem, and put it back in its original place.

        This is necessary when changing some or all of the dToolBarItem properties,
        and is called from within that object as a callafter.
        """
        idx = self._getIndexByItem(itm)
        if idx is not None:
            self.remove(idx, False)
            self.insertItem(idx, itm)

    def _getIndexByItem(self, itm):
        """
        Given a dToolBarItem object reference, return the index in the toolbar.

        Return None if the item doesn't exist in the toolbar.
        """
        for idx, o in enumerate(self.Children):
            if o == itm:
                return idx
        return None

    @property
    def Dockable(self):
        """
        Specifies whether the toolbar can be docked and undocked.  (bool)

        .. note::

        Currently, this only seems to work on Linux, and can't be changed after
        instantiation. Default is True.
        """
        return self._hasWindowStyleFlag(wx.TB_DOCKABLE)

    @Dockable.setter
    def Dockable(self, val):
        self._delWindowStyleFlag(wx.TB_DOCKABLE)
        if val:
            self._addWindowStyleFlag(wx.TB_DOCKABLE)

    @property
    def MaxHt(self):
        """
        Specifies the maximum height of added buttons.  (int)

        When set to zero, there will be no height limit.
        """
        try:
            v = self._maxHt
        except AttributeError:
            v = self._maxHt = 0
        return v

    @MaxHt.setter
    def MaxHt(self, val):
        self._maxHt = val
        if self._constructed():
            self._updBmpSize()
        else:
            self._properties["MaxHeight"] = val

    @property
    def MaxWd(self):
        """
        Specifies the maximum width of added buttons.  (int)

        When set to zero, there will be no width limit.
        """
        try:
            v = self._maxWd
        except AttributeError:
            v = self._maxWd = 0
        return v

    @MaxWd.setter
    def MaxWd(self, val):
        self._maxWd = val
        if self._constructed():
            self._updBmpSize()
        else:
            self._properties["MaxWidth"] = val

    @property
    def ShowCaptions(self):
        """Specifies whether the text captions are shown in the toolbar. Default=False  (bool)"""
        return self._hasWindowStyleFlag(wx.TB_TEXT)

    @ShowCaptions.setter
    def ShowCaptions(self, val):
        self._delWindowStyleFlag(wx.TB_TEXT)
        if val:
            self._addWindowStyleFlag(wx.TB_TEXT)
        if self._constructed():
            self._realize()

    @property
    def ShowIcons(self):
        """
        Specifies whether the icons are shown in the toolbar.  (bool)

        Note that you can set both ShowCaptions and ShowIcons to False, but in that case, the icons
        will still show. Default=True.
        """
        return not self._hasWindowStyleFlag(wx.TB_NOICONS)

    @ShowIcons.setter
    def ShowIcons(self, val):
        self._delWindowStyleFlag(wx.TB_NOICONS)
        if not val:
            self._addWindowStyleFlag(wx.TB_NOICONS)
        if self._constructed():
            self._realize()

    @property
    def ToolbarItemClass(self):
        """Class to instantiate for toolbar items. Default=dToolBarItem.  (varies)"""
        return self._toolbarItemClass

    @ToolbarItemClass.setter
    def ToolbarItemClass(self, val):
        if self._constructed():
            self._toolbarItemClass = val
        else:
            self._properties["ToolbarItemClass"] = val

    DynamicShowCaptions = makeDynamicProperty(ShowCaptions)
    DynamicShowIcons = makeDynamicProperty(ShowIcons)


class dToolBarItem(dObject):
    """Creates a toolbar item."""

    ## I can't figure out, for the life of me, how to mix-in dObject with
    ## wx.ToolBarToolBase - I always get a RunTimeError that there isn't a
    ## constructor. Therefore, I've made this wrapper class to decorate the
    ## wx.ToolBarToolBase instance that comes back from the AddTool()
    ## function.
    def __init__(self, wxItem=None, OnHit=None, *args, **kwargs):
        if wxItem is None:
            wxItem = self._getWxToolBarItem()
        self._wxToolBarItem = wxItem
        self._id = wxItem.GetId()
        self._parent = None
        self._dynamic = {}
        app = self.Application
        if app:
            app.uiApp.Bind(wx.EVT_MENU, self.__onWxHit, wxItem)
        super().__init__(*args, **kwargs)
        if OnHit is not None:
            self.bindEvent(events.Hit, OnHit)
        if wxItem.ToolBar:
            wxItem.ToolBar.bindEvent(events.Update, self.__onUpdate)

    def __getattr__(self, attr):
        """Exposes the underlying wx functions and attributes."""
        if hasattr(self._wxToolBarItem, attr):
            return getattr(self._wxToolBarItem, attr)
        raise AttributeError

    def _getWxToolBarItem(self):
        """Create the underlying wxToolBarToolBase item, and attach it to self."""
        # The only way I can figure out how to do this is to call
        # toolbar.AddTool() and save the result. Hence, the throwaway toolbar.
        tb = dToolBar(self.Application.ActiveForm)
        id_ = wx.ID_ANY
        wxItem = tb.AddTool(id_, "temp", ui.strToBmp("dCheckBox"))
        tb.RemoveTool(id_)
        tb.release()
        return wxItem

    def __onUpdate(self, evt):
        ui.callAfter(self.__updateDynamicProps)

    def __updateDynamicProps(self):
        for prop, func in list(self._dynamic.items()):
            if isinstance(func, tuple):
                args = func[1:]
                func = func[0]
            else:
                args = ()
            setattr(self, prop, func(*args))

    def __onWxHit(self, evt):
        self.raiseEvent(events.Hit)

    def GetChildren(self):
        # Placeholder to satisfy some wx layer code.
        return []

    def IsTopLevel(self):
        # Placeholder to satisfy some wx layer code.
        return True

    @property
    def CanToggle(self):
        """
        Specifies whether the toolbar item can be toggled.  (bool)

        For toggleable items, the Value property will tell you if the item is
        currently toggled or not.
        """
        return bool(self._wxToolBarItem.CanBeToggled())

    @CanToggle.setter
    def CanToggle(self, val):
        self._wxToolBarItem.ToggleTool(bool(val))

    @property
    def Caption(self):
        """Specifies the text caption of the toolbar item.

        You will only see the caption if dToolBar.ShowCaptions is set to True.
        """
        return self._wxToolBarItem.GetLabel()

    @Caption.setter
    def Caption(self, val):
        self._wxToolBarItem.SetLabel(val)
        if self.Parent:
            ui.callAfter(self.Parent._recreateItem, self)

    @property
    def Enabled(self):
        """Specifies whether the user may interact with the button."""
        return self.Parent.GetToolEnabled(self._id)

    @Enabled.setter
    def Enabled(self, val):
        if self.Parent:
            self.Parent.EnableTool(self._id, bool(val))
        else:
            self.Enable(bool(val))

    @property
    def Parent(self):
        """Contains an object reference to the containing toolbar."""
        return self._parent

    @property
    def Value(self):
        """
        Specifies whether the toolbar item is toggled or not.  (bool)

        For items with CanToggle = True, returns one of True or False, depending on the state of the
        button. For items with CanToggle = False, returns None.
        """
        if self.CanToggle:
            return bool(self.Parent.GetToolState(self._id))
        return None

    @Value.setter
    def Value(self, val):
        assert self.CanToggle, "Can't set Value on a non-toggleable tool."
        if self.Parent:
            self.Parent.ToggleTool(self._id, bool(val))
        else:
            if bool(self.IsToggled()) != bool(val):
                self.Toggle()

    DynamicCaption = makeDynamicProperty(Caption)
    DynamicEnabled = makeDynamicProperty(Enabled)


ui.dToolBar = dToolBar
ui.dToolBarItem = dToolBarItem


class _dToolBar_test(dToolBar):
    def initProperties(self):
        self.MaxWidth = 22
        self.MaxHeight = 22

    def afterInit(self):
        iconPath = "themes/tango/22x22"
        self.appendButton(
            "Copy",
            pic="%s/actions/edit-copy.png" % iconPath,
            toggle=False,
            OnHit=self.onCopy,
            tip="Copy",
            help="Much Longer Copy Help Text",
        )

        self.appendButton(
            "Toggle",
            pic="%s/actions/system-shutdown.png" % iconPath,
            toggle=True,
            OnHit=self.onToggle,
            tip="Toggle me",
            help="Toggle me",
        )

        self.appendButton(
            "Dabo",
            pic="daboIcon128",
            toggle=True,
            tip="Dabo! Dabo! Dabo!",
            help="Large icon resized to fit in the max dimensions",
        )

        self.appendSeparator()

        self.appendButton(
            "Exit",
            pic="%s/actions/system-log-out.png" % iconPath,
            toggle=True,
            OnHit=self.onExit,
            tip="Exit",
            help="Quit the application",
        )

    def onCopy(self, evt):
        ui.info("Copy Clicked!")

    def onToggle(self, evt):
        item = evt.EventObject
        ui.info("CHECKED: %s, ID: %s" % (item.Value, item.GetId()))

    def onExit(self, evt):
        app = self.Application
        if app:
            app.onFileExit(None)
        else:
            ui.stop("Sorry, there isn't an app object - can't exit.")


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dToolBar_test)
