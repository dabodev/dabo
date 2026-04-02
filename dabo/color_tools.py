# -*- coding: utf-8 -*-
import random
import re

import wx.lib.colourdb as wcd

from dabo import application
from dabo import ui


class HexError(Exception):
    pass


class InvalidCharError(HexError):
    pass


class TypeError(HexError):
    pass


class ColorTupleError(Exception):
    pass


class RgbValueError(ColorTupleError):
    pass


class LengthError(ColorTupleError):
    pass


class IntegerTypeError(ColorTupleError):
    pass


# wxPython stores color names in uppercase. Ugly, IMO.
colorDict = {itm[0].lower(): itm[1:] for itm in wcd.getColourInfoList() if " " not in itm[0]}
# Spelling differences
grays = {key.replace("grey", "gray"): val for key, val in colorDict.items() if "grey" in key}
colorDict.update(grays)
colors = list(colorDict.keys())
colors.sort()


def hexToDec(hx):
    if not isinstance(hx, str):
        raise TypeError("Input must be a string")
    # Define a dict of char-value pairs
    hex = {
        "0": 0,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "A": 10,
        "B": 11,
        "C": 12,
        "D": 13,
        "E": 14,
        "F": 15,
    }
    # Reverse it, and force upper case
    rev = hx[::-1].upper()
    ret = 0
    pos = 1
    for c in rev:
        if hex.get(c) == None:
            raise InvalidCharError(f"{c} is an invalid hex character")
        ret += hex[c] * pos
        pos = pos * 16
    return ret


def tupleToHex(t, includeHash=True):
    """Convert a color tuple into an HTML hex format."""
    if not len(t) == 3:
        raise LengthError("Color tuple needs to contain 3 elements")
    for rgb in t:
        if not isinstance(rgb, int):
            raise IntegerTypeError("Tuple elements should be all integers.")
        if not 0 <= rgb <= 255:
            raise RgbValueError("Rgb Value must be in the range 0-255")
    rx, gx, bx = hex(t[0]), hex(t[1]), hex(t[2])
    # Each is in the format '0x00'.
    r = rx[2:].upper()
    g = gx[2:].upper()
    b = bx[2:].upper()
    if len(r) == 1:
        r = "0" + r
    if len(g) == 1:
        g = "0" + g
    if len(b) == 1:
        b = "0" + b
    ret = ""
    if includeHash:
        ret = "#"
    ret += r + g + b
    return ret


def colorTupleFromHex(hx):
    # Strip the pound sign, if any
    hx = hx.replace("#", "")
    hx = hx.lstrip("0")
    if len(hx) < 6:
        hx = "0" * (6 - len(hx)) + hx
    red = hexToDec(hx[:2])
    green = hexToDec(hx[2:4])
    blue = hexToDec(hx[4:])
    return (red, green, blue)


def colorTupleFromName(color):
    """Given a color name, such as "Blue" or "Aquamarine", return a color tuple.

    This is used internally in the ForeColor and BackColor property setters. The
    color name is not case-sensitive. If the color name doesn't exist, an exception
    is raised.
    """
    ret = None
    try:
        ret = colorDict[color.lower().strip()]
    except KeyError:
        try:
            ret = colorTupleFromHex(color)
        except InvalidCharError:
            ret = colorTupleFromString(color)
    return ret


def colorTupleFromString(color):
    ret = None
    colorTuplePat = r"\((\d+), *(\d+), *(\d+)\)"
    mtch = re.match(colorTuplePat, color)
    if mtch:
        grps = mtch.groups()
        ret = (int(grps[0]), int(grps[1]), int(grps[2]))
        for val in ret:
            if not 0 <= val <= 255:
                raise KeyError("Color tuple integer must range from 0-255")
    else:
        raise KeyError(f"Color '{color}' is not defined.")
    return ret


def randomColor():
    """Returns a random color tuple"""
    return colorDict[random.choice(list(colorDict.keys()))]


def randomColorName():
    """Returns a random color name"""
    return random.choice(list(colorDict.keys()))


def colorNameFromTuple(colorTuple, firstOnly=False):
    """Returns a list of color names, if any, whose RGB tuple matches
    the specified tuple. If 'firstOnly' is True, then a single color name
    will be returned as a string, not a list; the string will be empty
    if there is no match.
    """
    ret = [nm for nm, tup in list(colorDict.items()) if tup == colorTuple]
    if firstOnly:
        try:
            ret = ret[0]
        except IndexError:
            ret = ""
    return ret


def text_color_on_background(r, g, b):
    """
    Determines if white or black text would look best against a given background.

    When displaying text on a colored background, it needs to be visible. This function takes the
    background color's RGB values, and returns 'white' or 'black', depending on the background's
    luminance (lightness).
    """
    # Calculate relative luminance
    luminance = (0.299 * r) + (0.587 * g) + (0.114 * b)
    # Choose black for lighter backgrounds, white for darker ones
    return "black" if luminance > 128 else "white"


if __name__ == "__main__":

    class ColorForm(ui.dForm):
        def afterInit(self):
            self.Caption = "Colors"
            bp = self.back_panel = ui.dScrollPanel(self)
            self.Sizer.append1x(bp)
            vsz = bp.Sizer = ui.dSizerV()
            vsz.appendSpacer(16)
            lbl = ui.dLabel(bp, Caption="Filter:")
            txt = self.filter_text = ui.dTextBox(bp, OnHit=self.filter)
            hsz = ui.dSizerH()
            hsz.append(lbl, border=2, alignment="right")
            hsz.append1x(txt, border=2)
            vsz.append(hsz, alignment="center")

            gsz = self.color_grid_sizer = ui.dGridSizer(MaxCols=6)
            self.color_panels = []
            panel_height = 80
            label_bottom = panel_height - 5
            for name, rgb in colorDict.items():
                p = ui.dPanel(
                    bp, Name=name, BackColor=name, Height=panel_height, BorderWidth=1, RegID=name
                )
                self.color_panels.append(p)
                ui.dLabel(
                    p,
                    Caption=name,
                    ForeColor=text_color_on_background(*rgb),
                    Left=2,
                    Bottom=label_bottom,
                )
                gsz.append(p, layout="x")
            gsz.setColExpand(True, "all", proportion=1)
            vsz.append1x(gsz, border=20)
            self.layout()

        def color_choice(self, evt):
            color = evt.EventObject.StringValue
            self.color_sample.BackColor = color

        def filter(self, evt):
            filter_val = evt.EventObject.Value
            [self.color_grid_sizer.remove(p) for p in self.color_panels]
            with self.lockDisplay():
                for pnl in self.color_panels:
                    vis = filter_val.lower() in pnl.RegID
                    pnl.Visible = vis
                    if vis:
                        self.color_grid_sizer.append(pnl, layout="x")
            self.layout()

    app = application.dApp()
    app.MainFormClass = ColorForm
    app.start()
