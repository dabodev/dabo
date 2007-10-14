#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import platform
import inspect
import dabo

def main():
	# The splash screen looks great on Mac/Win, and crappy on Linux.
	useSplash = "linux" not in platform.platform().lower()
	app = dabo.dApp(showSplashScreen=useSplash, splashTimeout=3000)
	curdir = os.getcwd()
	# Get the current location's path
	fname = inspect.getfile(main)
	pth = os.path.split(fname)[0]
	if pth:
		# Switch to that path
		os.chdir(pth)
	app.MainFormClass = "DaboDemo.cdxml"
	app.BasePrefKey = "demo.DaboDemo"
	app.start()
	
	# Return to the original location
	os.chdir(curdir)
	

if __name__ == '__main__':
	main()
