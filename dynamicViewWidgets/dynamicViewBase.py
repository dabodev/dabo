''' dynamicViewBase.py

Base classes for implementing dynamic recordsets.

Dabo. '''

import time

class DynamicView(object):
    ''' dynamicViewWidgets.dynamicViewBase.DynamicView()
    
    Logic for creating the dynamic view 
    from a given DynamicViewDef 
    
    Call the constuctor, set the clauses, and bind the
    result of viewRequery() to a varioable, which is 
    your recordset.
    
    Example: 
        view = dynamicViewBase.DynamicView("vr_invcats")
        view.whereClause = "cdescrp like '%baster%'"
        recordSet = DynamicView("vr_invcats")
    
    The dynamicViewDef is a dictionary that describes the data,
    and probably resides as a Python file in <daboRoot>/dynamicViews/.
    
    Dabo.
    '''
    
    def __init__(self,  dynamicViewDef=None,
                        fromClause=None,
                        whereClause=None,
                        groupClause=None,
                        orderClause=None,
                        limitClause=None):
        object.__init__(self)
        
        self.dynamicViewDef = dynamicViewDef
        self.fromClause  = fromClause
        self.whereClause = whereClause
        self.groupClause = groupClause
        self.orderClause = orderClause
        self.limitClause = limitClause

                
    def viewRequery(self, sql=None, dbc=None):
        ''' DynamicView.viewRequery(sql=None) -> dbconnect.dbRecordSet() 
        
            If sql is not passed, it will be generated based on the
            current clause values before doing the requery. This allows
            the users of this class to do a 3-step of getting the sql,
            tweaking it, and then sending it back for the requery, while
            still retaining the easy default of simply using the auto-
            generated sql without the need for additional calls.
        '''
        
        if sql == None:
            self.lastSQL = self.getSQL()
        else:
            self.lastSQL = sql
   
        beg = time.time()
        self.delta = dbc.dbRecordSet(self.lastSQL)
        end = time.time()
        
        self.lastQueryTime = round(end-beg,3)
        self.lastQueryTally = len(self.delta)
        
        return self.delta

        
    def getSQL(self):
        ''' DynamicView.getSQL() -> string '''

        sql =   "  %s%s%s%s%s%s" % (
                    self._getFieldClause(),
                    self._getFromClause(), 
                    self._getWhereClause(),
                    self._getGroupClause(),
                    self._getOrderClause(), 
                    self._getLimitClause())
        return sql
        
        
    def _getFromClause(self):
        ''' DynamicView._getFromClause() -> string '''
        
        if self.fromClause == None or len(self.fromClause) == 0:
            try:
                clause = self.dynamicViewDef["fromClause"]
            except KeyError:
                clause = None
        else:
            try:
                clause = ''.join([self.dynamicViewDef["fromClause"], "\n  ", self.fromClause])
            except KeyError:
                clause = None
                
        if clause == None or len(clause) == 0:
            clause = ""
        else:
            clause = "    from %s\n" % clause
        
        return clause
        
        
    def _getWhereClause(self):
        ''' DynamicView._getWhereClause() -> string '''
        
        if self.whereClause == None or len(self.whereClause) == 0:
            try:
                clause = self.dynamicViewDef["whereClause"]
            except KeyError:
                clause = None
        else:
            try:
                clause = ''.join([self.whereClause, "\n     AND ", self.dynamicViewDef["whereClause"]])
            except KeyError:
                clause = self.whereClause

        if clause == None or len(clause) == 0:
            clause = ""
        else:
            clause = "   where %s\n" % clause
        
        return clause
        
        
    def _getGroupClause(self):
        ''' DynamicView._getGroupClause() -> string '''
        
        if self.groupClause == None or len(self.groupClause) == 0:
            try:
                clause = self.dynamicViewDef["groupClause"]
            except KeyError:
                clause = None
        
        if clause == None or len(clause) == 0:
            clause = ""
        else:
            clause = "   group by %s\n" % clause
        
        return clause
            
        
    def _getOrderClause(self):
        ''' DynamicView._getOrderClause() -> string '''
        
        if self.orderClause == None or len(self.orderClause) == 0:
            try:
                clause = self.dynamicViewDef["orderClause"]
            except KeyError:
                clause = None
                
        if clause == None or len(clause) == 0:
            clause = ""
        else:
            clause = "   order by %s\n" % clause

        return clause
        

    def _getLimitClause(self):
        ''' DynamicView._getLimitClause() -> string '''
        
        if self.limitClause == None or len(self.limitClause) == 0:
            try:
                clause = self.dynamicViewDef["limitClause"]
            except KeyError:
                clause = None
                
        if clause == None:
            clause = ""
        else:
            clause = "   limit %s\n" % clause

        return clause
        
            
    def _getFieldClause(self):
        ''' DynamicView._getFieldClause() -> string '''
                    
        clause = ""
        
        try:
            for field in self.dynamicViewDef["fields"]:
                if len(clause) == 0:
                    prefix = "select "
                else:
                    prefix = ",\n         "
                
                try:
                    clause = ''.join((clause, prefix, field["select"], 
                                    " as ", field["name"]))
                except KeyError:
                    # Something is incorrect in this field def. Skip and move on.
                    pass
            
            clause = ''.join((clause, '\n'))
                    
        except KeyError:
            clause = None

        return clause
        

if __name__ == "__main__":
    views = DynamicViews()
    views["vr_invmast"] = DynamicViewDef()
    views["vr_invmast"]["selectClause"] = "invmast.iid as iid"
    print views
