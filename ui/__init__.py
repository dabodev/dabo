''' dabo.ui : This is Dabo's user interface layer which is the topmost layer.
              The UI will instantiate forms which contain bizobj's (dabo.biz)
              and the bizobj's will in turn communicate with the underlying
              db, abstracted with dabo.db.

              We've left it open for the possibility of using differing ui
              libraries, although wxPython is what we are starting with and
              may end up using exclusively.

              Qt is also a slick ui, and as dabo catches on someone may wish
              to figure out how to implement a PyQt ui.

              Curses, if someone is interested in doing it, would provide a
              text-only ui which could actually be very useful for industrial
              or server type applications - something that requires a ui but
              doesn't require it to look slick and possibly requires that 
              a GUI windowing system not be installed.

              Anyway, for now, all the ui development is in dabo.ui.uiwx.

              Each ui method uses common names for widgets, even though the
              actual implementation of them will vary wildly. The ui widget
              names I propose are:

                dForm
                dPageFrame
                dPage
                dGrid
                dColumn
                dTextBox
                dEditBox
                dSpinner
                dOptionGroup
                dCheckBox
                dCommandButton
                dMenu
                dToolBar
                dStatusBar
                             
'''
from dActionList import dActionList

# Module factory function: generically return the 
# proper module depending on the passed uiType.
def getUI(uiType):
    prefix = 'ui'
    try:
        exec("import %s%s as uiModule" % (prefix, uiType))
        return uiModule
        
    except ImportError:
        return None

def loadUI(uiType):
    prefix = 'ui'
    exec("from %s%s import *" % (prefix, uiType), globals())
        
# TEMPORARY!!!!! Just to get the wx stuff working!
# This will load uiwx into the global namespace dabo.ui.
loadUI('wx')

