#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import inspect

from .. import ui
from ..application import dApp


def main():
    app = dApp(BasePrefKey="PrefEditor", MainFormClass="PrefEditor.cdxml")
    curdir = os.getcwd()
    # Get the current location's path
    fname = os.path.abspath(inspect.getfile(main))
    pth = os.path.dirname(fname)
    # Switch to that path
    os.chdir(pth)
    app.start()

    # Return to the original location
    os.chdir(curdir)


if __name__ == "__main__":
    main()
