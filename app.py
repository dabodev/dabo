''' app.py : The application object for Dabo.

    This object gets instantiated from the client app's main.py,
    and lives through the life of the application.
    
        -- sets up an empty data connections object which holds 
        -- connectInfo connected to pretty names, then looks for
        -- an expected file and if it exists fills out a connection
        -- entry.

        -- decides which ui to use (wx) and gets that ball rolling

        -- makes a system menu bar, based on a combination
        -- of dabo defaults and user resource files.

        -- ditto for toolbar(s)

        -- looks for a mainFrame ui resource file in an expected 
        -- place, otherwise uses default dabo mainFrame, and 
        -- instantiates that. 

        -- maintains a forms collection and provides interfaces for
        -- opening dForms, closing them, and iterating through them.

        -- starts the main app event loop.
'''

class dApp(object):
    ''' dabo.dApp : The containing object for the entire application.
                    Various UI's will have app objects also, which 
                    dApp is a wrapper for. '''
                    
    def __init__(self):
        object.__init__(self)

        self._initProperties()
        
    def setup(self):
        print "app.setup"
    
    def start(self):
        print "app.start"
    
    def addForm(self, formRef):
        ''' dApp.addForm(formRef)
            Add the form to dApp's uiForms collection, which is a
            list of dictionaries.'''
        self.uiForms.append(formRef)
    
    def delForm(self, index):
        ''' dApp.delForm(index)
            Delete the form, if found, from the uiForms collection.'''
        try:
            del self.uiForms[index]
        except:
            pass
              
    def _initProperties(self):
        self.uiType = None # ('wx', 'qt', 'curses', 'http', etc.)
        
        # Initialize UI collections
        self.uiForms       = []
        self.uiMenus       = []
        self.uiToolBars    = []
        self.uiResources   = {}
        
        # Initialize DB collections
        self.dbConnections = {} 
