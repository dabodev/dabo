# -*- coding: utf-8 -*-
"""
dabo.biz : Dabo Business Objects (bizobjs)

Ed Leafe writes:

Bizobjs are objects whose purpose is to encapsulate
business rules about data, and which also serve as the glue
between the GUI controls and the backend cursors. In nearly
all forms, there is a primary table that is the 'focus' of
the form. There can be other tables that are related to the
primary one; usually they are related in some sort of
parent-child relation. Therefore, each bizobj can have
zero-to-many child bizobjs. Each bizobj also has a reference
to a cursor object. The cursor objects will encapsulate the
data access. The bizobj will have a property that will be
used to identify it, along with its cursor, for resolving
ControlSource references in the controls.

So, dabo.biz sits in between dabo.db and dabo.ui

"""
from dBizobj import dBizobj
from RemoteBizobj import RemoteBizobj

from dAutoBizobj import dAutoBizobj
from dAutoBizobj import autoCreateTables
from dAutoBizobj import setupAutoBiz
from dAutoBizobj import bizs
