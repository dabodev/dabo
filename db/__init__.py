''' dabo.db : The lowest tier, db access. This is where the communication
              to and from the backend database happens, and cursors get
              generated to be manipulated by the bizobj's in dabo.biz
'''

# When someone does a 'import dabo.db', what they really want is the
# stuff inside db.py in the dabo.db module
from db import Db
