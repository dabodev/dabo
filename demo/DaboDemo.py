#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import platform
import dabo
from dabo.dApp import dApp


def main():
	# The splash screen looks great on Mac/Win, and crappy on Linux.
	# Splash screen is buggy on Mac with the wx 3.0 move, removing it for now
	pltfrm = platform.platform().lower()
	useSplash = "linux" not in pltfrm and "darwin" not in pltfrm
	mfc = "DaboDemo.cdxml"
	if not os.path.exists(os.path.join(os.getcwd(), mfc)):
		mfc = os.path.join(os.getcwd(), os.path.split(sys.argv[0])[0], mfc)

	app = dApp(showSplashScreen=useSplash, splashTimeout=3000,
			MainFormClass=mfc, BasePrefKey="demo.DaboDemo")
	app.setAppInfo("appName", "DaboDemo")
	app.start()


if __name__ == '__main__':
	main()

