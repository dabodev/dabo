''' dbRecord.py '''


class DbRecord:
    """ Wrapper for data row. Provides access by
    column name as well as position."""

    def __init__(self, rowData, columnMap):
        self.__dict__['_data_'] = rowData
        self.__dict__['_map_']  = columnMap

    def __getattr__(self, name):
        return self._data_[self._map_[name]]

    def __setattr__(self, name, value):
        try:
            n = self._map_[name]
        except KeyError:
            self.__dict__[name] = value
        else:
            self._data_[n] = value

    def __getitem__(self, n):
        return self._data_[n]

    def __setitem__(self, n, value):
        self._data_[n] = value

    def __getslice__(self, i, j):
        return self._data_[i:j]

    def __setslice__(self, i, j, slice):
        self._data_[i:j] = slice

    def __len__(self):
        return len(self._data_)

    def __str__(self):
        return '%s: %s' % (self.__class__, repr(self._data_))


        
