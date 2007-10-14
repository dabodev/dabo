# -*- coding: utf-8 -*-
"""
File:			serialSetupPanel.py

Author:			Nathan Lowrie

Organization:	

Description:	This file contains a Panel that includes Dabo widgets for setting
	up and configuring a serial port.  The serial port object is provided in the 
	panel.  Each control is also given a RegID incase you need to access them
	for things like restricting baudrate choices.

Dependencies:	Dabo 		-> http://dabodev.com/
				PySerial	-> http://pyserial.sourceforge.net/
"""

import dabo
import serial


dabo.ui.loadUI('wx')

#A Note about the serial setup Panel.  I broke it off from the others because this
#Panel has the potential for reuse.  You can stick it in other applications without
#having to do any redesign or changing of the code.
class SerialSetupPanel(dabo.ui.dPanel):
	def afterInit(self):
		self.Sizer = dabo.ui.dSizer("vertical")
		
		#Set up the Control Panel
		bs = dabo.ui.dBorderSizer(self, "vertical", Caption="Serial Port Setup")
		gs = dabo.ui.dGridSizer(MaxCols=2)
		gs.setColExpand(True, 1)
		
		#choices for the dropdown list
		self.buadrateList = ('50', '75', '110', '134', '150', '200', '300', '600', '1200', '1800', '2400', '4800', '9600', '19200', '38400', '57600', '115200')
		self.bytesizeList = ('5', '6', '7', '8')
		self.parityList = ('None', 'Even', 'Odd')
		self.stopbitsList = ('1', '2')
		
		self.ddSerialPort = dabo.ui.dDropdownList(self, RegID="ddSerialPort", Choices=self.getAvailablePorts(), PositionValue=0)
		self.ddSerialBaudrate = dabo.ui.dDropdownList(self, RegID="ddSerialBaudrate", Choices=self.buadrateList, PositionValue=12)
		self.ddSerialBytesize = dabo.ui.dDropdownList(self, RegID="ddSerialBytesize", Choices=self.bytesizeList, PositionValue=3)
		self.ddSerialParity = dabo.ui.dDropdownList(self, RegID="ddSerialParity", Choices=self.parityList, PositionValue=0)
		self.ddSerialStopbits = dabo.ui.dDropdownList(self, RegID="ddSerialStopbits", Choices=self.stopbitsList, PositionValue=0)
		self.chkSerialXonXoff = dabo.ui.dCheckBox(self, RegID="chkSerialXonXoff", Caption="Enable Xon/Xoff flow control")
		self.chkSerialHardware = dabo.ui.dCheckBox(self, RegID="chkSerialHardware", Caption="Enable Hardware flow control")
		self.txtSerialTimeout = dabo.ui.dTextBox(self, RegID="txtSerialTimeout")
		
		gs.append(dabo.ui.dLabel(self, Caption="Port"), halign="right")
		gs.append(self.ddSerialPort, "expand")
		gs.append(dabo.ui.dLabel(self, Caption="Baudrate"), halign="right")
		gs.append(self.ddSerialBaudrate, "expand")
		gs.append(dabo.ui.dLabel(self, Caption="Bytesize"), halign="right")
		gs.append(self.ddSerialBytesize, "expand")
		gs.append(dabo.ui.dLabel(self, Caption="Parity"), halign="right")
		gs.append(self.ddSerialParity, "expand")
		gs.append(dabo.ui.dLabel(self, Caption="Stop Bits"), halign="right")
		gs.append(self.ddSerialStopbits, "expand")
		gs.append(dabo.ui.dLabel(self, Caption="Xon/Xoff control"), halign="right")
		gs.append(self.chkSerialXonXoff, "expand")
		gs.append(dabo.ui.dLabel(self, Caption="Hardware control"), halign="right")
		gs.append(self.chkSerialHardware, "expand")
		gs.append(dabo.ui.dLabel(self, Caption="Timeout (ms)"), halign="right")
		gs.append(self.txtSerialTimeout, "expand")
		
		bs.append1x(gs)
		self.Sizer.append(bs, "expand", 0)
		
		self.ddSerialPort.PositionValue = 0	#The value was coming up a None declaring it during instansiation, so this is here.
		
		self._serialPort = serial.Serial()
		self._serialPort.port = self.ddSerialPort.StringValue
		self._serialPort.open()
	
	
	def getAvailablePorts(self):
		serialPort = serial.Serial()
		serialList = []
		
		for x in xrange(9):
			try:
				serialPort.port = x
				serialPort.open()
			except serial.SerialException:
				pass
			else:
				serialList.append(serial.device(x))
		
		serialPort.close()
		
		if len(serialList) == 0:
			raise serial.SerialException, "There are no serial ports on this computer or all serial ports are in use."
		
		return serialList
	
	
	############################################################################
	# Event Handlers ###########################################################
	def onHit_ddSerialPort(self, evt):
		self.SerialPort.port = self.ddSerialPort.StringValue
	
	def onHit_ddSerialBaudrate(self, evt):
		self.SerialPort.baudrate = self.ddSerialBaudrate.StringValue
	
	def onHit_ddSerialBytesize(self, evt):
		self.SerialPort.bytesize = int(self.ddSerialBytesize.StringValue)
	
	def onHit_ddSerialParity(self, evt):
		self.SerialPort.parity = self.ddSerialParity.StringValue[0]
	
	def onHit_ddSerialStopbits(self, evt):
		self.SerialPort.stopbits = int(self.ddSerialStopbits.StringValue)
	
	def onHit_chkSerialXonXoff(self, evt):
		self.SerialPort.xonxoff = self.chkSerialXonXoff.Value
	
	def onHit_chkSerialHardware(self, evt):
		self.SerialPort.rtscts = self.chkSerialHardware.Value
	
	def onHit_txtSerialTimeout(self, evt):
		if len(self.txtSerialTimeout.Value) > 0:
			self.SerialPort.timeout = int(self.txtSerialTimeout.Value)
		else:
			self.SerialPort.timeout = None
	
	
	############################################################################
	# Property methods and declarations ########################################
	def _getSerialPort(self):
		return self._serialPort
	
	def _setSerialPort(self, val):
		if isinstance(val, serial.Serial):
			self._serialPort = val
		else:
			raise TypeError, "Serial port must by of type serial.Serial"
			
	
	SerialPort = property(_getSerialPort, _setSerialPort, None,
		_("Serial Port object that is configured by the panel (serial.Serial)"))
