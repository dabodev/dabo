''' dProgressDialog

    (Barely started - don't use)
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
        wx.Dialog.__init__(self,parent,-1,caption,style=wx.NO_BORDER)

        self.Centre(wx.BOTH)
        
        self.status = wx.StaticText(self,-1,'',pos=(0,100))

        # Set up event handler for any worker thread results
        EVT_RESULT(self,self.OnResult)

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

def displayAfterWait(parentWindow, seconds, func):
    # Start <func>, but if it hasn't finished in <seconds>, display a
    # 'please wait' dialog box.
    window = dProgressDialog(parentWindow, "Please Wait...", func, seconds)
    window.ShowModal()
    response = window.response
    window.Destroy()
    return response
