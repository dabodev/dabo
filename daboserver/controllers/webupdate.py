import logging
import simplejson
import os
import tempfile
from zipfile import ZipFile
from dabo.lib.xmltodict import xmltodict, dicttoxml

from pylons.decorators import jsonify
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from daboserver.lib.base import BaseController, render
from daboserver import model
from daboserver.model import Versions

log = logging.getLogger(__name__)



class WebupdateController(BaseController):
	""" Check for Web Update changes, and download the files when requested."""
	_deletedFilesName = "DELETEDFILES"
	
	
	@jsonify
	def xxx(self, val):
		return "You typed: %s" % val


	@jsonify
	def check(self, val):
		return Versions.changes(val)


	@jsonify
	def latest(self):
		return Versions.latest()


	def checkNoJson(self, val):
		chgs = Versions.changes(val)
		return str(chgs)


	@jsonify
	def changelog(self):
		return Versions.getLog()


	def files(self, val):		
		currdir = os.getcwd()
		chgs = Versions.changes(val)["files"]
		delfiles = []
		goodPrefixes = ("dabo", "demo", "ide")
		basepath = "%s%s" % (Versions.reposBase, Versions.repos)
		os.chdir(basepath)
		fd, tmpname = tempfile.mkstemp(suffix=".zip")
		os.close(fd)
		z = ZipFile(tmpname, "w")
		zcount = dcount = 0
		for chg in chgs:
			chgtype, pth = chg.split()
			try:
				prfx, fname = pth.split("/", 1)
			except ValueError:
				# A file in the trunk; ignore
				continue
			if prfx not in goodPrefixes:
				# Not a web update project
				continue
			if "D" in chgtype:
				delfiles.append(pth)
				dcount += 1
				continue
			# 'pth' must be str, not unicode
			if os.path.isfile(pth):
				z.write(str(pth))
				zcount += 1
		if dcount:
			# Add the file with deletion paths
			fd, tmpdel = tempfile.mkstemp()
			os.close(fd)
			file(tmpdel, "w").write("\n".join(delfiles))
			z.write(tmpdel, self._deletedFilesName)
			os.remove(tmpdel)

		z.close()
		response.headers['content-type'] = "application/x-zip-compressed"
		ret = file(tmpname).read()
		os.remove(tmpname)
		os.chdir(currdir)
		return ret
		
