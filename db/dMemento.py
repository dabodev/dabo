import dabo.dConstants as k

class dMemento(object):
    __snapshot = {}
    
    def __init__(self, vals=None):
        if vals is None:
            self.setMemento({})
        else:
            self.setMemento(vals)

        self.diff = {}


    def setMemento(self, vals):
        self.__snapshot = vals.copy()
        

    def isChanged(self, newvals):
        ''' Return True if the snapshot does not match the passed dictionary.
        '''
        return (self.__snapshot != newvals)


    def getOrigVal(self, fld):
        ''' Get the original value of the passed field name.
        '''
        try:
            return self.__snapshot[fld]
        except KeyError:
            return None
        
        
    def getSnapshot(self):
        """ Just for debugging! """
        return self.__snapshot
        
    
    def makeDiff(self, newvals, isNewRecord=False):
        ''' Get the changed values compared with the snapshot.
         
        Create a dictionary containing just the values that have changed in the
        newvals dict., as compared to the snapshot.
         
        Since the purpose of the memento is to compare different states of a
        data record, it is assumed that the keys are always going to be the same
        in both. 
        '''
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
