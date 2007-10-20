#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import platform
import dabo


def main():
	# The splash screen looks great on Mac/Win, and crappy on Linux.
	useSplash = "linux" not in platform.platform().lower()
	mfc = os.path.join(os.path.split(sys.argv[0])[0], "DaboDemo.cdxml")

	app = dabo.dApp(showSplashScreen=useSplash, splashTimeout=3000,
			MainFormClass=mfc, BasePrefKey="demo.DaboDemo")

	app.setAppInfo("appName", "DaboDemo")

	app.start()

	
if __name__ == '__main__':
	main()

