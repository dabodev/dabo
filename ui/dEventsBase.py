from dabo.dLocalize import _

# These are the dabo-recognized events, that must get handled by the 
# individual ui libraries.
events = (
	("Activate", _("Occurs when the form becomes active.")),
	("Close", _("Occurs when the user closes the form.")),
	("Create", _("Occurs when the control or form is created.")),
	("Deactivate", _("Occurs when another form becomes active.")),
	("Destroy", _("Occurs when the control or form is destroyed.")),
	("Hit", _("Occurs with the control's default event (button click, listbox pick, checkbox, etc.)")),
	("ItemPicked", _("Occurs when an item was picked from a picklist.")),
	("GotFocus", _("Occurs when the control gets the focus.")),
	("KeyChar", _("Occurs when a key is depressed and released on the focused control or form.")),
	("KeyDown", _("Occurs when any key is depressed on the focused control or form.")),
	("KeyUp", _("Occurs when any key is released on the focused control or form.")),
	("LostFocus", _("Occurs when the control loses the focus.")),
	("MouseEnter", _("Occurs when the mouse pointer enters the form or control.")),
	("MouseLeave", _("Occurs when the mouse pointer leaves the form or control.")),
	("MouseLeftClick", _("Occurs when the mouse's left button is depressed and released on the control.")),
	("MouseLeftDoubleClick", _("Occurs when the mouse's left button is double-clicked on the control.")),
	("MouseRightClick", _("Occurs when the mouse mouse's right button is depressed and released on the control.")),
	("MouseLeftDown", _("Occurs when the mouse's left button is depressed on the control.")),
	("MouseLeftUp", _("Occurs when the mouse's left button is released on the control.")),
	("MouseRightDown", _("Occurs when the mouse's right button is depressed on the control.")),
	("MouseRightUp", _("Occurs when the mouse's right button is released on the control.")),
	("PageEnter", _("Occurs when the page becomes the active page.")),
	("PageLeave", _("Occurs when a different page becomes active.")),
	("RowNumChanged", _("Occurs when the form recognizes that the cursor's row number has changed.")),
	("ValueRefresh", _("Occurs when the form wants the controls to refresh their values.")),
	)
	
