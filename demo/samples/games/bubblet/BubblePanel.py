# -*- coding: utf-8 -*-
import dabo
import dabo.ui
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import makeProxyProperty
import random
from dabo.ui import dPanel


class BubblePanel(dPanel):
    def afterInit(self):
        self.Buffered = False

        self._popped = False
        self._selected = False
        self._colors = ["blue", "green", "red", "yellow", "purple"]
        self._color = random.choice(self._colors)
        # Used to detect size changes
        self._sizeCache = (0, 0)

        plat = self.Application.Platform
        if plat == "Win":
            self.selectedBackColor = (192, 192, 255)
        else:
            self.selectedBackColor = (128, 128, 192)
        self.unselectedBackColor = (255, 255, 255)
        self.autoClearDrawings = plat in ("Win", "Gtk")
        self.row = -1
        self.col = -1
        # Create a background that will change to indicate
        # selected status.
        self.back = self.drawRectangle(0, 0, 1, 1, penWidth=0)
        # Create a dummy circle, and store the reference
        self.circle = self.drawCircle(0, 0, 1)
        self.DynamicVisible = lambda: not self.Popped
        self.onResize(None)
        self.update()

    def setRandomColor(self, repaint=False):
        self.Color = random.choice(self._colors)
        if repaint:
            self.Popped = False

    def update(self):
        dabo.ui.callAfterInterval(50, self._delayedUpdate)

    def _delayedUpdate(self):
        circ = self.circle
        back = self.back
        circ.AutoUpdate = back.AutoUpdate = False
        selct = self.Selected
        poppd = self.Popped
        back.FillColor = {
            True: self.selectedBackColor,
            False: self.unselectedBackColor,
        }[selct]
        circ.FillColor = {True: "white", False: self.Color}[poppd]
        circ.PenWidth = {True: 0, False: 1}[poppd]
        wd, ht = self.Size
        back.Width, back.Height = wd, ht
        pos = ((wd / 2), (ht / 2))
        rad = min(wd, ht) / 2
        circ.Xpos = int(wd / 2)
        circ.Ypos = int(ht / 2)
        circ.Radius = rad
        circ.AutoUpdate = back.AutoUpdate = True
        self._needRedraw = True
        super(BubblePanel, self).update()

    def onResize(self, evt):
        sz = self.Size
        if sz != self._sizeCache:
            self._sizeCache = sz
            self.update()

    def onMouseLeftClick(self, evt):
        self.Parent.bubbleClick(self)

    def _getColor(self):
        return self._color

    def _setColor(self, val):
        if val != self._color:
            if val is None:
                self._color = None
            else:
                self._color = val.lower()

    def _getPopped(self):
        return self._popped

    def _setPopped(self, val):
        if val != self._popped:
            self._popped = self.Visible = val
            self.update()

    def _getSelected(self):
        return self._selected

    def _setSelected(self, val):
        if val != self._selected:
            self._selected = val

    Color = property(_getColor, _setColor, None, _("Color for this bubble  (str or tuple)"))

    Popped = property(_getPopped, _setPopped, None, _("Is the bubble popped?  (bool)"))

    Selected = property(_getSelected, _setSelected, None, _("Selection Status  (bool)"))

    _proxyDict = {}
    Visible = makeProxyProperty(_proxyDict, "Visible", ("circle",))
