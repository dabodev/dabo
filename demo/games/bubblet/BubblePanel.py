# -*- coding: utf-8 -*-
import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _
import random


class BubblePanel(dabo.ui.dPanel):
	def afterInit(self):
		self.Buffered = True
		# Create a background that will change to indicate
		# selected status. 
		self.back = self.drawRectangle(0,0,1,1, penWidth=0)
		# Create a dummy circle, and store the reference
		self.circle = self.drawCircle(0,0,1)
		
		self._selected = False
		self._colors = ["blue", "green", "red", "yellow", "purple"]
		self._color = self.randColor()
		
		if self.Application.Platform == "Win":
			self.selectedBackColor = (192,192,255)
		else:
			self.selectedBackColor = (128,128,192)
		self.unselectedBackColor = (255,255,255)
		self.row = -1
		self.col = -1
		self.onResize(None)
		self.update()
		
	
	def randColor(self):
		return random.choice(self._colors)
	
	
	def setRandomColor(self, repaint=False):
		self.Color = self.randColor()
		if repaint:
			self.update()
		
	
	def onResize(self, evt):
		self.circle.AutoUpdate = self.back.AutoUpdate = False
		wd = self.Width
		ht = self.Height
		self.back.Width, self.back.Height = wd, ht
		pos = ( (wd/2), (ht/2) )
		rad = (min(ht, wd) / 2)
		self.circle.Xpos = int(wd/2)
		self.circle.Ypos = int(ht/2)
		self.circle.Radius = rad
		self.circle.AutoUpdate = self.back.AutoUpdate = True
		self.update()
	
	
	def update(self, evt=None):
		self.circle.AutoUpdate = self.back.AutoUpdate = False
		self.circle.FillColor = self.Color
		if self.Color:
			self.circle.PenWidth = 1
		else:
			self.circle.PenWidth = 0
		if self.Selected:
			self.back.FillColor = self.selectedBackColor
		else:
			self.back.FillColor = self.unselectedBackColor			
		self.circle.AutoUpdate = self.back.AutoUpdate = True
		super(BubblePanel, self).update()		


	def onMouseLeftClick(self, evt):
		self.Parent.bubbleClick(self)
	
	
	def _getColor(self):
		return self._color
		
	def _setColor(self, color):
		if color is None:
			self._color = None
		else:
			self._color = color.lower()

			
	def _getSelected(self):
		return self._selected

	def _setSelected(self, sel):
		self._selected = sel


	Color = property(_getColor, _setColor, None,
			_("Color for this bubble  (str or tuple)"))

	Selected = property(_getSelected, _setSelected, None,
			_("Selection Status  (bool)"))
	
