
import os
import os.path as path
import dabo

daboPath = path.dirname(dabo.__file__)

cmd = "python coverage.py -r"
fileList = []

for dir, subdirs, files in os.walk(daboPath):
	for file in files:
		if file[-3:] == ".py":
			filepath = path.join(dir, file)
			#cmdTemp += " %s" % (filepath,)
			fileList.append(filepath)


cmdTemp = cmd
for x in range(len(fileList)):
	cmdTemp += " %s" % (fileList[x],)
	if (x+1)%100 == 0:
		os.system(cmdTemp)
		cmdTemp = cmd

if len(cmdTemp) > 21:
	os.system(cmdTemp)
