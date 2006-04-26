import wx, dabo
import os
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _
import dControlMixin as dcm
from dabo.ui import makeDynamicProperty


class dImage(wx.StaticBitmap, dcm.dControlMixin):
	""" Create a simple bitmap to display images."""
	def __init__(self, parent, properties=None, attProperties=None, 
			*args, **kwargs):
		self._baseClass = dImage
		preClass = wx.StaticBitmap

		self._picture = ""
		self._bmp = None
		self._bitmapHeight = None
		self._bitmapWidth = None
		self._scaleMode = "Proportional"
		self._imgProp = 1.0
		self._rotation = 0
		self.__image = None
		bmp = wx.EmptyBitmap(1, 1)
		picName = self._extractKey((kwargs, properties, attProperties), "Picture", "")
	
		dcm.dControlMixin.__init__(self, preClass, parent, properties, 
				bitmap=bmp, *args, **kwargs)
		
		# Display the picture, if any. This will also initialize the 
		# self._picture attribute
		self.Picture = picName
	
	
	def _initEvents(self):
		super(dImage, self)._initEvents()
		self.bindEvent(dEvents.Resize, self._onResize)
	
	
	def _onResize(self, evt):
		self._showPic()
	
	
	def rotateCounterClockwise(self):
		self._rotation -= 1
		if self._rotation == -4:
			self._rotation = 0
		self._showPic()
		
		
	def rotateClockwise(self):
		self._rotation += 1
		if self._rotation == 4:
			self._rotation = 0
		self._showPic()


	def _showPic(self):
		"""Displays the picture according to the ScaleMode and image size."""
		if not self._Image.Ok():
			# No image to display
				return

		img = self._Image.Copy()
		switchProportions = False
		if self._rotation:
			cw = (self._rotation > 0)
			absRotate = abs(self._rotation)
			switchProportions = (absRotate % 2 == 1)
			for xx in range(absRotate):
				img = img.Rotate90(cw)
			
		w, h = origW, origH = self.Width, self.Height
		if w == h == 1:
			# Initial empty bitmap, let the image determine the size
			w = origW = img.GetWidth()
			h = origH = img.GetHeight()
		w, h = float(w), float(h)
		
		if h == 0:
			szProp = 1
		else:
			szProp = w/h
		imgProp = self._imgProp
		
		if switchProportions:
			# The image has been rotated.
			imgProp = 1/imgProp
			
		sm = self.ScaleMode[0].lower()
		
		if self._Image.GetWidth() ==  self._Image.GetHeight() == 1:
			# Empty bitmap; no need to scale.
			img = img
		elif sm == "c":
			# Clip; Don't change anything
			img = img
		elif sm == "p":
			# Proportional; find the largest dimension that fits.
			if imgProp > szProp:
				# Image is wider than control, so limit it to the control width
				imgW = w
				imgH = w / imgProp
			else:
				# Use the height as the limiting size
				imgH = h
				imgW = h * imgProp
			img = img.Scale(imgW, imgH)
		else:
			# Stretch; just use the control size
			img = img.Scale(w, h)
		
		# We have the adjusted image; now generate the bitmap			
		self.Bitmap = img.ConvertToBitmap()
		self._bitmapHeight = self.Bitmap.GetHeight()
		self._bitmapWidth = self.Bitmap.GetWidth()
		
		try:
			self.SetBitmap(self.Bitmap)
		except TypeError, e: pass
		self.SetSize((origW, origH))


	# Property definitions
	def _getBmp(self):
		if self._bmp is None:
			self._bmp = wx.EmptyBitmap(1, 1, 1)
		return self._bmp
		
	def _setBmp(self, val):
		self._bmp = val
		
		
	def _getBitmapHeight(self):
		return self._bitmapHeight


	def _getBitmapWidth(self):
		return self._bitmapWidth


	def _getPic(self):
		return self._picture
		
	def _setPic(self, val):
		if isinstance(val, wx.Image):
			# An image stored as a stream is being used
			self.__image = val
			self._picture = "(stream)"
		else:
			# Don't allow built-in graphics to be displayed here
			if not os.path.exists(val):
				if val:
					# They passed a non-existent image file
					raise IOError, "No file named '%s' exists." % val
				else:
					# Empty string passed; clear any current image
					self._picture = ""
					self._rotation = 0
					self._bmp = wx.EmptyBitmap(1, 1, 1)
					self.__image = self._bmp.ConvertToImage()
					self._showPic()
					return
			self._picture = val
			self._rotation = 0
			self._Image.LoadFile(val)
		self._imgProp = float(self._Image.GetWidth()) / float(self._Image.GetHeight())
		self._showPic()
		
	
	def _getScaleMode(self):
		return self._scaleMode
		
	def _setScaleMode(self, val):
		"""Only the first letter is significant. """
		initial = val[0].lower()
		modes = {"c" : "Clip", "p" : "Proportional", "s" : "Stretch"}
		try:
			self._scaleMode = modes[initial]
			self._showPic()
		except KeyError:
			dabo.errorLog.write(_("ScaleMode must be either 'Clip', 'Proportional' or 'Stretch'.") )


	def _getImg(self):
		if self.__image is None:
			self.__image = wx.NullImage
		return self.__image

	
	Bitmap = property(_getBmp, _setBmp, None,
			_("The bitmap representation of the displayed image.  (wx.Bitmap)") )
	DynamicBitmap = makeDynamicProperty(Bitmap)

	BitmapHeight = property(_getBitmapHeight, None, None,
			_("Height of the actual displayed bitmap  (int)"))
	
	BitmapWidth = property(_getBitmapWidth, None, None,
			_("Width of the actual displayed bitmap  (int)"))
	
	Picture = property(_getPic, _setPic, None,
			_("The file used as the source for the displayed image.  (str)") )
	DynamicPicture = makeDynamicProperty(Picture)
			
	ScaleMode = property(_getScaleMode, _setScaleMode, None,
			_("""Determines how the image responds to sizing. Can be one
			of the following:
				Clip: Only that part of the image that fits in the control's size is displayed
				Proportional: the image resizes to fit the control without changing
					its original proportions. (default)
				Stretch: the image resizes to the Height/Width of the control.
			""") )
	DynamicScaleMode = makeDynamicProperty(ScaleMode)

	_Image = property(_getImg, None, None, 
			_("Underlying image handler object  (wx.Image)") )

	
if __name__ == "__main__":
	class ImgForm(dabo.ui.dForm):
		def afterInit(self):
			self.Caption = "dImage Demonstration"
			# Sliders work differently on OS X
			### egl - This has been fixed in more recent versions of wxPython
			# self.reverseVert = (wx.PlatformInfo[0] == "__WXMAC__")
			self.reverseVert = False
			# Create a panel with horiz. and vert.  sliders
			self.imgPanel = dabo.ui.dPanel(self)
			self.VSlider = dabo.ui.dSlider(self, Orientation="V", Min=1, Max=100)
			self.HSlider = dabo.ui.dSlider(self, Orientation="H", Min=1, Max=100)
			if self.reverseVert:
				self.VSlider.Value = 0
			else:
				self.VSlider.Value = 100
			self.HSlider.Value = 100
			self.VSlider.bindEvent(dEvents.Hit, self.onSlider)
			self.HSlider.bindEvent(dEvents.Hit, self.onSlider)
			
			psz = self.imgPanel.Sizer = dabo.ui.dSizer("V")
			hsz = dabo.ui.dSizer("H")
			hsz.append(self.imgPanel, 1, "x")
			hsz.appendSpacer(10)
			hsz.append(self.VSlider, 0, "x")
			self.Sizer.DefaultBorder = 25
			self.Sizer.DefaultBorderLeft = self.Sizer.DefaultBorderRight = 25
			self.Sizer.appendSpacer(25)
			self.Sizer.append(hsz, 1, "x")
			self.Sizer.appendSpacer(10)
			self.Sizer.append(self.HSlider, 0, "x")
			self.Sizer.appendSpacer(10)

			hsz = dabo.ui.dSizer("H")
			hsz.DefaultSpacing = 10
			dabo.ui.dBitmapButton(self, RegID="btnRotateCW",
					Picture="rotateCW")
			dabo.ui.dBitmapButton(self, RegID="btnRotateCCW",
					Picture="rotateCCW")
			hsz.append(self.btnRotateCW)
			hsz.append(self.btnRotateCCW)			
			self.ddScale = dabo.ui.dDropdownList(self, 
					Choices=["Proportional", "Stretch", "Clip"],
					DataSource = "self.Form.img",
					DataField = "ScaleMode")
			self.ddScale.PositionValue = 0
			btn = dabo.ui.dButton(self, Caption="Load Image")
			btn.bindEvent(dEvents.Hit, self.onLoadImage)
			btnOK = dabo.ui.dButton(self, Caption="Done")
			btnOK.bindEvent(dEvents.Hit, self.close)
			hsz.append(self.ddScale, 0, "x")
			hsz.append(btn, 0, "x")
			hsz.append(btnOK, 0, "x")
			self.Sizer.append(hsz, 0, alignment="right")
			self.Sizer.appendSpacer(25)
			
			# Create the image control
			self.img = dImage(self.imgPanel)
			
			# Make sure that resizing the form updates the image
			self.bindEvent(dEvents.Resize, self.onResize)
			# Since lots of resize events fire when the window is
			# dragged, only do the updates on Idle
			self.bindEvent(dEvents.Idle, self.onIdle)
			# Set the idle update flage
			self.needUpdate = False


		def onHit_btnRotateCW(self, evt):
			self.img.rotateClockwise()


		def onHit_btnRotateCCW(self, evt):
			self.img.rotateCounterClockwise()


		def onSlider(self, evt):
			# Vertical sliders have their low value on the bottom on OSX;
			# on MSW and GTK, the low value is at the top
			val = evt.EventObject.Value * 0.01
			dir = evt.EventObject.Orientation[0].lower()
			if dir == "h":
				# Change the width of the image
				self.img.Width = (self.imgPanel.Width * val)
			else:
				if self.reverseVert:
					val = 1.01 - val
				self.img.Height = (self.imgPanel.Height * val)
			
			
		def onLoadImage(self, evt): 
			f = dabo.ui.getFile("jpg", "png", "gif", "bmp", "*")
			if f:
				self.img.Picture = f
			# Prevent occasional double-events on Windows
			evt.stop()
		
		
		def onResize(self, evt):
			self.needUpdate = True
			
		
		def onIdle(self, evt):
			if self.needUpdate:
				self.needUpdate = False
				wd = self.HSlider.Value * 0.01 * self.imgPanel.Width
				if self.reverseVert:
					ht = (101 - self.VSlider.Value) * 0.01 * self.imgPanel.Height
				else:
					ht = self.VSlider.Value * 0.01 * self.imgPanel.Height
				self.img.Size = (wd, ht)
						

	app = dabo.dApp()
	app.MainFormClass = ImgForm
	app.start()
	
