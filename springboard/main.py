#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")
import wx

def dummyImport():
	import dabo.db
	import dabo.biz
	import dabo.lib
	import dabo.ui
	import dabo.lib.autosuper
	import dabo.lib.datanav
	import dabo.lib.datanav2
	import dabo.ui.dialogs

	import wx
	import wx.build
	import wx.lib
	import wx.lib.mixins
	import wx.py
	import wx.tools
	import wx.calendar
	import wx.grid
	import wx.html
	import wx.wizard
	# import wx.activex
	import wx.gizmos
	import wx.glcanvas
	# import wx.iewin
	# import wx.ogl
	import wx.stc
	import wx.xrc
	
# 	import mx
# 	import mx.DateTime
	import xml
	import xml.dom
	import xml.dom.minidom
	
	import zlib
	# For PIL compatibility
# 	import PIL
# 	import Image
# 	import ArgImagePlugin
# 	import BmpImagePlugin
# 	import BufrStubImagePlugin
# 	import CurImagePlugin
# 	import DcxImagePlugin
# 	import EpsImagePlugin
# 	import FitsStubImagePlugin
# 	import FliImagePlugin
# 	import FpxImagePlugin
# 	import GbrImagePlugin
# 	import GifImagePlugin
# 	import GribStubImagePlugin
# 	import Hdf5StubImagePlugin
# 	import IcnsImagePlugin
# 	import IcoImagePlugin
# 	import ImImagePlugin
# 	import ImtImagePlugin
# 	import IptcImagePlugin
# 	import JpegImagePlugin
# 	import McIdasImagePlugin
# 	import MicImagePlugin
# 	import MpegImagePlugin
# 	import MspImagePlugin
# 	import PalmImagePlugin
# 	import PcdImagePlugin
# 	import PcxImagePlugin
# 	import PdfImagePlugin
# 	import PixarImagePlugin
# 	import PngImagePlugin
# 	import PpmImagePlugin
# 	import PsdImagePlugin
# 	import SgiImagePlugin
# 	import SpiderImagePlugin
# 	import SunImagePlugin
# 	import TgaImagePlugin
# 	import TiffImagePlugin
# 	import WmfImagePlugin
# 	import XVThumbImagePlugin
# 	import XbmImagePlugin
# 	import XpmImagePlugin



if __name__ == "__main__":
#	dummyImport()
	app = dabo.dApp()
	app.BasePrefKey = "dabo.springboard"
	app.MainFormClass = "springboard.cdxml"
	app.PreferenceManager.local_storage_dir = dabo.lib.utils.getUserAppDataDirectory()
	
	app.start()
