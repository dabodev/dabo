import dabo
import dabo.ui as ui
import dEvents

def testGotFocus(event):
	print "testGotFocus"
	
	
app = dabo.dApp()
app.UI = 'tk'
app.setup()
app.MainFrame.LogEvents = ["All"]

#app.MainFrame.bindEvent(dEvents.GotFocus, testGotFocus)

app.start()
