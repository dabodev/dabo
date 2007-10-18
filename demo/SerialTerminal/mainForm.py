# -*- coding: utf-8 -*-
"""
File:			mainForm.py

Author:			Nathan Lowrie

Organization:	

Description:	This program is a utility program for debugging different Serial
	Port interfaces like RS-232.  This program allows the The user to enter data
	in various forms such as ASCII and Hex formats to be sent to the terminal
	specified in the connections panel.

Dependencies:	Dabo 		-> http://dabodev.com/
				PySerial	-> http://pyserial.sourceforge.net/
"""

import dabo
import serial
import threading
import time

dabo.ui.loadUI('wx')

from SerialSetupPanel import SerialSetupPanel


class SerialPanel(dabo.ui.dPanel):
	def afterInit(self):
		self.Sizer = dabo.ui.dSizer("horizontal")
		
		########################################################################
		# Add the setup and formatting controls ################################
		vs = dabo.ui.dSizer("vertical")
		vs.DefaultSpacing = 5
		vs.DefaultBorder= 5
		vs.DefaultBorderAll = True
		
		self.pnlSerialSetup = SerialSetupPanel(self, RegID="pnlSerialSetup")
		self.SerialPort = self.pnlSerialSetup.SerialPort
		vs.append(self.pnlSerialSetup, "expand", 0)
		
		formats = ["ASCII", "Hex"]
		
		#set up the input and output format options
		bs = dabo.ui.dBorderSizer(self, "vertical", Caption="Serial Port Setup")
		gs = dabo.ui.dGridSizer(MaxCols=2)
		gs.setColExpand(True, 1)
		
		self.ddInputFormat = dabo.ui.dDropdownList(self, RegID="ddInputFormat", Choices=formats, Value="ASCII")
		self.ddOutputFormat = dabo.ui.dDropdownList(self, RegID="ddOutputFormat", Choices=formats, Value="ASCII")
		
		gs.append(dabo.ui.dLabel(self, Caption="Input Format"), halign="right")
		gs.append(self.ddInputFormat, "expand")
		gs.append(dabo.ui.dLabel(self, Caption="Output Format"), halign="right")
		gs.append(self.ddOutputFormat, "expand")
		
		bs.append1x(gs)
		vs.append(bs, "expand", 0)
		self.Sizer.append(vs, "expand", 0)
		
		########################################################################
		# Add the display controls #############################################
		vs = dabo.ui.dSizer("vertical")
		vs.DefaultSpacing = 5
		vs.DefaultBorder= 5
		vs.DefaultBorderAll = True
		
		#add the serial input command
		bs = dabo.ui.dBorderSizer(self, "vertical", Caption="Serial Input")
		self.txtSerialInput = dabo.ui.dTextBox(self, RegID="txtSerialInput")
		bs.append1x(self.txtSerialInput)
		vs.append(bs, "Expand", 0)
		
		#add the serial transfer viewscreen
		bs = dabo.ui.dBorderSizer(self, "vertical", Caption="Serial Transfer Viewscreen")
		self.edtSerialTransfer = dabo.ui.dEditBox(self, RegID="edtSerialTransfer")
		bs.append1x(self.edtSerialTransfer)
		vs.append1x(bs)
		self.Sizer.append1x(vs)
		
		########################################################################
		# Set up thread to check for data recieved #############################
		self.updateThread = KillableThread(function=self.checkSerialData)
		self.updateThread.start()
	
	def checkSerialData(self):
		if self.SerialPort.isOpen() and self.SerialPort.inWaiting():
			data = self.SerialPort.Read(self.SerialPort.inWaiting()).encode(self.ddOutputFormat.StringValue)
			
			self.edtSerialTransfer.Value += "Recieved: %s\n\n" % (data,)
		
		time.sleep(1)	#wait 1 second so we don't tie the processor
	
	def sendSerialData(self):
		if len(self.txtSerialInput.Value) % 2 and self.ddInputFormat.StringValue == "Hex":	#We will get an error if we don't have an even string length
			self.txtSerialInput.Value = "0" + self.txtSerialInput.Value
		
		try:
			data = self.txtSerialInput.Value.decode(self.ddInputFormat.StringValue)
		except:
			#Error because of non-hex digit
			dabo.ui.info("The input string must be made up of all hex digits.  If you wish to send ASCII data, please switch the input format to ASCII.")
			return
		
		self.SerialPort.write(data)
		
		self.edtSerialTransfer.Value += "Sent: %s\n\n" % (self.txtSerialInput.Value,)
		self.txtSerialInput.Value = ""
	
	
	############################################################################
	# Event Handlers ###########################################################
	def onKeyChar_txtSerialInput(self, evt):
		if evt.keyCode == 13 or evt.keyCode == 372:
			if not self.txtSerialInput.Value == "":
				self.sendSerialData()
	
	def beforeClose(self, evt):
		print "got here"
		self.updateThread.join(self)


class KillableThread(threading.Thread):
	def __init__(self,name='UpdateThread', function=None):
		""" constructor, setting initial variables """
		self._stopevent = threading.Event()
		self.function = function
		threading.Thread.__init__(self,name=name)
	
	def run(self):
		while not self._stopevent.isSet():
			if self.function != None:
				self.function()
	
	def join(self,timeout=None):
		""" Stop the thread and wait for it to end. """
		self._stopevent.set()
		threading.Thread.join(self, timeout)


class mainForm(dabo.ui.dForm):
	def afterInit(self):
		self.Sizer = dabo.ui.dSizer("vertical")
		self.Sizer.append1x(SerialPanel(self))
		self.Sizer.layout()
	
	def initProperties(self):
		self.Caption = "Serial Debugging Terminal"
		self.Size = (500,500)


if __name__ == "__main__":
	app = dabo.dApp()
	app.MainFormClass = mainForm
	app.start()