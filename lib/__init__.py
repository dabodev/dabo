""" External libraries that can be loaded into Daboized applications.
"""
import os as __os

# OpenFox functions: (FoxPro syntax)
__os.environ["OPENFOX_LOADUI"] = "0"
import ofFunctions

from ListSorter import ListSorter

