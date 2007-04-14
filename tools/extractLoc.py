""" This script is designed to scan source directories and update the MySQL database
containing translation data on dabodev.com.
"""
import os
import popen2
import MySQLdb

### NOTE: you must get these values from a Dabo administrator before 
###   getting access to the database
db=MySQLdb.connect(host="XXX", user="XXX", passwd="XXX", 
		db="XXX")
crs = db.cursor(MySQLdb.cursors.DictCursor)


def processText(txt, proj, pth, fname, xtraPth):
	print "** PROCESSING:", fname
	updated = inserted = 0
	# Each extracted string starts with '#: ', followed by the file and line
	# number. The first element is the generated header, so discard that.
	sections = txt.split("#: ")[1:]
	for section in sections:
		# Each section looks like this:
		#--------------------------
		# dTextBox.py:442
		# msgid ""
		# "Position of the beginning of the selected text. If no text is\n"
		# "\t\t\tselected, returns the Position of the insertion cursor.  (int)"
		# msgstr ""
		#--------------------------
		
		# First, split off the 'msgstr' line
		sect = section.split("msgstr \"\"")[0]
		
		try:
			info, locString = sect.split("\nmsgid ")
			junk, linenum = info.split(":")
		except ValueError:
			# This can happen when a string appears multiple times in a file
			continue
		
		cleanLocString = cleanup(locString)
		xtraSplit = os.path.split(xtraPth)[0]
		# See if that string already exists
		sql = """select pkid from originalstrings where cproject = %s
				and cdirectory = %s
				and cfilename = %s
				and nline = %s
				and tstring = %s"""
		res = crs.execute(sql, (proj, xtraSplit, fname, linenum, cleanLocString))
		if res:
			# Update! Only set the first such occurrence to not deleted
			# (there should only be one, anyway!
			recs = crs.fetchall()
			for rec in recs:
				crs.execute("""update originalstrings set ldeleted=0
						where pkid = %s""", rec["pkid"])
				updated += 1
				break
		else:
			sql = """insert into originalstrings (cproject, cdirectory, 
				cfilename, nline, ldeleted, tstring) VALUES (%s, %s, %s, %s, %s, %s)"""
			crs.execute(sql, (proj, xtraSplit, fname, linenum, 0, cleanLocString))
			inserted += 1
	return (updated, inserted)


def cleanup(val):
	"""Remove the gettext markup from the string."""
	lns = val.splitlines()
	newlns = []
	for ln in lns:
		if ln.startswith("\"") and ln.endswith("\""):
			ln = ln[1:-1]
		if ln.endswith("\\n"):
			ln = ln[:-2]
		newlns.append(ln)
	return "\n".join(newlns)


def processLoc(proj, drct, xtra=None):
	if xtra is None:
		pth = drct
		xtra = ""
	else:
		pth = os.path.join(drct, xtra)
	flist = os.listdir(pth)
	updated = inserted = 0
	for fname in flist:
		if fname.startswith("."):
			# Hidden file; skip
			continue
		fullname = os.path.join(pth, fname)
		newXtra = os.path.join(xtra, fname)
		if os.path.isdir(fullname):
			upd, ins = processLoc(proj, drct, newXtra)
			updated += upd
			inserted += ins
		else:
			if fname.endswith(".py"):
				out, inn, err = popen2.popen3("pygettext.py -a -o - %s" % fullname)
				upd, ins = processText(out.read(), proj, pth, fname, newXtra)
				updated += upd
				inserted += ins
	return (updated, inserted)


def main():
	# Mark the strings as deleted, in case they no longer exist
	crs.execute("update originalstrings set ldeleted = 1")
	
	### NOTE: This must be configured with your local paths
	projects = {"dabo": "/path/to/dabo/",
			"ide": "/path/to/ide/",
			"demo": "/path/to/demo/"}
	for project, drct in projects.items():
		upd, ins = processLoc(project, drct)
		print 
		print """Project %(project)s: 
	%(ins)s entries added
	%(upd)s entries updated""" % locals()
		print
		print
	

if __name__ == "__main__":
	main()