
class SerializableAttribute(object):
    pass


class GenericAttr(SerializableAttribute):
    def __init__(self, default):
        self.default = default
        
    def evaluate(self, value, env):
        if value is None:
            return self.default
        else:
            return eval(value, env)
        
        
class StringAttr(SerializableAttribute):
    def __init__(self, default):
        self.default = default
        
    def evaluate(self, value, env):
        if value is None:
            return self.default
        else:
            value = eval(value, env)
            assert isinstance(value, basestring)
            return value
        
        
class UnevalStringAttr(SerializableAttribute):
    def __init__(self, default):
        self.default = default
        
    def evaluate(self, value, env):
        assert isinstance(value, basestring)
        return value
        
        
class LengthAttr(SerializableAttribute):
    def __init__(self, default):
        self.default = default
        
    def evaluate(self, value, env):
        if value is None:
            return self.default
        else:
            from dabo.lib.reporting.util import getPt
            return getPt(eval(value, env))
        
        
class StringChoiceAttr(SerializableAttribute):
    def __init__(self, choices, default):
        self.choices = choices
        self.default = default
        
    def evaluate(self, value, env):
        if value is None:
            return self.default
        else:
            v = eval(value, env)
            assert v in self.choices, "Invalid value %r for %s" % (v, self.__class__.__name__)
            return v
        
        
class ColorAttr(SerializableAttribute):
    def __init__(self, default):
        self.default = default
        
    def evaluate(self, value, env):
        if value is None:
            return self.default
        else:
            value = eval(value, env)
            assert isinstance(value, tuple)
            return value


class PagesizesAttr(SerializableAttribute):
    def __init__(self, default):
        self.default = default
        
    def evaluate(self, value, env):
        from reportlab.lib import pagesizes
        pageSize = getattr(pagesizes, str(value).upper(), None)
        if pageSize is None:
            pageSize = getattr(pagesizes, str(self.default).upper(), None)
        return pageSize
        
        
