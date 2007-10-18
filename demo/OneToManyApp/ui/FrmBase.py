# -*- coding: utf-8 -*-

import dabo.ui
import dabo.lib.datanav2 as datanav


class FrmBase(datanav.Form):

	def initProperties(self):
		self.super()
		self.AddChildEditPages = False
		self.RequeryOnLoad = False
		self.Icon = "daboIcon.ico"

