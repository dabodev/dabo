import dabo.dConstants as k

class dMemento(object):
    def __init__(self, vals=None):
        if vals is None:
            self.setMemento({})
        else:
            self.setMemento(vals)

        self.diff = {}


    def setMemento(self, vals):
        self.__snapshot = vals.copy()
        

    def isChanged(self, newvals):
        """ 
        Returns a boolean value, depending on whether or not 
        the passed dictionary of values is identical to the current snapshot.
        """
        return (self.__snapshot != newvals)


    def getOrigVal(self, fld):
        """ Given a field name, returns the values saved in the snapshot """
        ret = None
        if self.__snapshot.has_key(fld):
            ret = self.__snapshot[fld]
        return ret
        
    
    def makeDiff(self, newvals, isNewRecord=False):
        """ 
        The idea here is to create a dictionary containing just the values 
        that have changed in the newvals dict., as compared to the snapshot. 
        Since the purpose of the memento is to compare different states of a
        data record, it is assumed that the keys are always going to be the same
        in both. 
        """
        ret = {}
        for kk, vv in newvals.items():
            if kk == k.CURSOR_MEMENTO:
                # Ignore the mementos
                continue
            if kk == k.CURSOR_NEWFLAG:
                # Ignore the new record flag.
                continue
            # OK, if this is a new record, include all the values. Otherwise, just
            # include the changed ones.
            if isNewRecord or self.__snapshot[kk] != vv:
                ret[kk] = vv
        return ret
