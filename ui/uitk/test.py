import dabo
import dabo.ui as ui
import dabo.dEvents as dEvents

def testGotFocus(event):
	print "testGotFocus"
	
app = dabo.dApp()
app.UI = 'tk'
app.LogEvents = ["All"]
app.setup()

app.MainFrame.bindEvent(dEvents.GotFocus, testGotFocus)

app.start()
