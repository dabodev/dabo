''' app.py : The application object for Dabo.

    This object gets instantiated from the client app's main.py,
    and lives through the life of the application.
    
        -- set up an empty data connections object which holds 
        -- connectInfo objects connected to pretty names. Entries
        -- can be added programatically, but upon initialiazation
        -- it will look for a file called 'dbConnectionDefs.py' which
        -- contains connection definitions.

        -- Set up a DB Connection manager, that is basically a dictionary
        -- of dConnection objects. This allows connections to be shared
        -- application-wide.

        -- decide which ui to use (wx) and gets that ball rolling

        -- make a system menu bar, based on a combination
        -- of dabo defaults and user resource files.

        -- ditto for toolbar(s)

        -- look for a mainFrame ui resource file in an expected 
        -- place, otherwise uses default dabo mainFrame, and 
        -- instantiate that. 

        -- maintain a forms collection and provide interfaces for
        -- opening dForms, closing them, and iterating through them.

        -- start the main app event loop.

        -- clean up and exit gracefully
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

                
class dApp(object):
    ''' dabo.dApp : The containing object for the entire application.
                   Various UI's will have app objects also, which 
                   dabo.App is a wrapper for. 
    '''

    def __init__(self):
        object.__init__(self)
        self._initProperties()
        
    def setup(self):
        ''' Set up the app - call this before start().'''

        # dabo is going to want to import various things from the homeDir
        sys.path.append(self.homeDir)
    
        self._initUI()
        self._initDB()

    def start(self):
        ''' Start the application event loop, which involves
            wrapping the application object for the ui library
            being used.
        '''
        self.uiApp = self.uiModule.uiApp()
        self.uiApp.start(self)
        self.finish()
    
    def finish(self):
        ''' The main event loop has exited and the application
            is about to finish.
        '''
        pass
        
    def _initProperties(self):
        ''' Initialize the public properties of the app object. '''
        
        # it is useful to know from where we came
        self.homeDir = os.getcwd()
        
        self.uiType   = None    # ('wx', 'qt', 'curses', 'http', etc.)
        self.uiModule = None
        
        # Initialize UI collections
        self.uiForms = Collection()
        self.uiMenus = Collection()
        self.uiToolBars = Collection()
        self.uiResources = {}
        
        # Initialize DB collections
        self.dbConnectionDefs = {} 

    def _initDB(self):
        ''' Set the available connection definitions for use by the app. '''

        dbConnectionDefs = None
        try:
            globals_ = {}
            execfile("%s/dbConnectionDefs.py" % (self.homeDir,), globals_)
            dbConnectionDefs = globals_["dbConnectionDefs"]
        except:
            dbConnectionDefs = None
        
        if dbConnectionDefs != None and type(dbConnectionDefs) == type(dict()):
            # For each connection type, bind a db() object
            for entry in dbConnectionDefs:
                dbConnectionDefs[entry]["dbObject"] = db.Db()
            print "%s database connection definition(s) loaded." % len(dbConnectionDefs)

        else:
            print "No database connection definitions loaded (dbConnectionDefs.py)"
        
        self.dbConnectionDefs = dbConnectionDefs 
        self.dbDynamicViews = self._getDynamicViews()
                
    def _initUI(self):
        ''' Set the user-interface library for the application. '''
        
        if self.uiType == None:
            # Future: read a config file in the homeDir
            # Present: set UI to wx
            uiType = "wx"
            
            # Now, get the appropriate ui module into self.uiModule
            uiModule = ui.getUI(uiType)
            if uiModule != None:
                self.uiType = uiType
                self.uiModule = uiModule
        else:
            # Custom app code already set this: don't touch
            pass
        
        print "User interface set to %s using module %s" % (self.uiType, self.uiModule)
        
            
    def _getDynamicViews(self):
        dynamicViews = {}
        try:
            dynviewDefs = os.listdir("%s/dynamicViews" % homeDir)
        except:
            dynviewDefs = []
         
        for file in dynviewDefs:
            if file[-3:] == ".py" and file[0:3] == "vr_":
                fileStem = file[:-3]
                try:
                    file = open("./dynamicViews/%s" % file, "r")
                    exec(file) # creates the viewDef variable
                    dynamicViews["%s" % fileStem] = viewDef #viewdef.viewDef
                    dynamicViews["%s" % fileStem]["Id"] = 23
#                    dynamicViews["%s" % fileStem]["Id"] = wx.NewId()
                     
                except KeyError:
                    pass	
        
        return dynamicViews

    def getDynamicViewNameFromId(self, Id):
        dynViewName = None
        for dynview in self.dynamicViews:
            try:
                viewId = self.dynamicViews[dynview]["Id"]
            except KeyError:
                viewId = -1
            if Id == viewId:
                dynViewName = dynview
                break
        return dynViewName
        
