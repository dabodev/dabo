# -*- coding: utf-8 -*-
from dabo.base_object import dObject
from dabo.localization import _


class dTable(dObject):
    """
    This class is used to hold information about a table so it can
    be created on any database.

    For example:

        To define a temporary table named 'mytemp' that has ? fields,
        where the fields are:

            ========  ======================
            field 1:  'theid', it is an autoincrementing field that uses a 2 byte integer
            field 2:  'first_name', it is a string field that has a max of 25 characters,
                      part of an indexes 'idx_first' and 'idx_name'
            field 3:  'last_name', it is a string field that has a max of 25 characters,
                      NULL's are not allowed, part of an indexes 'idx_last' and 'idx_name'
            field 4:  'amount_owes', it is a float that has a total of 8 decimal places,
                      2 of the decimal places are to the right of the point, uses 8 bytes,
                      and the default is 0
            ========  ======================

    Code Example::

        from dabo.db import dTable
        myTable = dTable(Name="mytemp", IsTemp=True)
        myTable.addField(Name="theid", IsPK=True, DataType="int",
                Size=2, IsAutoIncrement=True)
        myTable.addField(Name="first_name", DataType="string", Size=25,
                Index="idx_first")
        myTable.addField(Name="last_name", DataType="string", Size=25,
                AllowNulls=False, Index="idx_last")
        myTable.addField(Name="amount_owes", DataType="float",
                TotalDP=8, RightDP=2, Size=8, Default=0)
        # When you want to have more than one field in an index, use addIndex().
        myTable.addIndex(Name="idx_name", Fields=("last_name","first_name"))

    """

    def __init__(self, *args, **kwargs):
        self._baseClass = dTable
        self._name = ""
        self._isTemp = False
        self._fields = []
        self._indexes = []
        self._pk = None
        super().__init__(*args, **kwargs)

    def __str__(self):
        txt = ""
        txt = txt + "Table Name: " + self._name
        if self._isTemp == True:
            txt = txt + "\n  is TEMPOARY\n"
        txt = txt + "\nFields:\n"
        for f in self._fields:
            txt = txt + " " + str(f) + "\n"
        txt = txt + "\nIndexes:\n"
        for i in self._indexes:
            txt = txt + " " + str(i) + "\n"
        return txt

    def addField(self, *args, **kwargs):
        """Add a field to the table."""
        # Check if adding an index
        try:
            idx = kwargs["Index"]
            name = kwargs["Name"]
        except KeyError:
            pass
        else:
            self._indexes.append(dIndex(Name=idx, Fields=name))
            del kwargs["Index"]

        # Check if setting PK
        try:
            pk = kwargs["IsPK"]
            name = kwargs["Name"]
        except KeyError:
            pass
        else:
            if pk == True:
                if self._pk is None:
                    self._pk = [name]
                else:
                    self._pk.append(name)

        self._fields.append(dField(*args, **kwargs))

    def addIndex(self, *args, **kwargs):
        """Add an index to the table."""
        self._indexes.append(dIndex(*args, **kwargs))

    def _getFields(self):
        return self._fields

    def _getIndexes(self):
        return self._indexes

    def _setIsTemp(self, value):
        self._isTemp = value

    def _getIsTemp(self):
        return self._isTemp

    def _setName(self, name):
        self._name = name

    def _getName(self):
        return self._name

    def _getPK(self):
        return self._pk

    Fields = property(_getFields, None, None, _("List of the fields in the table. (list)"))

    Indexes = property(_getIndexes, None, None, _("List of the indexes in the table. (list)"))

    IsTemp = property(
        _getIsTemp, _setIsTemp, None, _("Whether or not the table is temporary. (bool)")
    )

    Name = property(_getName, _setName, None, _("The name of the table. (str)"))

    PK = property(_getPK, None, None, _("The primary key of the table. (str)"))


class dIndex(dObject):
    def __init__(self, *args, **kwargs):
        self._baseClass = dIndex
        self._name = ""
        self._fields = None
        super().__init__(*args, **kwargs)

    def __str__(self):
        txt = self._name + " ("
        for fld in self._fields:
            txt = txt + fld + ","
        if txt[-1:] == ",":
            txt = txt[:-1]
        return txt + ")"

    def _getFields(self):
        return self._fields

    def _setFields(self, fields):
        if isinstance(fields, str):
            flds = fields.split()
            self._fields = tuple(flds)
        elif isinstance(fields, list):
            self._fields = tuple(flds)
        else:
            self._fields = fields

    def _getName(self):
        return self._name

    def _setName(self, name):
        self._name = name

    Fields = property(_getFields, _setFields, None, _("Fields which comprise the index.  (list)"))

    Name = property(_getName, _setName, None, _("Name of the index.  (str)"))


class dField(dObject):
    def __init__(self, *args, **kwargs):
        self._baseClass = dField
        self._name = ""
        self._type = fType()
        self._allow_nulls = True
        self._default = None
        self._autoincrement = False
        self._isPK = False
        super().__init__(*args, **kwargs)

    def __str__(self):
        if self._allow_nulls:
            allowednulls = "Nulls Allowed"
        else:
            allowednulls = "Nulls Not Allowed"
        if self._autoincrement:
            autoi = " Auto Incrementing"
        else:
            autoi = ""
        if self._isPK:
            pk = " PK"
        else:
            pk = ""

        tmplt = "%s%s (%s, Size:%i, Total DP:%i Right DP:%i)%s %s Default:%s"
        return tmplt % (
            self._name,
            pk,
            self._type.DataType,
            self._type.Size,
            self._type.TotalDP,
            self._type.RightDP,
            autoi,
            allowednulls,
            self._default,
        )

    @property
    def AllowNulls(self):
        """Whether or not nulls are allowed. Default:True (bool)"""
        return self._allow_nulls

    @AllowNulls.setter
    def AllowNulls(self, allow):
        self._allow_nulls = allow

    @property
    def DataType(self):
        """The type of the column. (str)"""
        return self._type.DataType

    @DataType.setter
    def DataType(self, datatype):
        self._type.DataType = datatype

    @property
    def Default(self):
        """The default value for the field. Default: None (str)"""
        return self._default

    @Default.setter
    def Default(self, default):
        self._default = default

    @property
    def IsAutoIncrement(self):
        """Whether or not the field is an auto incrementing field. Default: False  (bool)"""
        return self._autoincrement

    @IsAutoIncrement.setter
    def IsAutoIncrement(self, auto):
        self._autoincrement = auto

    @property
    def IsPK(self):
        """Whether or not the field has the primary key. (bool)"""
        return self._isPK

    @IsPK.setter
    def IsPK(self, value):
        self._isPK = value

    @property
    def Name(self):
        """The name of the table. (str)"""
        return self._name

    @Name.setter
    def Name(self, name):
        self._name = name

    @property
    def TotalDP(self):
        """The total number of decimal places  (int)"""
        return self._type.TotalDP

    @TotalDP.setter
    def TotalDP(self, places):
        self._type.TotalDP = places

    @property
    def RightDP(self):
        """The number of decimal places to the right of the period.  (int)"""
        return self._type.RightDP

    @RightDP.setter
    def RightDP(self, places):
        self._type.RightDP = places

    @property
    def Size(self):
        """The size required for the column in bytes or character units if it's a string. (int)"""
        return self._type.Size

    @Size.setter
    def Size(self, size):
        self._type.Size = size

    @property
    def Type(self):
        """The type of the column.  (class)"""
        return self._type

    @Type.setter
    def Type(self, type):
        self._type = type


class fType(dObject):
    """
    Dabo DB Field Type - Used to hold the information about types
    of fields in any database.
    """

    def __init__(self, *args, **kwargs):
        self._baseClass = fType
        self._data_type = "Numeric"
        self._size = 1
        self._total_dp = 0
        self._right_dp = 0
        super().__init__(*args, **kwargs)

    @property
    def DataType(self):
        """
        Type of data for this field. Allowed types: Numeric, Float, String, Date, Time,
        DateTime, Stamp, Binary  (str)
        """
        return self._data_type

    @DataType.setter
    def DataType(self, datatype):
        check = {
            "numeric": "Numeric",
            "int": "Numeric",
            "integer": "Numeric",
            "float": "Float",
            "double": "Float",
            "decimal": "Decimal",
            "string": "String",
            "varchar": "String",
            "char": "String",
            "date": "Date",
            "time": "Time",
            "datetime": "DateTime",
            "stamp": "Stamp",
            "binary": "Binary",
        }
        self._data_type = check[datatype.lower()]

    @property
    def TotalDP(self):
        """The total number of decimal places  (int)"""
        return self._total_dp

    @TotalDP.setter
    def TotalDP(self, places):
        self._total_dp = places

    @property
    def RightDP(self):
        """The number of decimal places to the right of the period.  (int)"""
        return self._right_dp

    @RightDP.setter
    def RightDP(self, places):
        self._right_dp = places

    @property
    def Size(self):
        """Size of this field  (int)"""
        return self._size

    @Size.setter
    def Size(self, size):
        self._size = size


if __name__ == "__main__":
    print("\n\nstarting\n")

    # type = fType(DataType="String", Size=25)
    # print type.getProperties(("DataType","Size"))

    # col = dField(Name="colname", Type=fType(DataType="String",Size=50))
    # print col
    # col = dField(Name="colname", DataType="String", Size=50)
    # print col

    myTable = dTable(Name="mytemp", IsTemp=True)
    myTable.addField(Name="theid", IsPK=True, DataType="int", Size=2, IsAutoIncrement=True)
    myTable.addField(Name="first_name", DataType="string", Size=25, Index="idx_first")
    myTable.addField(
        Name="last_name", DataType="string", Size=25, AllowNulls=False, Index="idx_last"
    )
    myTable.addField(Name="amount_owes", DataType="float", TotalDP=8, RightDP=2, Size=8, Default=0)

    # When you want to have more than one field in an index, use addIndex().
    myTable.addIndex(Name="idx_name", Fields=("last_name", "first_name"))

    print(myTable)
