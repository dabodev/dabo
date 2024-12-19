# -*- coding: utf-8 -*-
import wx

from ..dLocalize import _
from . import dBorderSizer, dButton, dGauge, dLabel, dPanel


class dReportProgress(dPanel):
    def afterInit(self):
        ms = self.Sizer = dBorderSizer(self, "v", DefaultBorder=5)
        self.gauge = dGauge(self, Size=(75, 12))
        lblTitle = dLabel(self, Name="lblTitle", Caption="", FontBold=True)
        butCancel = dButton(
            self,
            Name="butCancelReportProgress",
            CancelButton=False,
            Caption="Cancel",
            Enabled=False,
            OnHit=self.onCancel,
        )
        ms.append(lblTitle)
        ms.append(self.gauge, "expand")
        ms.append(butCancel, alignment="right")
        self.Visible = False

    def show(self):
        self.oldCancel = self.Form.FindWindowById(wx.ID_CANCEL)
        butCancel = self.butCancelReportProgress
        if self.oldCancel:
            self.oldCancelEnabled = self.oldCancel.Enabled
            self.oldCancel.Enabled = False
            self.oldCancel.CancelButton = False
        butCancel.Enabled = True
        butCancel.CancelButton = True
        self.oldFocus = self.Form.ActiveControl
        self.setFocus()  ## Ensures a pressed 'esc' will register on our cancel button
        self.Visible = True

    def hide(self):
        butCancel = self.butCancelReportProgress
        self.Visible = False
        if self.oldFocus:
            self.oldFocus.setFocus()  ## Let 'esc' register on the form instead of our cancel button
        butCancel.Enabled = False
        butCancel.CancelButton = False
        if self.oldCancel:
            if self.oldCancelEnabled:
                self.oldCancel.Enabled = True
            self.oldCancel.CancelButton = True

    def updateProgress(self, val, range_):
        self.gauge.Range = range_
        self.gauge.Value = val
        self.gauge.refresh()

    def onCancel(self, evt):
        evt.stop()  ## keep dialogs from automatically being closed.
        if not self.Visible:
            return
        self.cancel()

    def cancel(self):
        self.ProcessObject.cancel()

    # Property definitions
    @property
    def Caption(self):
        """Specifies the caption of the progress bar."""
        return self.lblTitle.Caption

    @Caption.setter
    def Caption(self, val):
        self.lblTitle.Caption = val
        self.fitToSizer()

    @property
    def ProcessObject(self):
        """Specifies the object that is processing (a dReportWriter instance, for example)."""
        self._processObject = getattr(self, "_processObject", None)
        return self._processObject

    @ProcessObject.setter
    def ProcessObject(self, val):
        self._processObject = val


ui.dReportProgress = dReportProgress
