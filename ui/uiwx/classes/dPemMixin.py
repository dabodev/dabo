''' dPemMixin.py: Provide common PEM functionality '''
import wx, sys

class dPemMixin(object):
    ''' Provide Property/Event/Method interfaces for dForms and dControls.

    Subclasses can extend the property sheet by defining their own get/set
    functions along with their own property() statements.
    '''
    def __getattr__(self, att):
        ''' Try to resolve att to a child object reference.

        This allows accessing children with the style:
            self.mainPanel.txtName.Value = "test"
        '''
        try:
            ret = self.FindWindowByName(att)
        except TypeError:
            ret = None
        if not ret:
            raise AttributeError, "%s object has no attribute %s" % (
                self._name, att)
        else:
            return ret


    def doDefault(cls, *args, **kwargs):
        ''' A much simpler way to call superclass methods than super().

        The python super(type,ref).method(args) syntax is really convoluted,
        so this doDefault() is a wrapper for that that constructs the super()
        call on behalf of the caller.

        Where you would use:
            super(cls,obj).method([args]),
        instead use:
            cls.doDefault([args])
        '''
        frame = sys._getframe(1)
        self = frame.f_locals['self']
        methodName = frame.f_code.co_name
        return eval('super(cls, self).%s(*args, **kwargs)' % methodName)
    doDefault = classmethod(doDefault)


    def beforeInit(self, preCreateObject):
        ''' Called before the wx object is fully instantiated.

        Allows things like extra style flags to be set or XRC resources to
        be loaded. Subclasses can override this as necessary.
        '''
        self._name = '?'


    def __init__(self, *args, **kwargs):
        if self.Position == (-1, -1):
            # The object was instantiated with a default position,
            # which ended up being (-1,-1). Change this to (0,0). 
            # This is completely moot when sizers are employed.
            self.Position = (0, 0)

        if self.Size == (-1, -1):
            # The object was instantiated with a default position,
            # which ended up being (-1,-1). Change this to (0,0). 
            # This is completely moot when sizers are employed.
            self.Size = (0, 0)

        if not wx.HelpProvider.Get():
            # The app hasn't set a help provider, and one is needed
            # to be able to save/restore help text.
            wx.HelpProvider.Set(wx.SimpleHelpProvider())
        

    def afterInit(self):
        ''' Called after the wx object's __init__ has run fully.

        Subclasses should place their __init__ code here in this hook,
        instead of overriding __init__ directly.
        '''
        pass


    def getPropertyList(classOrInstance):
        ''' Return the list of properties for this object (class or instance).
        '''
        propList = []
        for item in dir(classOrInstance):
            if type(eval('classOrInstance.%s' % item)) == property:
                propList.append(item)
        return propList
    getPropertyList = classmethod(getPropertyList)


    # The following 3 flag functions are used in some of the property
    # get/set functions.
    def hasWindowStyleFlag(self, flag):
        ''' Return whether or not the flag is set. (bool)
        '''
        return (self.GetWindowStyleFlag() & flag) == flag

    def addWindowStyleFlag(self, flag):
        ''' Add the flag to the window style.
        '''
        self.SetWindowStyleFlag(self.GetWindowStyleFlag() | flag)

    def delWindowStyleFlag(self, flag):
        ''' Remove the flag from the window style.
        '''
        self.SetWindowStyleFlag(self.GetWindowStyleFlag() & (~flag))


    # Scroll to the bottom to see the property definitions.

    # Property get/set/delete methods follow.
    def _getClass(self):
        try:
            return self.__class__
        except AttributeError:
            return None

    def _getBaseClass(self):
        try:
            return self._baseClass
        except AttributeError:
            return None

    def _getSuperClass(self):
        if self.BaseClass == self.Class:
            # Any higher up goes into the wx classes:
            return None
        else:
            return self.__class__.__base__


    def _getFont(self):
        return self.GetFont()
    def _setFont(self, font):
        self.SetFont(font)

    def _getFontInfo(self):
        return self.Font.GetNativeFontInfoDesc()

    def _getFontBold(self):
        return self.Font.GetWeight() == wx.BOLD
    def _setFontBold(self, fontBold):
        font = self.Font
        if fontBold:
            font.SetWeight(wx.BOLD)
        else:
            font.SetWeight(wx.LIGHT)    # wx.NORMAL doesn't seem to work...
        self.Font = font

    def _getFontItalic(self):
        return self.Font.GetStyle() == wx.ITALIC
    def _setFontItalic(self, fontItalic):
        font = self.Font
        if fontItalic:
            font.SetStyle(wx.ITALIC)
        else:
            font.SetStyle(wx.NORMAL)
        self.Font = font

    def _getFontFace(self):
        return self.Font.GetFaceName()
    def _setFontFace(self, fontFace):
        font = self.Font
        font.SetFaceName(fontFace)
        self.Font = font

    def _getFontSize(self):
        return self.Font.GetPointSize()
    def _setFontSize(self, fontSize):
        font = self.Font
        font.SetPointSize(fontSize)
        self.Font = font

    def _getFontUnderline(self):
        return self.Font.GetUnderlined()
    def _setFontUnderline(self, val):
        # underlining doesn't seem to be working...
        font = self.Font
        font.SetUnderlined(val)
        self.Font = font


    def _getTop(self):
        return self.GetPosition()[1]
    def _setTop(self, top):
        self.SetPosition((self.Left, top))

    def _getLeft(self):
        return self.GetPosition()[0]
    def _setLeft(self, left):
        self.SetPosition((left, self.Top))

    def _getPosition(self):
        return self.GetPosition()
    def _setPosition(self, position):
        self.SetPosition(position)

    def _getBottom(self):
        return self.Top + self.Height
    def _setBottom(self, bottom):
        self.Top = bottom - self.Height

    def _getRight(self):
        return self.Left + self.Width
    def _setRight(self, right):
        self.Left = right - self.Width


    def _getWidth(self):
        return self.GetSize()[0]
    def _setWidth(self, width):
        self.SetSize((width, self.Height))

    def _getHeight(self):
        return self.GetSize()[1]
    def _setHeight(self, height):
        self.SetSize((self.Width, height))

    def _getSize(self): 
        return self.GetSize()
    def _setSize(self, size):
        self.SetSize(size)


    def _getName(self):
        name = self.GetName()
        self._name = name      # keeps name available even after C++ object is gone.
        return name
    def _setName(self, name):
        self._name = name      # keeps name available even after C++ object is gone.
        self.SetName(name)


    def _getCaption(self):
        return self.GetLabel()
    def _setCaption(self, caption):
        self.SetLabel(caption)
        
        # Frames have a Title separate from Label, but I can't think
        # of a reason why that would be necessary... can you? 
        self.SetTitle(caption)

        
    def _getEnabled(self):
        return self.IsEnabled()
    def _setEnabled(self, value):
        self.Enable(value)


    def _getBackColor(self):
        return self.GetBackgroundColour()
    def _setBackColor(self, value):
        self.SetBackgroundColour(value)

    def _getForeColor(self):
        return self.GetForegroundColour()
    def _setForeColor(self, value):
        self.GetForegroundColour(value)


    def _getMousePointer(self):
        return self.GetCursor()
    def _setMousePointer(self, value):
        self.SetCursor(value)


    def _getToolTipText(self):
        t = self.GetToolTip()
        if t:
            return t.GetTip()
        else:
            return ''
    def _setToolTipText(self, value):
        t = self.GetToolTip()
        if t:
            t.SetTip(value)
        else:
            t = wx.ToolTip(value)
            self.SetToolTip(t)


    def _getHelpContextText(self):
        return self.GetHelpText()
    def _setHelpContextText(self, value):
        self.SetHelpText(value)


    def _getVisible(self):
        return self.IsShown()
    def _setVisible(self, value):
        self.Show(value)

    def _getParent(self):
        return self.GetParent()
    def _setParent(self, newParentObject):
        # Note that this isn't allowed in the property definition, however this
        # is how we'd do it *if* it were allowed <g>:
        self.Reparent(newParentObject)

    def _getWindowHandle(self):
        return self.GetHandle()

    def _getBorderStyle(self):
        if self.hasWindowStyleFlag(wx.RAISED_BORDER):
            return 'Raised'
        elif self.hasWindowStyleFlag(wx.SUNKEN_BORDER):
            return 'Sunken'
        elif self.hasWindowStyleFlag(wx.SIMPLE_BORDER):
            return 'Simple'
        else:
            return 'None'
    def _setBorderStyle(self, style):
        if style == 'None':
            self.addWindowStyleFlag(wx.NO_BORDER)
        elif style == 'Simple':
            self.addWindowStyleFlag(wx.SIMPLE_BORDER)
        elif style == 'Sunken':
            self.addWindowStyleFlag(wx.SUNKEN_BORDER)
        elif style == 'Raised':
            self.addWindowStyleFlag(wx.RAISED_BORDER)


    # Property definitions follow
    Name = property(_getName, _setName, None, 
                    'The name of the object. (str)')
    Class = property(_getClass, None, None,
                    'The class the object is based on. Read-only. (class)')
    BaseClass = property(_getBaseClass, None, None, 
                    'The base class of the object. Read-only. (class)')
    SuperClass = property(_getSuperClass, None, None, 
                    'The parent class of the object. Read-only. (class)')

    Parent = property(_getParent, None, None,
                    'The containing object. Read-only. (obj)')

    WindowHandle = property(_getWindowHandle, None, None,
                    'The platform-specific handle for the window. Read-only. (long)')

    Font = property(_getFont, _setFont, None,
                    'The font properties of the object. (obj)')
    FontInfo = property(_getFontInfo, None, None,
                    'Specifies the platform-native font info string. Read-only. (str)')
    FontBold = property(_getFontBold, _setFontBold, None,
                    'Specifies if the font is bold-faced. (bool)')
    FontItalic = property(_getFontItalic, _setFontItalic, None,
                    'Specifies whether font is italicized. (bool)')
    FontFace = property(_getFontFace, _setFontFace, None,
                    'Specifies the font face. (str)')
    FontSize = property(_getFontSize, _setFontSize, None,
                    'Specifies the point size of the font. (int)')
    FontUnderline = property(_getFontUnderline, _setFontUnderline, None,
                    'Specifies whether text is underlined. (bool)')

    Top = property(_getTop, _setTop, None, 
                    'The top position of the object. (int)')
    Left = property(_getLeft, _setLeft, None,
                    'The left position of the object. (int)')
    Bottom = property(_getBottom, _setBottom, None,
                    'The position of the bottom part of the object. (int)')
    Right = property(_getRight, _setRight, None,
                    'The position of the right part of the object. (int)')
    Position = property(_getPosition, _setPosition, None, 
                    'The (x,y) position of the object. (tuple)')

    Width = property(_getWidth, _setWidth, None,
                    'The width of the object. (int)')
    Height = property(_getHeight, _setHeight, None,
                    'The height of the object. (int)')
    Size = property(_getSize, _setSize, None,
                    'The size of the object. (tuple)')


    Caption = property(_getCaption, _setCaption, None, 
                    'The caption of the object. (str)')

    Enabled = property(_getEnabled, _setEnabled, None,
                    'Specifies whether the object (and its children) can get user input. (bool)')

    Visible = property(_getVisible, _setVisible, None,
                    'Specifies whether the object is visible at runtime. (bool)')                    


    BackColor = property(_getBackColor, _setBackColor, None,
                    'Specifies the background color of the object. (tuple)')

    ForeColor = property(_getForeColor, _setForeColor, None,
                    'Specifies the foreground color of the object. (tuple)')

    MousePointer = property(_getMousePointer, _setMousePointer, None,
                    'Specifies the shape of the mouse pointer when it enters this window. (obj)')

    ToolTipText = property(_getToolTipText, _setToolTipText, None,
                    'Specifies the tooltip text associated with this window. (str)')

    HelpContextText = property(_getHelpContextText, _setHelpContextText, None,
                    'Specifies the context-sensitive help text associated with this window. (str)')

    BorderStyle = property(_getBorderStyle, _setBorderStyle, None,
                    'Specifies the type of border for this window. (int). \n'
                    '     None \n'
                    '     Simple \n'
                    '     Sunken \n'
                    '     Raised')


if __name__ == "__main__":
    o = dPemMixin()
    print o.BaseClass
    o.BaseClass = "dForm"
    print o.BaseClass
