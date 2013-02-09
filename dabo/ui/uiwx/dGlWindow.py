# -*- coding: utf-8 -*-
from wx import glcanvas
import wx
import dabo
import dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty

try:
	from OpenGL.GL import *
	from OpenGL.GLUT import *
	openGL = True
except ImportError:
	openGL = False
except StandardError, e:
	# Report the error, and abandon the import
	dabo.log.error(_("Error importing OpenGL: %s") % e)
	openGL = False


class dGlWindow(cm.dControlMixin, glcanvas.GLCanvas):
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		if not openGL:
			raise ImportError, "PyOpenGL is not present, so dGlWindow cannot instantiate."

		self.init = False
		self._rotate = self._pan = False

		#set initial mouse position for rotate
		self.lastx = self.x = 30
		self.lasty = self.y = 30
		self._leftDown = self._rightDown = False

		self._baseClass = dGlWindow
		preClass = glcanvas.GLCanvas
		cm.dControlMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)

	def initGL(self):
		"""Hook function.  Put your initial GL code in here."""
		pass


	def onDraw(self):
		"""
		Hook function.  Put the code here for what happens when you draw.

		.. note::
			You don't need to swap buffers here....We do this for you automatically.

		"""
		pass


	def onResize(self, event):
		if self.GetContext():
			self.SetCurrent()
			glViewport(0, 0, self.Width, self.Height)


	def onPaint(self, event):
		dc = wx.PaintDC(self)
		self.SetCurrent()
		if not self.init:
			self.initGL()
			self.init = True
		self._onDraw()


	def _onDraw(self):
		#Call user hook method
		self.onDraw()

		if self.Rotate:
			glRotatef((self.y - self.lasty), 0.0, 0.0, 1.0);
			glRotatef((self.x - self.lastx), 1.0, 0.0, 0.0);

		#if self.Pan:
		#	pass

		self.SwapBuffers()


	def onMouseRightDown(self, evt):
		self.x, self.y = self.lastx, self.lasty = evt.EventData["mousePosition"]
		self._rightDown = True


	def onMouseRightUp(self, evt):
		self._rightDown = False

	#def onMouseLeftDown(self, evt):
		#pass

	#def onMouseLeftUp(self, evt):
		#pass

	def onMouseMove(self, evt):
		if self._rightDown:	#want to rotate object
			self.lastx, self.lasty = self.x, self.y	#store the previous x and y
			self.x, self.y = evt.EventData["mousePosition"]	#store the new x,y so we know how much to rotate
			self.Refresh(False)	#Mark window as "dirty" so it will be repainted

	# Getters and Setters
	def _getRotate(self):
		return self._rotate

	def _setRotate(self, val):
		self._rotate = val

	# Property Definitions
	Rotate = property(_getRotate, _setRotate, None,
		_("Rotate on Right Mouse Click and Drag"))


class _dGlWindow_test(dGlWindow):
	def initProperties(self):
		self.Rotate = True

	def initGL(self):
		# set viewing projection
		glMatrixMode(GL_PROJECTION)
		glFrustum(-0.5, 0.5, -0.5, 0.5, 1.0, 3.0)

		# position viewer
		glMatrixMode(GL_MODELVIEW)
		glTranslatef(0.0, 0.0, -2.0)

		# position object
		glRotatef(self.y, 1.0, 0.0, 0.0)
		glRotatef(self.x, 0.0, 1.0, 0.0)

		glEnable(GL_DEPTH_TEST)
		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)


	def onDraw(self):
		# clear color and depth buffers
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		# draw six faces of a cube
		glBegin(GL_QUADS)
		glNormal3f( 0.0, 0.0, 1.0)
		glVertex3f( 0.5, 0.5, 0.5)
		glVertex3f(-0.5, 0.5, 0.5)
		glVertex3f(-0.5,-0.5, 0.5)
		glVertex3f( 0.5,-0.5, 0.5)

		glNormal3f( 0.0, 0.0,-1.0)
		glVertex3f(-0.5,-0.5,-0.5)
		glVertex3f(-0.5, 0.5,-0.5)
		glVertex3f( 0.5, 0.5,-0.5)
		glVertex3f( 0.5,-0.5,-0.5)

		glNormal3f( 0.0, 1.0, 0.0)
		glVertex3f( 0.5, 0.5, 0.5)
		glVertex3f( 0.5, 0.5,-0.5)
		glVertex3f(-0.5, 0.5,-0.5)
		glVertex3f(-0.5, 0.5, 0.5)

		glNormal3f( 0.0,-1.0, 0.0)
		glVertex3f(-0.5,-0.5,-0.5)
		glVertex3f( 0.5,-0.5,-0.5)
		glVertex3f( 0.5,-0.5, 0.5)
		glVertex3f(-0.5,-0.5, 0.5)

		glNormal3f( 1.0, 0.0, 0.0)
		glVertex3f( 0.5, 0.5, 0.5)
		glVertex3f( 0.5,-0.5, 0.5)
		glVertex3f( 0.5,-0.5,-0.5)
		glVertex3f( 0.5, 0.5,-0.5)

		glNormal3f(-1.0, 0.0, 0.0)
		glVertex3f(-0.5,-0.5,-0.5)
		glVertex3f(-0.5,-0.5, 0.5)
		glVertex3f(-0.5, 0.5, 0.5)
		glVertex3f(-0.5, 0.5,-0.5)
		glEnd()

class _dGlWindow_test2(dGlWindow):
	def initProperties(self):
		self.Rotate = True

	def initGL(self):
		glMatrixMode(GL_PROJECTION)
		# camera frustrum setup
		glFrustum(-0.5, 0.5, -0.5, 0.5, 1.0, 3.0)
		glMaterial(GL_FRONT, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
		glMaterial(GL_FRONT, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
		glMaterial(GL_FRONT, GL_SPECULAR, [1.0, 0.0, 1.0, 1.0])
		glMaterial(GL_FRONT, GL_SHININESS, 50.0)
		glLight(GL_LIGHT0, GL_AMBIENT, [0.0, 1.0, 0.0, 1.0])
		glLight(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
		glLight(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
		glLight(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 1.0, 0.0])
		glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		glDepthFunc(GL_LESS)
		glEnable(GL_DEPTH_TEST)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		# position viewer
		glMatrixMode(GL_MODELVIEW)
		# position viewer
		glTranslatef(0.0, 0.0, -2.0);
		#
		glutInit([])


	def onDraw(self):
		# clear color and depth buffers
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		# use a fresh transformation matrix
		glPushMatrix()
		# position object
		#glTranslate(0.0, 0.0, -2.0)
		glRotate(30.0, 1.0, 0.0, 0.0)
		glRotate(30.0, 0.0, 1.0, 0.0)

		glTranslate(0, -1, 0)
		glRotate(250, 1, 0, 0)
		glutSolidCone(0.5, 1, 30, 5)
		glPopMatrix()


if __name__ == "__main__":
	import test
	test.Test().runTest(_dGlWindow_test)
	test.Test().runTest(_dGlWindow_test2)
