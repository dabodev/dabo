''' dPemMixin.py: Provide common PEM functionality '''

class dPemMixin(object):
    ''' Provide Property/Event/Method interfaces for dForms and dControls.
    
    Subclasses can extend the property sheet by defining their own get/set
    functions along with their own property() statements.
    '''
    
    # Scroll to the bottom to see the property definitions.
    
    # Property get/set/delete methods follow.
    def _getBaseClass(self):
        return self._baseClass
    def _setBaseClass(self, baseClass):
        self._baseClass = baseClass
        
    def _getParentClass(self):
        return self._parentClass
    def _setParentClass(self, parentClass):
        self._parentClass = parentClass
    
        
    def _getFont(self):
        return self.GetFont()
    def _setFont(self, font):
        self.SetFont(font)
    
        
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
    
        
    def _getWidth(self):
        return self.GetSize()[0]
    def _setWidth(self, width):
        self.SetSize((width, self.Height))

    def _getHeight(self):
        return self.GetSize()[1]
    def _setHeight(self, height):
        self.SetSize((self.Width, height))
    
    def _getSize(self): 
        return self.GetPosition()
    def _setSize(self, size):
        self.SetSize(size)


    def _getName(self):
        return self.GetName()
    def _setName(self, name):
        self.SetName(name)


    def _getCaption(self):
        return self.GetLabel()
    def _setCaption(self, caption):
        self.SetLabel(caption)

        
    # Property definitions follow
    Name = property(_getName, _setName, None, 
                    'The name of the object.')
    BaseClass = property(_getBaseClass, _setBaseClass, None, 
                    'The base class of the object')
    ParentClass = property(_getParentClass, _setParentClass, None, 
                    'The parent class of the object.')
    
    Font = property(_getFont, _setFont, None,
                    'The font properties of the object.')

    Top = property(_getTop, _setTop, None, 
                    'The top position of the object.')
    Left = property(_getLeft, _setLeft, None,
                    'The left position of the object.')
    Position = property(_getPosition, _setPosition, None, 
                    'The (x,y) position of the object.')

    Width = property(_getWidth, _setWidth, None,
                    'The width of the object.')
    Height = property(_getHeight, _setHeight, None,
                    'The height of the object.')
    Size = property(_getSize, _setSize, None,
                    'The size of the object')

    Name = property(_getName, _setName, None,
                    'The name of the object.')
    Caption = property(_getCaption, _setCaption, None, 
                    'The caption of the object.')
    
        
if __name__ == "__main__":
    o = dPemMixin()
    print o.BaseClass
    o.BaseClass = "dForm"
    print o.BaseClass