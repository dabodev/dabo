import os

script_dir = os.path.join(os.getcwd(), __file__)
dabo_dir = os.sep.join(script_dir.split(os.sep)[:-2])

for root, dirs, files in os.walk(dabo_dir):
	for dirname in dirs:
		if dirname == "test":
			for fname in os.listdir(os.path.join(root, dirname)):
				if fname[-3:] == ".py" and fname[0:5] == "test_":
					print "\n==========================================="
					print "Running test: %s" % fname
					os.system("python %s" % os.path.join(root, dirname, fname))


