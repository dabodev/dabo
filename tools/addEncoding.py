# -*- coding: utf-8 -*-
import os

utf = "# -*- coding: utf-8 -*-\n"
shebangEnv = "#!/usr/bin/env python"
shebangReplace = """#!/usr/bin/env python
# -*- coding: utf-8 -*-"""

def insertUtf(fname):
	orig = open(fname).read()
	if not utf in orig:
		if orig.startswith(shebangEnv):
			open(fname, "w").write(orig.replace(shebangEnv, shebangReplace))
		else:
			open(fname, "w").write("%s%s" % (utf, orig))
		return 1
	else:
		return 0

### NOTE:
### This must be customized for your directory structure before running!
rootpath = "/Users/ed/projects"
for proj in ("dabo-dev", "daborun", "demo-dev", "ide-dev"):
	reps = 0
	for root, dirs, files in os.walk(os.path.join(rootpath, proj)):
		for f in [ff for ff in files if ff.endswith(".py")]:
			fname = os.path.join(root, f)
			if fname.endswith("/_daborevs/__init__.py"):
				# These are external
				continue
			reps += insertUtf(fname)
	print "Project %s: %s files were modified" % (proj, reps)

