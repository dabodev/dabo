""" vr_none.py : an example """

viewDef = {
            "fields":   [
                            {   "name":         "iid",
                                "select":       "test.iid",
                                "caption":      "ID",
                                "type":         "I",
                                "showGrid":     True,
                                "showEdit":     True,
                                "editEnabled":  False,
                                "selectTypes":  ("range",),
                                "columnOrder":  95,
                                "pk":           True     },
                            
                            {   "name":         "cdescrp",
                                "select":       "test.cdescrp",
                                "caption":      "Description",
                                "type":         "C",
                                "showGrid":     True,
                                "showEdit":     True,
                                "selectTypes":  ("stringMatch","startsWith"),
                                "columnOrder":  1     },

                            {   "name":         "mnotes",
                                "select":       "test.mnotes",
                                "caption":      "Notes",
                                "type":         "M",
                                "showGrid":     False,
                                "showEdit":     True,
                                "selectTypes":  ("stringMatch",),
                                "columnOrder":  2     },

                            {   "name":         "dcreated",
                                "select":       "date_format(test.dcreated, '%Y-%m-%d')",
                                "caption":      "Date Created",
                                "type":         "D",
                                "showGrid":     True,
                                "showEdit":     True,
                                "selectTypes":  ("range","xDays"),
                                "columnOrder":  5     },

                            {   "name":         "ldeleted",
                                "select":       "test.ldeleted",
                                "caption":      "Deleted",
                                "type":         "I",
                                "showGrid":     False,
                                "showEdit":     False,
                                "columnOrder":  90     }
                        ],
            "updateTableName":  "testdb.test",
            "fromClause":       "testdb.test",
            "whereClause":      "test.ldeleted=0",
            "groupClause":      "test.iid",
            "orderClause":      "test.cdescrp",
            "limitClause":      400,
            "caption":         "Test... no actual database",
            "defaultRowHeight": 40
        }

                           
