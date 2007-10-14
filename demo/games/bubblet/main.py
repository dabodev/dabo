# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")
from BubbletForm import BubbletForm

def main():
	app = dabo.dApp()
	app.BasePrefKey = "demo.games.Bubblet"
	app.setAppInfo("appName", "Bubblet")
	app.MainFormClass = BubbletForm
	app.start()


if __name__ == "__main__":
	main()
