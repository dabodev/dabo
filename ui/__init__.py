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

              Anyway, for now, all the ui development is in dabo.ui.wx.

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

# When the ui module is imported, I want to check for the existence of 
# a global variable, 'uiType', that specifies which ui is going to be
# used. This global will have been set already, presumably. At the moment,
# I have no idea where this will get set (main.py of the client application?)
# and I don't know how to set a global variable. For now, bring the ui.wx
# module into the global namespace of the ui module, but in the future we'll
# want to make this dynamic.
import wxDabo as uiModule
#import curses as uiModule
#import qt as uiModule

# Now, whatever the uiType, it's module is in uiModule. Import the dWidgets
# into the dabo.ui namespace
dApp = uiModule.dApp()
from uiModule import dForm
from uiModule import dPageFrame
from uiModule import dPage
from uiModule import dGrid
from uiModule import dColumn
from uiModule import dTextBox
from uiModule import dEditBox
from uiModule import dSpinner
from uiModule import dOptionGroup
from uiModule import dCheckBox
from uiModule import dCommandButton
from uiModule import dMenu
from uiModule import dToolBar
from uiModule import dStatusBar
