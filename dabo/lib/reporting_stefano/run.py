# -*- coding: utf-8 -*-
import os
import os.path
import sys

from . import report
from . import serialization

if __name__ == "__main__":
    if len(sys.argv) > 1:
        for reportForm in sys.argv[1:]:
            output = "./%s.pdf" % os.path.splitext(reportForm)[0]
            print("Creating %s from report form %s..." % (output, reportForm))
            reportObj = serialization.deserialize(reportForm, report.Report)
            reportObj.evaluate({})
            reportObj.write(output, reportObj.getTestCursor())
    else:
        print("Usage: reportWriter <specFile> [<specFile>...]")
