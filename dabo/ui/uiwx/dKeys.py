# -*- coding: utf-8 -*-
import wx
import dabo
from dabo.dLocalize import _

key_Alt = wx.WXK_ALT
try:
	# Versions < 2.8 don't have this
	key_Command = wx.WXK_COMMAND
except AttributeError:
	key_Command = None
key_Back = wx.WXK_BACK
key_Tab = wx.WXK_TAB
key_Return = wx.WXK_RETURN
key_Enter = wx.WXK_RETURN
key_Escape = wx.WXK_ESCAPE
key_Space = wx.WXK_SPACE
key_Delete = wx.WXK_DELETE
key_Start = wx.WXK_START
key_Lbutton = wx.WXK_LBUTTON
key_Rbutton = wx.WXK_RBUTTON
key_Cancel = wx.WXK_CANCEL
key_Mbutton = wx.WXK_MBUTTON
key_Clear = wx.WXK_CLEAR
key_Shift = wx.WXK_SHIFT
key_Control = wx.WXK_CONTROL
key_Menu = wx.WXK_MENU
key_Pause = wx.WXK_PAUSE
key_Capital = wx.WXK_CAPITAL
key_Prior = wx.WXK_PRIOR
key_Next = wx.WXK_NEXT
key_End = wx.WXK_END
key_Home = wx.WXK_HOME
# if wx.Platform == "__WXMAC__":
# 	key_Insert = 323
# 	key_Left = 28
# 	key_Up = 30
# 	key_Right = 29
# 	key_Down = 31
# else:
# 	key_Insert = wx.WXK_INSERT
# 	key_Left = wx.WXK_LEFT
# 	key_Up = wx.WXK_UP
# 	key_Right = wx.WXK_RIGHT
# 	key_Down = wx.WXK_DOWN
key_Insert = wx.WXK_INSERT
key_Left = wx.WXK_LEFT
key_Up = wx.WXK_UP
key_Right = wx.WXK_RIGHT
key_Down = wx.WXK_DOWN

key_Select = wx.WXK_SELECT
key_Print = wx.WXK_PRINT
key_Execute = wx.WXK_EXECUTE
key_Snapshot = wx.WXK_SNAPSHOT
key_Help = wx.WXK_HELP
key_Numpad0 = wx.WXK_NUMPAD0
key_Numpad1 = wx.WXK_NUMPAD1
key_Numpad2 = wx.WXK_NUMPAD2
key_Numpad3 = wx.WXK_NUMPAD3
key_Numpad4 = wx.WXK_NUMPAD4
key_Numpad5 = wx.WXK_NUMPAD5
key_Numpad6 = wx.WXK_NUMPAD6
key_Numpad7 = wx.WXK_NUMPAD7
key_Numpad8 = wx.WXK_NUMPAD8
key_Numpad9 = wx.WXK_NUMPAD9
key_Multiply = wx.WXK_MULTIPLY
key_Add = wx.WXK_ADD
key_Separator = wx.WXK_SEPARATOR
key_Subtract = wx.WXK_SUBTRACT
key_Decimal = wx.WXK_DECIMAL
key_Divide = wx.WXK_DIVIDE
key_F1 = wx.WXK_F1
key_F2 = wx.WXK_F2
key_F3 = wx.WXK_F3
key_F4 = wx.WXK_F4
key_F5 = wx.WXK_F5
key_F6 = wx.WXK_F6
key_F7 = wx.WXK_F7
key_F8 = wx.WXK_F8
key_F9 = wx.WXK_F9
key_F10 = wx.WXK_F10
key_F11 = wx.WXK_F11
key_F12 = wx.WXK_F12
key_F13 = wx.WXK_F13
key_F14 = wx.WXK_F14
key_F15 = wx.WXK_F15
key_F16 = wx.WXK_F16
key_F17 = wx.WXK_F17
key_F18 = wx.WXK_F18
key_F19 = wx.WXK_F19
key_F20 = wx.WXK_F20
key_F21 = wx.WXK_F21
key_F22 = wx.WXK_F22
key_F23 = wx.WXK_F23
key_F24 = wx.WXK_F24
key_Numlock = wx.WXK_NUMLOCK
key_Scroll = wx.WXK_SCROLL
key_Pageup = wx.WXK_PAGEUP
key_Pagedown = wx.WXK_PAGEDOWN
key_Numpad_space = wx.WXK_NUMPAD_SPACE
key_Numpad_tab = wx.WXK_NUMPAD_TAB
key_Numpad_enter = wx.WXK_NUMPAD_ENTER
key_Numpad_f1 = wx.WXK_NUMPAD_F1
key_Numpad_f2 = wx.WXK_NUMPAD_F2
key_Numpad_f3 = wx.WXK_NUMPAD_F3
key_Numpad_f4 = wx.WXK_NUMPAD_F4
key_Numpad_home = wx.WXK_NUMPAD_HOME
key_Numpad_left = wx.WXK_NUMPAD_LEFT
key_Numpad_up = wx.WXK_NUMPAD_UP
key_Numpad_right = wx.WXK_NUMPAD_RIGHT
key_Numpad_down = wx.WXK_NUMPAD_DOWN
key_Numpad_prior = wx.WXK_NUMPAD_PRIOR
key_Numpad_pageup = wx.WXK_NUMPAD_PAGEUP
key_Numpad_next = wx.WXK_NUMPAD_NEXT
key_Numpad_pagedown = wx.WXK_NUMPAD_PAGEDOWN
key_Numpad_end = wx.WXK_NUMPAD_END
key_Numpad_begin = wx.WXK_NUMPAD_BEGIN
key_Numpad_insert = wx.WXK_NUMPAD_INSERT
key_Numpad_delete = wx.WXK_NUMPAD_DELETE
key_Numpad_equal = wx.WXK_NUMPAD_EQUAL
key_Numpad_multiply = wx.WXK_NUMPAD_MULTIPLY
key_Numpad_add = wx.WXK_NUMPAD_ADD
key_Numpad_separator = wx.WXK_NUMPAD_SEPARATOR
key_Numpad_subtract = wx.WXK_NUMPAD_SUBTRACT
key_Numpad_decimal = wx.WXK_NUMPAD_DECIMAL
key_Numpad_divide = wx.WXK_NUMPAD_DIVIDE
key_Windows_left = wx.WXK_WINDOWS_LEFT
key_Windows_right = wx.WXK_WINDOWS_RIGHT
key_Windows_menu = wx.WXK_WINDOWS_MENU

mod_Alt = wx.ACCEL_ALT
mod_Shift = wx.ACCEL_SHIFT
mod_Ctrl = wx.ACCEL_CTRL
try:
	# Versions < 2.8 don't have this
	mod_Cmd = wx.ACCEL_CMD
except AttributeError:
	mod_Cmd = None
mod_Normal = wx.ACCEL_NORMAL

arrowKeys = {
		"up" : key_Up,
		"down" : key_Down,
		"left" : key_Left,
		"right" : key_Right
		}

numpadArrowKeys = {
		"numpad_up": key_Numpad_up,
		"numpad_down": key_Numpad_down,
		"numpad_left": key_Numpad_left,
		"numpad_right": key_Numpad_right,
		}

allArrowKeys = arrowKeys.copy()
allArrowKeys.update(numpadArrowKeys)

modifierStrings = {
	"alt": mod_Alt,
	"shift": mod_Shift,
	"ctrl": mod_Ctrl,
	"cmd": mod_Cmd,
}

arrows = (key_Up, key_Down, key_Left, key_Right)
whitespace = (key_Tab, key_Space, key_Numpad_space, key_Numpad_tab)

## pkm: I didn't include all the keycodes below - I want to see what is
##      actually necessary to add. Do we really need separate codes for
##      the '*' on the numpad versus the '*' on the keyboard, for instance.
##      Has anyone ever seen a keyboard in real life with a F24 key?
keyStrings = {
	"alt": key_Alt,
	"bksp": key_Back,
	"backspace": key_Back,
	"tab": key_Tab,
	"enter": key_Return,
	"return": key_Return,
	"esc": key_Escape,
	"escape": key_Escape,
	"space": key_Space,
	"delete": key_Delete,
	"start": key_Start,
	"clear": key_Clear,
	"shift": key_Shift,
	"ctrl": key_Control,
	"control": key_Control,
	"menu": key_Menu,
	"pause": key_Pause,
	"capslock": key_Capital,
	"pgup": key_Pageup,
	"pageup": key_Pageup,
	"pgdn": key_Pagedown,
	"pagedown": key_Pagedown,
	"end": key_End,
	"home": key_Home,
	"left": key_Left,
	"up": key_Up,
	"right": key_Right,
	"down": key_Down,
	"print": key_Print,
	"ins": key_Insert,
	"insert": key_Insert,
	"f1": key_F1,
	"f2": key_F2,
	"f3": key_F3,
	"f4": key_F4,
	"f5": key_F5,
	"f6": key_F6,
	"f7": key_F7,
	"f8": key_F8,
	"f9": key_F9,
	"f10": key_F10,
	"f11": key_F11,
	"f12": key_F12,
	"numlock": key_Numlock,
	"scroll": key_Scroll,
	"numpad_0": key_Numpad0,
	"numpad_1": key_Numpad1,
	"numpad_2": key_Numpad2,
	"numpad_3": key_Numpad3,
	"numpad_4": key_Numpad4,
	"numpad_5": key_Numpad5,
	"numpad_6": key_Numpad6,
	"numpad_7": key_Numpad7,
	"numpad_8": key_Numpad8,
	"numpad_9": key_Numpad9,
	"numpad_space": key_Numpad_space,
	"numpad_tab": key_Numpad_tab,
	"numpad_enter": key_Numpad_enter,
	"numpad_f1": key_Numpad_f1,
	"numpad_f2": key_Numpad_f2,
	"numpad_f3": key_Numpad_f3,
	"numpad_f4": key_Numpad_f4,
	"numpad_home": key_Numpad_home,
	"numpad_left": key_Numpad_left,
	"numpad_up": key_Numpad_up,
	"numpad_right": key_Numpad_right,
	"numpad_down": key_Numpad_down,
	"numpad_prior": key_Numpad_prior,
	"numpad_pageup": key_Numpad_pageup,
	"numpad_next": key_Numpad_next,
	"numpad_pagedown": key_Numpad_pagedown,
	"numpad_end": key_Numpad_end,
	"numpad_begin": key_Numpad_begin,
	"numpad_insert": key_Numpad_insert,
	"numpad_delete": key_Numpad_delete,
	"numpad_equal": key_Numpad_equal,
	"numpad_multiply": key_Numpad_multiply,
	"numpad_add": key_Numpad_add,
	"numpad_separator": key_Numpad_separator,
	"numpad_subtract": key_Numpad_subtract,
	"numpad_decimal": key_Numpad_decimal,
	"numpad_divide": key_Numpad_divide,
}


def resolveKeyCombo(keyCombo, returnFlags=False):
	"""
	When returnFlags is False (default), this takes a string representation
	of keys and modifiers, and returns a 2-tuple, containing the modifier(s)
	as the first element, and the key as the second.

	If returnFlags is True, a 3-tuple is returned, with the first two elements the
	same as above, but with a thrid element that is a numeric value compatible with
	what wxPython expects.
	"""
	if not isinstance(keyCombo, basestring) or not keyCombo.strip():
		raise ValueError(_("Invalid key combination: '%s'") % keyCombo)
	parts = keyCombo.split("+")
	if len(parts) == 1:
		# A single character
		key = parts[0]
		parts = []
	else:
		# Special case: handle the '+' key, which will create two empty elements at the end
		if parts[-2:] == ["", ""]:
			key = "+"
			parts = parts[:-2]
		else:
			key = parts[-1]
			parts = parts[:-1]
	# The modifier keys, if any, comprise all but the last key in keys
	mods = [p.lower() for p in parts]
	if returnFlags:
		# Convert the string mods and key into the correct parms for wx:
		flags = mod_Normal
		for mod in mods:
			flags = flags | modifierStrings[mod.lower()]
		return (mods, key, flags)
	else:
		return (mods, key)
