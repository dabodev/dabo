# -*- coding: utf-8 -*-
import os
import inspect
import dabo

def main():
	app = dabo.dApp()
	curdir = os.getcwd()
	# Get the current location's path
	fname = inspect.getfile(main)
	pth = os.path.split(fname)[0]
	if pth:
		# Switch to that path
		os.chdir(pth)
	app.MainFormClass = "PrefEditor.cdxml"
	app.start()
	
	# Return to the original location
	os.chdir(curdir)
	

if __name__ == '__main__':
	main()
