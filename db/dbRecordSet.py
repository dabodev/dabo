''' dbRecordSet.py '''

import dbRecord

class DbRecordSet:
    """ Wrapper for tabular data """

    def __init__(self, tableData, columnNames):
        self.data      = tableData
        self.columns   = columnNames
        self.columnMap = {}

        for name, n in zip(columnNames, xrange(10000)):
            self.columnMap[name] = n

    def __getitem__(self, n):
        return dbRecord.DbRecord(self.data[n], self.columnMap)

    def __setitem__(self, n, value):
        self.data[n] = value

    def __delitem__(self, n):
        del self.data[n]

    def __len__(self):
        return len(self.data)

    def __str__(self):
        return '%s: %s' % (self.__class__, self.columns)

    def append(self, fields=[], values=[]):
        # append method added 12/8/2003
        recordData = []
        for column in self.columns:       
            #recordData = copy.copy(self.data[0])
            if column[0].upper() in ("I", "N"):
                recordData.append(0)
            else:
                recordData.append("")
                
        self.data.append(recordData)
        record = self[len(self.data) - 1]
                
        for column in self.columns:
            try:
                index = fields.index(column)
            except ValueError:
                index = None
                
            if index >= 0:
                # default value present
                exec("record.%s = values[index]" % column)
            else:
                #print "%s" % column, type(eval("record.%s" % column))
                if type(eval("record.%s" % column)) == type(int()):
                    value = 0
                else:
                    value = "''"
                cmd = "record.%s = %s" % (column, value) 
                #print cmd
                exec(cmd)

                
    def sort(self, column=None, descending=False):
        # sort method by pkm on 11/18/2003
        if type(column) == type(int()):
            # column position referenced
            col = column
        else:
            # column name referenced: convert to position
            col = self.columnMap[column]
        
        # build a temp list of the column to sort, sort it, then integrate
        # the rest of the fields and save to self.data:
        tempList = []
        for record in self.data:
            tempList.append([record[col], record])
        tempList.sort()
        
        self.data = []
        for record in tempList:
            self.data.append(record[1])  
        
        if descending == True:
            self.data.reverse()
            
    def seek(self, column=None, value=None):
        # seek method by pkm on 11/18/2003
        
        value = str(value).strip()
        
        if type(column) == type(int()):
            # column position referenced
            col = column
        else:
            # column name referenced: convert to position
            col = self.columnMap[column]
            
        # build a temp list of the column to seek with the length
        # of value, do the seek, and
        # return the index:
        tempList = []
        for record in self.data:
            tempList.append(str(record[col]).strip().upper()[0:len(value)])
        try:
            index = tempList.index(value)
        except:
            index = -1
        return index
