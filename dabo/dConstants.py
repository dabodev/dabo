# -*- coding: utf-8 -*-
"""dConstants.py"""

# Return values for most operations
# FILE_OK = 0
# FILE_CANCEL = -1
# FILE_NORECORDS = -2
# FILE_BOF = -3
# FILE_EOF = -4

# Return values for updates to the database
# UPDATE_OK = 0
# UPDATE_NORECORDS = -2

# Return values from Requery
# REQUERY_SUCCESS = 0
# REQUERY_ERROR = -1

# Referential Integrity constants
REFINTEG_IGNORE = 1
REFINTEG_RESTRICT = 2
REFINTEG_CASCADE = 3

# Constants specific to cursors
CURSOR_MEMENTO = "dabo-memento"
CURSOR_NEWFLAG = "dabo-newrec"
CURSOR_TMPKEY_FIELD = "dabo-tmpKeyField"
CURSOR_FIELD_TYPES_CORRECTED = "dabo-fieldTypesCorrected"

DLG_OK = 0
DLG_CANCEL = -1
DLG_YES = 2
DLG_NO = -2

# Flag to indicate that field validation was skipped
BIZ_DEFAULT_FIELD_VALID = "Dabo default field validation".split(" ")
