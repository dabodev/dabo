''' dProgressDialog

(Barely started - don't use)

Ed writes:
> - The whole threading issue. Since killing threads is not
> feasible, we should look at what we want to accomplish.
> Ideally, we want to avoid locking the UI by a runaway query
> process. Given that, we should rewrite all potentially
> runaway calls in the UI to the bizobj so that we begin by
> creating a separate thread for the bizobj call. The UI then
> starts a timer, which will display a "Please Wait" message
> with a Cancel button after a given time (say, 1 second). If
> the user clicks Cancel, the UI continues on its way. Further
> interaction with the bizobj will not be possible until the
> bizobj process returns, since its state will be undefined. We
> then need a UI-level flag to be set to indicate this state.
> The bizobj returns from its process by emitting an event; the
> UI will have to trap that event, and if it is received when
> the flag is set, issue a call to the bizobj to reset itself
> back to its last known state. When the bizobj completes that,
> the UI clears the 'unstable' flag. This will require, of
> course, that the bizobj save its state before each call, and
> be able to restore that state when asked. None of this will
> eliminate problems caused by runaway queries, but will at
> least allow the UI to remain responsive, reducing the chance
> that the user will three-finger it.
'''
import time
from threading import *
import wx
import time

ID_CANCEL = wx.NewId()
EVT_RESULT_ID = wx.NewId()

def EVT_RESULT(win, func):
    win.Connect(-1, -1, EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
    ''' Simple event to carry arbitrary result data.
    '''

    def __init__(self, response):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.response = response

# Thread class that executes processing
class WorkerThread(Thread):
    def __init__(self, notify_window, func):
        Thread.__init__(self)
        self._notify_window = notify_window
        self._want_abort = 0
        self.setDaemon(1)
        self._func = func
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()

    def setFunc(self, func):
        self._func = func
        
    def run(self):
        response = self._func()
        # Done, send notify:
        wx.PostEvent(self._notify_window,ResultEvent(response))

# GUI Frame class that spins off the worker thread
class dProgressDialog(wx.Dialog):
    def __init__(self, parent, caption="Progress Dialog", func=None, wait=0):
        wx.Dialog.__init__(self,parent,-1,caption,style=0)

        self.Centre(wx.BOTH)
        self.SetSize((300,100))
        
        self.status = wx.StaticText(self,-1,'',pos=(0,100))

        wx.EVT_CLOSE(self, self.OnClose)
        
        # Set up event handler for any worker thread results
        EVT_RESULT(self, self.OnResult)

        # And indicate we don't have a worker thread yet
        self.worker = None
        self.response = None
        
        self.start(func)
        
    def start(self, func):
        if func:
            self.status.SetLabel('Please Wait...')
            self.worker = WorkerThread(self, func)
        else:
            print "configure caller to send func parameter"

    def OnResult(self, event):
        self.response = event.response
        self.Hide()
        
    def OnClose(self, event):
        # Don't let the window close.
        pass

def displayAfterWait(parentWindow, seconds, func):
    # Start <func>, but if it hasn't finished in <seconds>, display a
    # 'please wait' dialog box.
    window = dProgressDialog(parentWindow, "Please Wait...", func, seconds)
    window.ShowModal()
    response = window.response
    window.Destroy()
    return response
