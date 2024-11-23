# -*- coding: utf-8 -*-
HANDLE_SIZE = 8
from .. import ui
from .. import events

from ..ui import dPanel


class DragHandle(dPanel):
    """The class for all the handles used to indicate the selected control
    that are dragged to resize the control. It has properties indicating
    whether it controls resizing the control in the up, right, down or left
    directions. These values are determined from the name of the handle,
    which follows a simple naming convention:
        First character: T, M, B => Top, Middle or Bottom
        Second character: L, M, R = > Left, Middle or Right
    When the contol is dragged, it passes the event up to its parent. The
    parent object then determines the affected control, and passes the
    event on to that control.
    """

    def __init__(self, parent, handleName):
        sz = (HANDLE_SIZE, HANDLE_SIZE)
        super(DragHandle, self).__init__(parent, Size=sz, Visible=False, BackColor="blue")
        self.handleName = handleName

        if self.handleName in ("TL", "BR"):
            cursor = dabo.ui.dUICursors.Cursor_Size_NWSE
        elif self.handleName in ("TR", "BL"):
            cursor = dabo.ui.dUICursors.Cursor_Size_NESW
        elif self.handleName in ("TM", "BM"):
            cursor = dabo.ui.dUICursors.Cursor_Size_NS
        else:
            cursor = dabo.ui.dUICursors.Cursor_Size_WE
        self.MousePointer = dabo.ui.dUICursors.getStockCursor(cursor)

        self.selection = None

        ud = handleName[0]
        lr = handleName[1]
        self.up = ud == "T"
        self.down = ud == "B"
        self.left = lr == "L"
        self.right = lr == "R"

        self.bindEvent(events.MouseLeftDown, self.onLeftDown)
        self.bindEvent(events.MouseLeftUp, self.onLeftUp)
        self.bindEvent(events.MouseMove, self.onMouseDrag)
        self.dragging = False

    def onLeftDown(self, evt):
        self.dragging = True
        self.Form.startResize(self, evt)

    def onLeftUp(self, evt):
        self.dragging = False
        self.Form.processLeftUp(self, evt)
        evt.stop()

    def onMouseDrag(self, evt, shft=None):
        if shft is None:
            try:
                shft = evt.EventData["shiftDown"]
            except AttributeError:
                shft = False
        if self.dragging:
            self.Form.resizeCtrl(self, evt)
