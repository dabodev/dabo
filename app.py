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

class App(object):
    def setup(self):
        print "app.setup"
    
    def start(self):
        print "app.start"