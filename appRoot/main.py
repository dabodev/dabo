''' dabo: main.py
    
    This is a default script, which you should either copy or 
    completely replace for your custom app. It allows you the
    flexibility of choosing whether you want to use the dabo
    framework's app object directly, or perhaps you would rather
    subclass and extend Dabo's app object. 
    
    Start your app with a main.py script like this one, that imports
    an app object and starts the event loop. Don't put much functionality
    here, as Python doesn't compile main scripts. 'Tis just a
    Dabo wrapper...
    
    If you want to not think about anything at all, just copy this
    to the root of your custom application directory.
    
    If you want to go the subclassing route, you'll need to write your
    own customApp.py script, put it in the root of your custom app 
    directory, make sure your app object subclasses dabo's app
    object, and then change the import line to:
    
    import customApp as daboApp
    
    and it should work fine. Unless you really want to extend the app
    object, though, just stick with using the daboApp directly.
    
    Dabo is fun to say!
'''

if __name__ == "__main__":
    import dabo.daboApp as daboApp # dabo must be in PYTHONPATH (hint:site-packages)
    app = daboApp.MainApp()
    app.setup()
    app.MainLoop()
