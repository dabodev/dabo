import dabo.dConstants as k

class SqlBuilder:
    """ 
    The following properties are used to create SQL statements
    in a programmatic fashion
    """

    sqlfields = ""
    sqlfrom = ""
    sqlwhere = ""
    sqlgroupby = ""
    sqlorderby = ""
    sqllimit = ""
    defaultLimit = 1000

    def setFieldList(self, fldlist):
        self.sqlfields = fldlist

    def addField(self, fld):
        if self.sqlfields:
            self.sqlfields = ",".join((self.sqlfields, fld))
        else:
            self.sqlfields = fld

    def setFrom(self, fromspec):
        self.sqlfrom = fromspec

    def addFrom(self, fromspec):
        if self.sqlfrom:
            self.sqlfrom = ",".join((self.sqlfrom, fromspec))
        else:
            self.sqlfrom = fromspec

    def setWhere(self, clause):
        self.sqlwhere = clause

    def addWhere(self, clause, andor="and"):
        if self.sqlwhere:
            self.sqlwhere += " " + andor + " " 
        self.sqlwhere += clause

    def setGroupBy(self, grp):
        self.groupby = grp

    def addGroupBy(self, grp):
        if self.sqlgroupby:
            self.sqlgroupby = ",".join((self.sqlgroupby, grp))
        else:
            self.sqlgroupby = grp

    def setOrderBy(self, ord):
        self.sqlorderby = ord

    def addOrderBy(self, ord, desc=0):
        if self.sqlorderby:
            self.sqlorderby = ",".join((self.sqlorderby, ord))
        else:
            self.sqlorderby = ord
        if desc:
            self.sqlorderby += " DESC "

    def setLimit(self, limit):
        self.sqllimit = limit

    def createSQL(self):
        ret = ""
        if not self.sqlfrom: return ret

        if self.sqlfields:
            ret = "select " + self.sqlfields
        else:
            # Default to all fields
            ret = "select *"

        ret += " from " + self.sqlfrom

        if self.sqlwhere:
            ret += " where " + self.sqlwhere
        if self.sqlgroupby:
            ret += " group by " + self.sqlgroupby
        if self.sqlorderby:
            ret += " order by " + self.sqlorderby
        if self.sqllimit:
            ret += " limit " + str(self.sqllimit)
        else:
            ret += " limit " + str(self.defaultLimit)

        return ret

    def executeSQL(self, args=None):
        self.execute(self.createSQL(), args)

