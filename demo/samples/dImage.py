# -*- coding: utf-8 -*-
import dabo
import dabo.ui
import dabo.dEvents as dEvents
from dabo.dLocalize import _


from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer
from dabo.ui import dTextBox
from dabo.ui import dButton
from dabo.ui import dDropdownList
from dabo.ui import dSlider
from dabo.ui import dBitmapButton

dImage = dabo.ui.dImage


class TestPanel(dPanel):
    def afterInit(self):
        # Set the idle update flag
        self.needUpdate = False

        # Create a panel with horiz. and vert.  sliders
        self.imgPanel = dPanel(self)
        self.VSlider = dSlider(
            self,
            Orientation="V",
            Min=1,
            Max=100,
            Value=100,
            Continuous=True,
            OnHit=self.onSlider,
        )
        self.HSlider = dSlider(
            self,
            Orientation="H",
            Min=1,
            Max=100,
            Value=100,
            Continuous=True,
            OnHit=self.onSlider,
        )

        mainSizer = self.Sizer = dSizer("V")
        psz = self.imgPanel.Sizer = dSizer("V")
        hsz = dSizer("H")
        hsz.append1x(self.imgPanel)
        hsz.appendSpacer(10)
        hsz.append(self.VSlider, 0, "x")
        mainSizer.DefaultBorder = 25
        mainSizer.DefaultBorderLeft = mainSizer.DefaultBorderRight = True
        mainSizer.appendSpacer(25)
        mainSizer.append(hsz, 1, "x")
        mainSizer.appendSpacer(10)
        mainSizer.append(self.HSlider, 0, "x")
        mainSizer.appendSpacer(10)

        # Create the image control
        self.img = dImage(self.imgPanel, BackColor="yellow", DroppedFileHandler=self)

        hsz = dSizer("H")
        hsz.DefaultSpacing = 10
        btn = dBitmapButton(self, Picture="rotateCW", OnHit=self.onRotateCW, Size=(36, 36))
        hsz.append(btn)
        btn = dBitmapButton(self, Picture="rotateCCW", OnHit=self.onRotateCCW, Size=(36, 36))
        hsz.append(btn)
        btn = dBitmapButton(self, Picture="flip_horiz", OnHit=self.onFlipHoriz, Size=(36, 36))
        hsz.append(btn)
        btn = dBitmapButton(self, Picture="flip_vert", OnHit=self.onFlipVert, Size=(36, 36))
        hsz.append(btn)

        self.ddScale = dDropdownList(
            self,
            Choices=["Proportional", "Stretch", "Clip"],
            PositionValue=0,
            ValueMode="String",
        )
        self.ddScale.DataSource = self.img
        self.ddScale.DataField = "ScaleMode"

        btn = dButton(self, Caption=_("Load Your Own Image"), OnHit=self.onLoadImage)

        hsz.append(self.ddScale, "x")
        hsz.append(btn, "x")
        mainSizer.append(hsz, alignment="right")
        mainSizer.appendSpacer(25)

        # Load an image
        self.img.Picture = "media/homer.jpg"

    def processDroppedFiles(self, filelist):
        self.img.Picture = filelist[0]

    def onRotateCW(self, evt):
        self.img.rotateClockwise()

    def onRotateCCW(self, evt):
        self.img.rotateCounterClockwise()

    def onFlipHoriz(self, evt):
        self.img.flipHorizontally()

    def onFlipVert(self, evt):
        self.img.flipVertically()

    def onSlider(self, evt):
        slider = evt.EventObject
        val = slider.Value * 0.01
        ornt = slider.Orientation[0].lower()
        if ornt == "h":
            # Change the width of the image
            self.img.Width = self.imgPanel.Width * val
        else:
            self.img.Height = self.imgPanel.Height * val

    # Without Dabo, you need to create this exact string to get the same behavior.
    #    JPEG Files (*.jpg)|*.jpg|PNG Files (*.png)|*.png|GIF Files (*.gif)|*.gif|Bitmap Files (*.bmp)|*.bmp|All Files (*)|*
    def onLoadImage(self, evt):
        f = dabo.ui.getFile("jpg", "png", "gif", "bmp", "*")
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


category = "Controls.dImage"

overview = """
<p>The <b>dImage</b> class is used to display images in your app. It provides
simple ways to control the sizing, scaling and rotation of images. It can use any
of the following common image formats: <b>PNG</b>, <b>JPEG</b>,
<b>GIF</b> and <b>BMP</b>.</p>

<p>To display an image, just set the <b>Picture</b> property to the path to the
file containing the image; the class will do the rest. You can also set the DataSource
and DataField to an image column in a database.</p>

<p>The <b>ScaleMode</b> property controls how the image is scaled to fit the control size:</p>
<ul>
<li><b>Proportional</b>: the original ratio of the Width and Height is maintained, which may result in
empty areas.</li>
<li><b>Stretch</b>: the image completely fills the area allotted to it, which may result in distortion.</li>
<li><b>Clip</b>: The original size of the image is maintained. Changing the control size just shows more
or less of the image, or more empty space if the control is bigger than the original image size.</li>
</ul>
"""
