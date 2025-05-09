# -*- coding: utf-8 -*-
from ... import events
from ... import ui
from ...localization import _
from .. import dOkCancelDialog


class SortingForm(dOkCancelDialog):
    """This class affords a simple way to order a list of items."""

    def __init__(self, parent=None, Choices=[], *args, **kwargs):
        self._itms = list(Choices)
        super().__init__(parent=parent, *args, **kwargs)
        self.AutoSize = False
        self.Size = (330, 300)
        self._listCaption = ""

    def addControls(self):
        self.listBox = ui.dEditableList(
            self,
            Caption=self._listCaption,
            Choices=self._itms,
            Editable=False,
            CanDelete=False,
            CanAdd=False,
        )
        self.Sizer.append(self.listBox, 1, "expand", border=30, borderSides="all")
        self.layout()

    @property
    def Choices(self):
        try:
            return self.listBox.Choices
        except AttributeError:
            return self._itms

    # Property definitions
    @Choices.setter
    def Choices(self, chc):
        """Items in the list to sort.   (list)"""
        self._itms = self.listBox.Choices = list(chc)

    @property
    def ListCaption(self):
        """Caption for the sorting list  (str)"""
        return self.listBox.Caption

    @ListCaption.setter
    def ListCaption(self, val):
        try:
            self.listBox.Caption = val
        except AttributeError:
            self._listCaption = val


if __name__ == "__main__":
    from .application import dApp

    class DummyForm(ui.dForm):
        def onActivate(self, evt):
            self.Visible = False
            dlg = SortingForm(
                self,
                Caption="Fruit Sort",
                ListCaption="Which do you like best?",
                Choices=["apple", "pear", "banana", "peach", "strawberry", "lime"],
            )
            dlg.show()
            if dlg.Accepted:
                print("Sorted:", dlg.Choices)
            else:
                print("Cancel was pressed")
            dlg.release()
            ui.callAfter(self.release)

    app = dApp()
    app.MainFormClass = DummyForm
    app.start()
