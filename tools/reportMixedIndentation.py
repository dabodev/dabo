#!/usr/bin/env python
import os

culprits = {}
culpritLineCount = 0

for root, dirs, files in os.walk("."):
    for fname in files:
        if fname[-3:] == ".py":
            fullFile = os.path.join(root, fname)
            with open(fullFile) as ff:
                lineNum = 0
                for l in ff.readlines():
                    lineNum += 1
                    l = l.replace("\t", "")
                    if len(l) > 0 and l[0] == " ":
                        culpritLineCount += 1
                        lineNums = culprits.setdefault(fullFile, [])
                        lineNums.append(lineNum)
            if fullFile in culprits:
                print("! => %s (%s)" % (fullFile, len(culprits[fullFile])))

print(
    """
There are %s file(s) with mixed or space-only indentation, and a total of
%s line(s). We'll now cycle through the lines in vim, one by one, so that 
you may edit them as needed. Due to this script being kind of stupid, you
shouldn't add or remove lines in the files, just fix the problem.
"""
    % (len(culprits), culpritLineCount)
)

print("\nContinue? (y/[N])", end=" ")
ret = input()
if ret.lower() == "y":
    for fileName, lines in list(culprits.items()):
        for line in lines:
            os.system("vi %s +%s" % (fileName, line))
    #    print "%s: %s" % (k, v)
