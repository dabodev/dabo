''' Dabo: A Framework for developing data-driven business applications
        by Paul McNett (p@ulmcnett.com)

    Dabo is for developing multi-platform database business applications -
    you know, applications that need to connect to a database server (MySQL,
    Oracle, MS-SQL, whatever), get recordsets of data based on criteria 
    set by the user, provide easy ways to edit and commit changes to the 
    data, and to report on the data.
    
    For basic, easy use that hopefully satisfies 80% of your needs, you 
    simply create/edit data definition files that Dabo uses to dynamically
    create things like menus, edit forms, data browsing grids, etc.
    
    So, the basic idea is that you have a functional, working, albeit basic
    application up and running very quickly, and you can then spend time 
    getting all the fancy bells and whistles implemented. Keep things as 
    simple as possible though, while still fulfilling your customer's 
    specifications. Simplicity is the better part of elegance.
    
    Dabo is fun to say, which is enough justification for its name, but 
    perhaps it could stand for:
        Database Application Business Objects
        Database Application Builder O (Just think, it could have been ActiveO... <g>)
        Object oriented Business Application Development (but OBAD sounds so bad)
        
    Dabo has a few parts. First, there is this package, the Dabo framework. Your
    applications will be based on the classes and modules herein. There are several
    Dabo packages available:
        
        Dabo:       This package, the base framework. Other packages require this
                    to be installed, but Dabo doesn't care whether the other packages
                    are installed.
        
        DaboWiz:    Wizards for common tasks, such as setting up directories for a
                    new project based on Dabo, and for setting up dynamic view
                    definitions, dynamic menu items, etc. The wizards take the 
                    drudgery out of setting up your data definitions: they pretty
                    much do it for you!
                    
        DaboDemo:   A demonstration application that you can run on your machine
                    to get a feel for Dabo's capabilities. You can then take a
                    look at the DaboDemo's source code, which is mostly made up
                    of data definition scripts instead of actual source code, to
                    see what makes it tick. You can experiment with a change here
                    or there, learning how to use Dabo in a hands-on way.
    
    The Dabo framework will have to be distributed to your client's machine(s),
    along with your project-specific data definitions and (if applicable), your
    subclasses of the Dabo classes and additional Python scripts, if any. There 
    are ways to do runtime deployment via installers that take the complexity 
    out of this, but that is outside the scope of Dabo itself, and you'll use
    a different method for each target platform.
    
    To run Dabo, and apps based on Dabo, you need:
        + Python 2.3 or higher
        
        + wxPython 2.4.2.4 or higher, which has a dependency on:
            + wxWindows 2.4.2.4 or higher
        
        + Windows 98SE or higher
        + Macintosh OSX 10.2 or higher
        + Linux 2.4 with X11 running
        
        + Access to some sort of database server, along with the 
        appropriate Python driver(s) installed. For example, for
        MySQL you'll need to have the MySQL client libraries
        installed, as well as the MySQLDb Python module. (Dabo
        does not use ODBC: it connects directly using the Python
        DB API coupled with the individual database drivers. This
        is, at the same time, less flexible, tougher to get started
        with, but more capable, more multi-platform, and better 
        performing, than ODBC is.) 
    
    How you get started is pretty much up to you. Look at the demo.
    Run a wizard. Hand-edit the data definition files.
    
    ToDo: pointers to get started.
                            
'''