""" External libraries that can be loaded into Daboized applications.
"""
import os

# OpenFox functions: (FoxPro syntax)
os.environ["OPENFOX_LOADUI"] = "0"
import ofFunctions

from getMouseObject import getMouseObject
