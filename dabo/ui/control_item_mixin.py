# -*- coding: utf-8 -*-
import wx

from dabo.debugging import logPoint

from .. import ui
from ..lib.propertyHelperMixin import _DynamicList
from ..lib.utils import ustr
from ..localization import _
from . import dDataControlMixin
from . import makeDynamicProperty


class dControlItemMixin(dDataControlMixin):
    """
    This mixin class factors out the common code among all of the
    controls that contain lists of items.
    """

    def __init__(self, *args, **kwargs):
        self._keys = []
        self._invertedKeys = []
        self._valueMode = "s"
        self._sorted = False
        self._sortFunction = None
        if not kwargs.get("PositionValue"):
            kwargs["PositionValue"] = 0
        super().__init__(*args, **kwargs)

    def _initEvents(self):
        super()._initEvents()

    def _onWxHit(self, evt):
        self._userChanged = True
        # Flush value on every hit:
        self.flushValue()
        super()._onWxHit(evt)
        # Since super method set this attribute again, we must reset it.
        self._userChanged = False

    def appendItem(self, txt, select=False):
        """Adds a new item to the end of the list"""
        chc = self._choices
        chc.append(txt)
        self.Choices = chc
        if select:
            if self._isMultiSelect():
                self.StringValue += (txt,)
            else:
                self.StringValue = txt

    def insertItem(self, pos, txt, select=False):
        """Inserts a new item into the specified position."""
        chc = self._choices[:pos]
        chc.append(txt)
        chc += self._choices[pos:]
        self.Choices = chc
        if select:
            self.StringValue = txt

    def removeItem(self, pos):
        """Removes the item at the specified position."""
        del self._choices[pos]
        self.Delete(pos)

    def removeAll(self):
        """Removes all entries from the control."""
        self._choices = []
        self.Clear()

    def clearSelections(self):
        """
        Stub method. Only used in the list box, where there
        can be multiple selections.
        """
        pass

    def setSelection(self, index):
        """Same as setting property PositionValue."""
        self.PositionValue = index

    def _setSelection(self, index):
        """Backend UI wrapper."""
        if self.Count > index:
            self.SetSelection(index)
        else:
            ## pkm: The user probably set the Value property from inside initProperties(),
            ##      and it is getting set before the Choice property has been applied.
            ##      If this is the case, callAfter is the ticket.
            ui.callAfter(self.SetSelection, index)

    def _isMultiSelect(self):
        """Return whether this control has multiple-selectable items."""
        try:
            ms = self.MultipleSelect
        except AttributeError:
            ms = False
        return ms

    def sort(self, sortFunction=None):
        """
        Sorts the list items. By default, the standard Python sorting is
        used, but this can be overridden with a custom sortFunction.
        """
        if sortFunction is None:
            sortFunction = self._sortFunction
        self._choices.sort(sortFunction)

    def _resetChoices(self):
        """
        Sequence required to update the choices for the list. Refactored out
        to avoid duplicate code.
        """
        self.Clear()
        self._setSelection(-1)
        if self._sorted:
            self.sort()
        self.AppendItems(self._choices)

    # Property definitions:
    @property
    def Choices(self):
        """
        Specifies the string choices to display in the list. Returns a list of strings. Read-write
        at runtime. The list index becomes the PositionValue, and the string becomes the
        StringValue.
        """
        try:
            _choices = self._choices
        except AttributeError:
            _choices = self._choices = []
        return _DynamicList(_choices, self)

    @Choices.setter
    def Choices(self, choices):
        if self._constructed():
            self.lockDisplay()
            vm = self.ValueMode
            oldVal = self.Value
            self._choices = list(choices)
            self._resetChoices()
            if oldVal is not None:
                # Try to get back to the same row:
                try:
                    self.Value = oldVal
                except ValueError:
                    if self._choices:
                        self.PositionValue = 0
            else:
                self.PositionValue = 0 if self._choices else -1
            self.unlockDisplay()
        else:
            self._properties["Choices"] = choices

    @property
    def Count(self):
        """Number of items in the control. Read-only.  (int)"""
        return self.GetCount()

    @property
    def Keys(self):
        """
        Specifies a mapping between arbitrary values and item positions.  Read-write at runtime.
        (dict)

        The Keys property is a dictionary, where each key resolves into a list index (position). If
        using keys, you should update the Keys property whenever you update the Choices property, to
        make sure they are in sync. Optionally, Keys can be a list/tuple that is a 1:1 mapping of
        the Choices property. So if your 3rd Choices entry is selected, KeyValue will return the 3rd
        entry in the Keys property.
        """
        try:
            keys = self._keys
        except AttributeError:
            keys = self._keys = {}
        return keys

    @Keys.setter
    def Keys(self, val):
        if isinstance(val, dict):
            self._keys = val
            # What about duplicate values?
            self._invertedKeys = dict((v, k) for k, v in val.items())
        elif isinstance(val, (list, tuple)):
            self._keys = val
            self._invertedKeys = None
        else:
            raise TypeError(_("Keys must be a dictionary or list/tuple."))

    @property
    def KeyValue(self):
        """Specifies the key value or values of the selected item or items. Read-write at runtime.

        Returns the key value or values of the selected item(s), or selects the item(s) with the
        specified KeyValue(s). An exception will be raised if the Keys property hasn't been set up
        to accomodate.
        """
        selections = self.PositionValue
        values = []
        if not self._isMultiSelect():
            if selections is None:
                return None
            else:
                selections = (selections,)
        for selection in selections:
            if selection < 0:
                # This is returned by the control to indicate no selection
                continue
            if isinstance(self.Keys, (list, tuple)):
                try:
                    values.append(self.Keys[selection])
                except IndexError:
                    values.append(None)
            else:
                try:
                    values.append(self._invertedKeys[selection])
                except KeyError:
                    values.append(None)

        if not self._isMultiSelect():
            if len(values) > 0:
                return values[0]
            else:
                return None
        else:
            return tuple(values)

    @KeyValue.setter
    def KeyValue(self, value):
        if self._constructed():
            # This function takes a key value or values, such as 10992 or
            # (10992, 92991), finds the mapped position or positions, and
            # and selects that position or positions.

            # convert singular to tuple:
            if not isinstance(value, (list, tuple)):
                value = (value,)

            # Clear all current selections:
            self.clearSelections()

            invalidSelections = []
            # Select items that match indices in value:
            for key in value:
                if isinstance(self.Keys, dict):
                    try:
                        self.setSelection(self.Keys[key])
                    except KeyError:
                        invalidSelections.append(key)
                else:
                    try:
                        self.setSelection(self.Keys.index(key))
                    except ValueError:
                        invalidSelections.append(key)

            # pkm: getBlankValue() returns None, so if there isn't a Key for None (the default) the
            # update cycle will result in the ValueError, which isn't friendly default behavior. So
            # I'm making it so that None values in *any* dControlItem class will be allowed. We can
            # discuss whether we should expose a property to control this behavior or not.
            if len(value) == 0 or invalidSelections == [None]:
                # Value being set to an empty tuple, list, or dict, or to None in a Multi-Select
                # control, which means "nothing is selected":
                self._resetChoices()
                invalidSelections = []

            if invalidSelections:
                snm = self.Name
                dataSource = self.DataSource
                dataField = self.DataField
                raise ValueError(
                    _(
                        f"Trying to set {sn}m.Value (DataSource: '{dataSource}', DataField: "
                        f"'{dataField}') to these invalid selections: {invalidSelections}"
                    )
                )

        else:
            self._properties["KeyValue"] = value

    @property
    def PositionValue(self):
        """
        Specifies the position (index) of the selected item(s). (int or tuple(int)) Read-write at
        runtime. Returns the current position(s), or sets the current position(s).
        """
        if hasattr(self, "SelectedIndices"):
            ret = tuple(self.SelectedIndices)
            if not self._isMultiSelect():
                # Only return a single index
                ret = ret[0]
        else:
            if not self._isMultiSelect():
                ret = self.GetSelection()
            else:
                selections = self.GetSelections()
                ret = tuple(selections)
        return ret

    @PositionValue.setter
    def PositionValue(self, value):
        if self._constructed():
            # convert singular to tuple:
            if not isinstance(value, (list, tuple)):
                value = (value,)
            # Clear all current selections:
            self.clearSelections()
            # Select items that match indices in value:
            for index in value:
                if index is None:
                    continue
                try:
                    self._setSelection(index)
                except IndexError:
                    pass
            self._afterValueChanged()
        else:
            self._properties["PositionValue"] = value

    @property
    def Sorted(self):
        """
        Are the items in the control automatically sorted? Default=False. If True, whenever the
        Choices property is changed, the resulting list will be first sorted using the SortFunction
        property, which defaults to None, giving a default sort order.  (bool)
        """
        return self._sorted

    @Sorted.setter
    def Sorted(self, val):
        if self._constructed():
            if self._sorted != val:
                self._sorted = val
                if val:
                    # Force a re-ordering
                    self.sort()
        else:
            self._properties["Sorted"] = val

    @property
    def SortFunction(self):
        """
        Function used to sort list items when Sorted=True. Default=None, which gives the default
        sorting  (callable or None)
        """
        return self._sortFunction

    @SortFunction.setter
    def SortFunction(self, val):
        if self._constructed():
            if callable(val):
                self._sortFunction = val
                if not isinstance(self, ui.dListControl):
                    # Force a re-ordering
                    self.sort()
            else:
                raise TypeError(_("SortFunction must be callable"))
        else:
            self._properties["SortFunction"] = val

    @property
    def StringValue(self):
        """
        Specifies the text of the selected item. (str or tuple(str))

        Returns the text of the selected item(s), or selects the item(s) with the specified text. An
        exception is raised if there is no position with matching text.
        """
        selections = self.PositionValue
        if not self._isMultiSelect():
            if selections is None:
                return None
            else:
                selections = (selections,)
        strings = []
        for index in selections:
            if (index < 0) or (index > (self.Count - 1)):
                continue
            try:
                strings.append(self.GetString(index))
            except AttributeError:
                # If this is a list control, there is no native GetString.
                # Use the Dabo-supplied replacement
                try:
                    strings.append(self._GetString(index))
                except IndexError:
                    # Invalid index; usually an empty list
                    pass
        if not self._isMultiSelect():
            # convert to singular
            if len(strings) > 0:
                return strings[0]
            else:
                return None
        else:
            return tuple(strings)

    @StringValue.setter
    def StringValue(self, value):
        if self._constructed():
            # convert singular to tuple:
            if not isinstance(value, (list, tuple)):
                value = (value,)
            # Clear all current selections:
            self.clearSelections()
            # Select items that match the string tuple:
            for str_val in value:
                if str_val is None:
                    continue
                if isinstance(str_val, str):
                    index = self.FindString(str_val)
                    if index < 0:
                        raise ValueError(_(f"str_val must be present in the choices: 'str_val'"))
                    else:
                        self.setSelection(index)
                else:
                    raise TypeError(_("String required."))
            self._afterValueChanged()
        else:
            self._properties["StringValue"] = value

    @property
    def Value(self):
        """
        Specifies which item is currently selected in the list. Read-write at runtime.

        Value refers to one of the following, depending on the setting of ValueMode:

            + ValueMode="Position" : the index of the selected item(s) (integer)
            + ValueMode="String"   : the displayed string of the selected item(s) (string)
            + ValueMode="Key"      : the key of the selected item(s) (can vary)
        """
        if self.ValueMode == "position":
            ret = self.PositionValue
        elif self.ValueMode == "key":
            ret = self.KeyValue
        else:
            ret = self.StringValue
        return ret

    @Value.setter
    def Value(self, value):
        if self.ValueMode == "position":
            self.PositionValue = value
        elif self.ValueMode == "key":
            self.KeyValue = value
        else:
            self.StringValue = value

    @property
    def ValueMode(self):
        """
        Specifies the information that the Value property refers to. (str) Read-write at runtime.

        =========== =========================
        'Position'  Value refers to the position in the choices (integer).
        'String'    Value refers to the displayed string for the selection (default) (string).
        'Key'       Value refers to a separate key, set using the Keys property (can vary).
        =========== =========================

        """
        try:
            vm = {"p": "position", "s": "string", "k": "key"}[self._valueMode]
        except AttributeError:
            vm = self._valueMode = "string"
        return vm

    @ValueMode.setter
    def ValueMode(self, val):
        val = ustr(val).lower()[0]
        if val in ("p", "s", "k"):
            self._valueMode = val

    DynamicKeyValue = makeDynamicProperty(KeyValue)
    DynamicPositionValue = makeDynamicProperty(PositionValue)
    DynamicStringValue = makeDynamicProperty(StringValue)
    DynamicValue = makeDynamicProperty(Value)
    DynamicValueMode = makeDynamicProperty(ValueMode)


ui.dControlItemMixin = dControlItemMixin
