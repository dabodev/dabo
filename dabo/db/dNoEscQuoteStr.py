# -*- coding: utf-8 -*-
from ..dObject import dObject


class dNoEscQuoteStr(dObject):
    def __init__(self, value):
        self._baseClass = dNoEscQuoteStr
        super().__init__()
        self._value = value

    def __str__(self):
        return self._value
