# -*- coding: utf-8 -*-
import wx

from .. import application, events, settings, ui
from ..base_object import dObject
from ..lib.utils import ustr
from ..localization import _
from . import makeDynamicProperty

dabo_module = settings.get_dabo_package()


class dFont(dObject):
    """This class wraps the various font properties into a single object."""

    def __init__(self, properties=None, _nativeFont=None, *args, **kwargs):
        if _nativeFont is not None:
            self._nativeFont = _nativeFont
        else:
            self._nativeFont = wx.Font(
                settings.defaultFontSize,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
            )
        self._macNonScaledSize = 0

        super().__init__(properties=properties, *args, **kwargs)

    def _propsChanged(self):
        self.raiseEvent(events.FontPropertiesChanged)

    # Property definitions
    @property
    def Bold(self):
        """Bold setting for this font  (bool)"""
        if self._nativeFont:
            return self._nativeFont.GetWeight() == wx.FONTWEIGHT_BOLD
        return False

    @Bold.setter
    def Bold(self, val):
        if val:
            self._nativeFont.SetWeight(wx.FONTWEIGHT_BOLD)
        else:
            self._nativeFont.SetWeight(wx.FONTWEIGHT_NORMAL)
        self._propsChanged()

    @property
    def Description(self):
        """Read-only plain text description of the font  (str)"""
        ret = self.Face + " " + ustr(self.Size)
        if self.Bold:
            ret += " B"
        if self.Italic:
            ret += " I"
        return ret

    @property
    def Face(self):
        """Name of the font face  (str)"""
        if self._nativeFont:
            return self._nativeFont.GetFaceName()
        return ""

    @Face.setter
    def Face(self, val):
        if not val:
            return
        availableFonts = ui.getAvailableFonts()

        def trySetFont(val):
            if val in availableFonts:
                try:
                    return self._nativeFont.SetFaceName(val)
                except AttributeError:
                    return False
            return False

        if not trySetFont(val):
            # The font wasn't found on the user's system. Try to set it
            # automatically based on some common-case mappings.
            automatic_face = None
            lowVal = val.lower()
            if lowVal in ("courier", "courier new", "monospace", "mono"):
                for trial in ("Courier New", "Courier", "Monaco", "Monospace", "Mono"):
                    if trySetFont(trial):
                        automatic_face = trial
                        break
            elif lowVal in ("arial", "helvetica", "geneva", "sans"):
                for trial in ("Arial", "Helvetica", "Geneva", "Sans Serif", "Sans"):
                    if trySetFont(trial):
                        automatic_face = trial
                        break
            elif lowVal in ("times", "times new roman", "georgia", "serif"):
                for trial in ("Times New Roman", "Times", "Georgia", "Serif"):
                    if trySetFont(trial):
                        automatic_face = trial
                        break

            if not automatic_face:
                if not lowVal.startswith("ms shell dlg"):
                    # Ignore the non-existent MS Shell Dlg font names; they are Windows aliases
                    dabo_module.error(_("The font '%s' doesn't exist on this system.") % val)

        self._propsChanged()

    @property
    def Italic(self):
        """Italic setting for this font  (bool)"""
        if self._nativeFont:
            return self._nativeFont.GetStyle() == wx.FONTSTYLE_ITALIC
        return False

    @Italic.setter
    def Italic(self, val):
        if val:
            self._nativeFont.SetStyle(wx.FONTSTYLE_ITALIC)
        else:
            self._nativeFont.SetStyle(wx.FONTSTYLE_NORMAL)
        self._propsChanged()

    @property
    def Size(self):
        """Size in points for this font  (int)"""
        ret = None
        if self._useMacFontScaling():
            ret = self._macNonScaledSize
        if not ret:
            # Could be zero if it is the first time referenced when using Mac font scaling
            if self._nativeFont:
                ret = self._nativeFont.GetPointSize()
            else:
                # No native font yet; return a reasonable default.
                ret = 9
        return ret

    @Size.setter
    def Size(self, val):
        # Round to closest int
        val = round(val)
        if self._useMacFontScaling():
            self._macNonScaledSize = val
            val = round(val / 0.75)
        try:
            self._nativeFont.SetPointSize(val)
        except ValueError:
            dabo_module.error(_("Setting FontSize to %s failed") % val)
        self._propsChanged()

    def _useMacFontScaling(self):
        return wx.Platform == "__WXMAC__" and settings.macFontScaling

    @property
    def Underline(self):
        """Underline setting for this font  (bool)"""
        if self._nativeFont:
            return self._nativeFont.GetUnderlined()
        return False

    @Underline.setter
    def Underline(self, val):
        self._nativeFont.SetUnderlined(val)
        self._propsChanged()

    # Aliases for the various properties
    FontBold = Bold
    FontFace = Face
    FontItalic = Italic
    FontSize = Size
    FontUnderline = Underline


ui.dFont = dFont
