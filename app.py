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
import sys, os
import db, ui

class Collection(list):
    ''' Collection : Base class for the various collection
                     classes used in the app object.
    '''
    def __init__(self):
        list.__init__(self)
        
    def add(self, objRef):
        ''' Collection.add(objRef)
            Add the object reference to the collection.
        '''
        self.append(objRef)
    
    def remove(self, index):
        ''' Collection.remove(objRef)
            Delete the object reference from the collection.
        '''
        del self[index]

                
class App(object):
    ''' dabo.App : The containing object for the entire application.
                    Various UI's will have app objects also, which 
                    dApp is a wrapper for. '''
    def __init__(self):
        object.__init__(self)
        self._initProperties()
        
    def setup(self):
        # dabo is going to want to import various things from the homeDir
        sys.path.append(self.homeDir)
        self.initUI()
        self.initDB()

    def initDB(self):
        dbConnectionDefs = None
        try:
            globals_ = {}
            execfile("%s/dbConnectionDefs.py" % (self.homeDir,), globals_)
            dbConnectionDefs = globals_["dbConnectionDefs"]
        except:
            dbConnectionDefs = None
        
        if dbConnectionDefs <> None and type(dbConnectionDefs) == type(dict()):
            
            # For each connection type, get a db() object bound:
            for entry in dbConnectionDefs:
                dbConnectionDefs[entry]["dbObject"] = db.Db()
            print "%s database connection definition(s) loaded." % len(dbConnectionDefs)

        else:
            print "No database connection definitions loaded (dbConnectionDefs.py)"
        self.dbConnectionDefs = dbConnectionDefs 

                
    def initUI(self):
        if self.uiType == None:
            # Future: read a config file in the homeDir
            # Present: set UI to wx
            uiType = "wx"
            
            # Now, get the appropriate ui module into self.uiModule
            uiModule = ui.getUI(uiType)
            if uiModule <> None:
                self.uiType = uiType
                self.uiModule = uiModule
        else:
            # Custom app code already set this: don't touch
            pass
        print "User interface set to %s using module %s" % (self.uiType, self.uiModule)
            
    def start(self):
        print "app.start"
              
    def _initProperties(self):
        # it is useful to know from where we came
        self.homeDir = os.getcwd()
        
        self.uiType   = None    # ('wx', 'qt', 'curses', 'http', etc.)
        self.uiModule = None
        
        # Initialize UI collections
        self.uiForms       = Collection()
        self.uiMenus       = Collection()
        self.uiToolBars    = Collection()
        self.uiResources   = {}
        
        # Initialize DB collections
        self.dbConnectionDefs = {} 
