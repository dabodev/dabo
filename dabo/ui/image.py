#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import imghdr
import io
import os

import filetype
import wx

from .. import events
from .. import settings
from .. import ui
from ..lib import utils
from ..localization import _
from . import dDataControlMixin
from . import dForm
from . import dImageMixin
from . import makeDynamicProperty

# See if PIL is installed
_USE_PIL = True
try:
    from PIL import Image
except ImportError:
    _USE_PIL = False
## The tag number is a constant, so no need to calculate it each time.
# from PIL.ExifTags import TAGS
# _ORIENTATION_TAG = [tagnum for tagnum, tagname in TAGS.items()
#        if tagname == "Orientation"][0]
_ORIENTATION_TAG = 274

dabo_module = settings.get_dabo_package()


# The EXIF rotation values do not lend themselves easily to rotation
# calculation, so I've defined my own for this class. These next two
# functions convert between the two.
def _imgToExif(imgState):
    return {1: 1, 2: 6, 3: 3, 4: 8, 5: 2, 6: 5, 7: 4, 8: 7}[imgState]


def _exifToImg(orientation):
    return {1: 1, 6: 2, 3: 3, 8: 4, 2: 5, 5: 6, 4: 7, 7: 8}[orientation]


class dImage(dDataControlMixin, dImageMixin, wx.StaticBitmap):
    """Create a simple bitmap to display images."""

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dImage
        preClass = wx.StaticBitmap

        self._scaleMode = "Proportional"
        self._imgProp = 1.0
        # Images can be dsiplayed in one of 8 combinations of rotation and mirror
        # State   Rotation   Mirrored?
        #   1           0      False
        #   2          90      False
        #   3         180      False
        #   4         270      False
        #   5           0      True
        #   6          90      True
        #   7         180      True
        #   8         270      True
        self._displayState = 1
        # These describe how to go from one state to the other when flipping
        self._vFlipTrans = {1: 7, 2: 6, 3: 5, 4: 8, 5: 3, 6: 2, 7: 1, 8: 4}
        self._hFlipTrans = {1: 5, 2: 8, 3: 7, 4: 6, 5: 1, 6: 4, 7: 3, 8: 2}
        self._imageData = self.__image = None
        self._inReload = self._inShowPic = False
        picName = self._extractKey((kwargs, properties, attProperties), "Picture", "")
        self._pictureIndex = self._extractKey(
            (kwargs, properties, attProperties), "PictureIndex", -1
        )

        dImageMixin.__init__(self)
        dDataControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            bitmap=wx.Bitmap(1, 1),
            *args,
            **kwargs,
        )

        # Display the picture, if any. This will also initialize the
        # self._picture attribute
        self.Picture = picName

    def _initEvents(self):
        super()._initEvents()
        self.bindEvent(events.Resize, self._onResize)

    def _onResize(self, evt):
        if not self._inShowPic:
            self._showPic()

    def update(self):
        ui.callAfterInterval(100, super().update)

    def _calcNewRotation(self, amt):
        ds = self._displayState
        mirrored = ds > 4
        if mirrored:
            ds -= 4
        rot = ds + amt
        if rot > 4:
            rot -= 4
        elif rot < 1:
            rot += 4
        if mirrored:
            rot += 4
        self._displayState = rot
        self._showPic()

    def rotateCounterClockwise(self):
        self._calcNewRotation(-1)

    def rotateClockwise(self):
        self._calcNewRotation(+1)

    def flipVertically(self):
        self._displayState = self._vFlipTrans[self._displayState]
        self._showPic()

    def flipHorizontally(self):
        self._displayState = self._hFlipTrans[self._displayState]
        self._showPic()

    def getImgType(self):
        data = self._imageData
        ret = (None, None)
        if data:
            ret = None
            fname = self.Application.getTempFile(ext="")
            open(fname, "wb").write(data)
            aux = wx.NullImage
            hnds = aux.GetHandlers()
            for hnd in hnds:
                aux.RemoveHandler(hnd.GetName())
            for hnd in hnds:
                try:
                    if hnd.LoadFile(fname):
                        ret = (hnd.GetName(), hnd.GetExtension())
                        break
                except Exception as e:
                    print("ERROR", e)
        return ret

    def getOriginalImgSize(self):
        """
        Since the image can be scaled, this returns the size of
        the unscaled image.
        """
        img = self._Image
        return (img.GetWidth(), img.GetHeight())

    def _showPic(self):
        """Displays the picture according to the ScaleMode and image size, as
        well as any applied rotation and/or mirroring.
        """
        if self._inShowPic:
            return
        if not self._Image.IsOk():
            # No image to display
            self.Bitmap = wx.Bitmap(1, 1)
            self.Freeze()
            self.SetBitmap(self.Bitmap)
            self.Thaw()
            return

        self._inShowPic = True
        img = self._Image.Copy()

        ds = self._displayState
        switchProportions = (ds % 2) == 0
        mirrored = ds > 4
        rotCount = (ds - 1) % 4
        if mirrored:
            img = img.Mirror()
        for rot in range(rotCount):
            img = img.Rotate90(True)

        w, h = origW, origH = self.Width, self.Height
        if w <= 1 or h < 1:
            # Initial empty bitmap, let the image determine the size
            w = origW = img.GetWidth()
            h = origH = img.GetHeight()
        w, h = float(w), float(h)

        if h == 0:
            szProp = 1
        else:
            szProp = w / h
        imgProp = self._imgProp

        if switchProportions:
            # The image has been rotated.
            imgProp = 1 / imgProp

        sm = self.ScaleMode[0].lower()

        if self._Image.GetWidth() == self._Image.GetHeight() == 1:
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
            img = img.Scale(int(imgW), int(imgH))
        else:
            # Stretch; just use the control size
            img = img.Scale(int(w), int(h))

        # We have the adjusted image; now generate the bitmap
        self.Bitmap = img.ConvertToBitmap()
        self._bitmapHeight = self.Bitmap.GetHeight()
        self._bitmapWidth = self.Bitmap.GetWidth()

        self.Freeze()
        try:
            self.SetBitmap(self.Bitmap)
        except TypeError as e:
            pass
        self.Thaw()
        self.SetSize((origW, origH))
        self._inShowPic = False

    # Property definitions
    @property
    def FrameCount(self):
        """
        Number of frames in the current image. Will be 1 for most images, but can be greater for
        animated GIFs, ICOs and some TIFF files. (read-only) (int)
        """
        if not self.Picture:
            return 0
        typ = os.path.splitext(self.Picture)[1].replace(".", "")
        if filetype.guess(self.Picture).extension in ("gif",):
            anim = wx.animate.Animation(self.Picture)
            cnt = anim.GetFrameCount()
        else:
            cnt = self.__image.GetImageCount(self.Picture)
        return cnt

    @property
    def Picture(self):
        """The file used as the source for the displayed image.  (str)"""
        return self._picture

    @Picture.setter
    def Picture(self, val):
        if not val:
            # Empty string passed; clear any current image
            self._picture = ""
            self._displayState = 1
            self._bmp = wx.Bitmap(1, 1, 1)
            self.__image = wx.Image(1, 1)  # self._bmp.ConvertToImage()
            self._showPic()
            return
        elif isinstance(val, wx.Image):
            # An image stored as a stream is being used
            self.__image = val
            self._picture = "(stream)"
        elif isinstance(val, wx.Bitmap):
            # a raw bitmap is being supplied
            self._bmp = val
            self.__image = val.ConvertToImage()
            self._picture = "(stream)"
        elif isinstance(val, memoryview):
            val = io.StringIO(val)
            img = wx.Image()
            img.LoadStream(val)
            self._setPicture(img)
            return
        else:
            if not os.path.isfile(val):
                origVal = val
                val = ui.getImagePath(val)
                if val is None or not os.path.isfile(val):
                    # This will raise an IOError if it fails
                    try:
                        val = utils.resolvePathAndUpdate(origVal)
                    except IOError:
                        val = None
                if val is None or not os.path.isfile(val):
                    # Bad image reference
                    dabo_module.error(_("No file named '%s' exists.") % origVal)
                    return
            self._picture = val
            self._displayState = 1
            idx = self.PictureIndex
            if idx != -1:
                # The image count is 1-based.
                maxIdx = self.FrameCount - 1
                if idx > maxIdx:
                    dabo_module.error(
                        _(
                            "Attempt to set PictureIndex (%(idx)s)to a value "
                            "greater than the maximum index available (%(maxIdx)s)."
                        )
                        % locals()
                    )
                    idx = self.PictureIndex = maxIdx
            try:
                self._Image.LoadFile(val, index=idx)
            except IndexError:
                # Note: when I try to load an invalid index, I get a segfault, so I don't know
                # how useful this is.
                self._Image.LoadFile(val, index=-1)
            if _USE_PIL:
                try:
                    pil_img = Image.open(val)
                    # Only jpeg images support this
                    exif = pil_img._getexif()
                    orientation = exif.get(_ORIENTATION_TAG, 1)
                    self._displayState = _exifToImg(orientation)
                except AttributeError:
                    # Not a jpeg, or not a version with the _getexif() method
                    pass
                except IOError:
                    # Bad image, or no exif data available
                    pass
        if self._Image.IsOk():
            self._imgProp = float(self._Image.GetWidth()) / float(self._Image.GetHeight())
        else:
            self._imgProp = 1.0
        self._showPic()

    @property
    def PictureIndex(self):
        """
        When displaying images from files that can contain multiple images, such as GIF, TIFF and
        ICO, this determines which image is used. Default=-1, which displays the first image for GIF
        and TIFF, and the main image for ICO.  (int)
        """
        return self._pictureIndex

    @PictureIndex.setter
    def PictureIndex(self, val):
        if self._constructed():
            self._pictureIndex = val
            if not self._inReload:
                # Re-load the image
                self._inReload = True
                self.Picture = self._picture
                self._inReload = False
        else:
            self._properties["PictureIndex"] = val

    @property
    def ScaleMode(self):
        """
        Determines how the image responds to sizing. Can be one of the following:

            =============== ===================
            Clip            Only that part of the image that fits in the control's size
                            is displayed
            Proportional    The image resizes to fit the control without changing its
                            original proportions. (default)
            Stretch         The image resizes to the Height/Width of the control.
            =============== ===================
        """
        return self._scaleMode

    @ScaleMode.setter
    def ScaleMode(self, val):
        """Only the first letter is significant."""
        initial = val[0].lower()
        modes = {"c": "Clip", "p": "Proportional", "s": "Stretch"}
        try:
            self._scaleMode = modes[initial]
            self._showPic()
        except KeyError:
            dabo_module.error(_("ScaleMode must be either 'Clip', 'Proportional' or 'Stretch'."))

    @property
    def Value(self):
        """Image content for this control  (binary img data)"""
        return self._imageData

    @Value.setter
    def Value(self, val):
        if self._constructed():
            if self._imageData == val:
                return
            img = self._imageData = None
            if val:
                try:
                    isFile = os.path.isfile(val)
                except (TypeError, ValueError):
                    isFile = False
                if isFile:
                    try:
                        self._imageData = open(val, "rb").read()
                    except Exception:
                        pass
                else:
                    # Probably an image stream
                    self._imageData = val
                try:
                    img = ui.imageFromData(self._imageData)
                except TypeError:
                    pass
            self._setPicture(img)
            self._afterValueChanged()
        else:
            self._properties["Value"] = val

    @property
    def _Image(self):
        """Underlying image handler object  (wx.Image)"""
        if self.__image is None:
            try:
                self.__image = wx.NullImage.Copy()
            except ui.assertionException:
                self.__image = wx.NullImage
        return self.__image

    DynamicPicture = makeDynamicProperty(Picture)
    DynamicScaleMode = makeDynamicProperty(ScaleMode)


ui.dImage = dImage


if __name__ == "__main__":
    from ..application import dApp

    class ImgForm(dForm):
        def afterInit(self):
            self.Caption = "dImage Demonstration"
            self.mainPanel = mp = ui.dPanel(self)
            self.Sizer.append1x(mp)
            sz = ui.dSizer("v")
            mp.Sizer = sz
            # Create a panel with horiz. and vert.  sliders
            self.imgPanel = ui.dPanel(mp)
            self.VSlider = ui.dSlider(
                mp, Orientation="V", Min=1, Max=100, Value=100, OnHit=self.onSlider
            )
            self.HSlider = ui.dSlider(
                mp, Orientation="H", Min=1, Max=100, Value=100, OnHit=self.onSlider
            )

            psz = self.imgPanel.Sizer = ui.dSizer("V")
            hsz = ui.dSizer("H")
            hsz.append1x(self.imgPanel)
            hsz.appendSpacer(10)
            hsz.append(self.VSlider, 0, "x")
            sz.DefaultBorder = 25
            sz.DefaultBorderLeft = sz.DefaultBorderRight = True
            sz.appendSpacer(25)
            sz.append(hsz, 1, "x")
            sz.appendSpacer(10)
            sz.append(self.HSlider, 0, "x")
            sz.appendSpacer(10)

            # Create the image control
            self.img = dImage(self.imgPanel)

            hsz = ui.dSizer("H")
            hsz.DefaultSpacing = 10
            ui.dBitmapButton(
                mp,
                RegID="btnRotateCW",
                Picture="rotateCW",
                OnHit=self.onRotateCW,
                Size=(36, 36),
            )
            ui.dBitmapButton(
                mp,
                RegID="btnRotateCCW",
                Picture="rotateCCW",
                OnHit=self.onRotateCCW,
                Size=(36, 36),
            )
            ui.dBitmapButton(
                mp,
                RegID="btnFlipHorizontal",
                Picture="flip_horiz",
                OnHit=self.onFlipHoriz,
                Size=(36, 36),
            )
            ui.dBitmapButton(
                mp,
                RegID="btnFlipVertical",
                Picture="flip_vert",
                OnHit=self.onFlipVert,
                Size=(36, 36),
            )
            hsz.append(self.btnRotateCW)
            hsz.append(self.btnRotateCCW)
            hsz.append(self.btnFlipHorizontal)
            hsz.append(self.btnFlipVertical)

            self.ddScale = ui.dDropdownList(
                mp,
                Choices=["Proportional", "Stretch", "Clip"],
                DataSource="self.Form.img",
                DataField="ScaleMode",
            )
            self.ddScale.PositionValue = 0
            btn = ui.dButton(mp, Caption="Load Image", OnHit=self.onLoadImage)
            btnOK = ui.dButton(mp, Caption="Done", OnHit=self.close)
            hsz.append(self.ddScale, 0, "x")
            hsz.append(btn, 0, "x")
            hsz.append(btnOK, 0, "x")
            sz.append(hsz, 0, alignment="right")
            sz.appendSpacer(25)

            # Set the idle update flage
            self.needUpdate = False

        def onRotateCW(self, evt):
            self.img.rotateClockwise()

        def onRotateCCW(self, evt):
            self.img.rotateCounterClockwise()

        def onFlipVert(self, evt):
            self.img.flipVertically()

        def onFlipHoriz(self, evt):
            self.img.flipHorizontally()

        def onSlider(self, evt):
            # Vertical sliders have their low value on the bottom on OSX;
            # on MSW and GTK, the low value is at the top
            val = evt.EventObject.Value * 0.01
            dir = evt.EventObject.Orientation[0].lower()
            if dir == "h":
                # Change the width of the image
                self.img.Width = self.imgPanel.Width * val
            else:
                self.img.Height = self.imgPanel.Height * val

        def onLoadImage(self, evt):
            f = ui.getFile("jpg", "png", "gif", "bmp", "tif", "ico", "*")
            if f:
                self.img.Picture = f

        def onResize(self, evt):
            self.needUpdate = True

        def onIdle(self, evt):
            if self.needUpdate:
                self.needUpdate = False
                wd = self.HSlider.Value * 0.01 * self.imgPanel.Width
                ht = self.VSlider.Value * 0.01 * self.imgPanel.Height
                self.img.Size = (wd, ht)

    app = dApp()
    app.MainFormClass = ImgForm
    app.start()
