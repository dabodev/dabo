''' dbConnection.py '''

import dbRecordSet

class DbConnection:
    """ Lazy proxy for db connection: from Python Cookbook page 287
    credit: John B. Dell'Aquila """

    def __init__(self, factory, *args, **keywords):
        """ init with factory method to generate DB connection
        (e.g. odbc.odbc, cx_oracle.connect) plus any positional and/or
        keyword arguments required when factory is called."""

        self.__cxn = None
        self.__factory = factory
        self.__args	= args
        self.__keywords = keywords

    def __getattr__(self, name):
        if self.__cxn is None:
            self.__cxn = self.__factory(*self.__args, **self.__keywords)
        return getattr(self.__cxn, name)

    def close(self):
        if self.__cxn is not None:
            self.__cxn.close()
            self.__cxn = None

    def __call__(self, sql, *args, **keywords):
        """ Execute SQL query and return results. Optional Keyword
        args are '%' substituted into query beforehand."""

        cursor = self.cursor()
#		cursor.execute(sql % keywords)
        if len(args) > 0:
            #print args
            cursor.execute(sql % args)
        else:
            cursor.execute(sql)
        
        recordSet = dbRecordSet.DbRecordSet(
            [list(x) for x in cursor.fetchall()],
            [x[0].lower() for x in cursor.description])
        
        return recordSet
